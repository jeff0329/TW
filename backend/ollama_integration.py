"""
Ollama 集成模組
負責與本地 Ollama LLM 模型的交互
"""

import requests
import json
import heapq
import logging
import math
from collections import Counter
import re
from typing import List, Dict, Any, Optional
from pathlib import Path
import ollama

try:
    from .config import OLLAMA_CONFIG, RAG_CONFIG
    from .itinerary_planner import build_itinerary, flatten_recommended_places
except ImportError:  # pragma: no cover - fallback for direct script execution
    from backend.config import OLLAMA_CONFIG, RAG_CONFIG
    from backend.itinerary_planner import build_itinerary, flatten_recommended_places

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class OllamaClient:
    """Ollama 客戶端（支持 Demo 模式）"""
    
    def __init__(self, base_url: str = OLLAMA_CONFIG["base_url"], model: str = OLLAMA_CONFIG["model"], demo_mode: bool = False):
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.is_demo = demo_mode
        self.client = None
        self.last_error = None
        
        if not demo_mode:
            try:
                self.client = ollama.Client(host=base_url)
                self._check_connection()
            except Exception as e:
                self.last_error = str(e)
                logger.warning(f"Cannot initialize Ollama client: {e}")
                logger.info("Switching to demo mode")
                self.is_demo = True
        else:
            logger.info("Running in Demo Mode (no Ollama required)")
    
    def _check_connection(self) -> bool:
        """檢查 Ollama 連接"""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            if response.status_code == 200:
                models = response.json().get("models", [])
                available_models = {model.get("name") for model in models}
                if self.model not in available_models:
                    raise RuntimeError(
                        f"Ollama model '{self.model}' not found. "
                        f"Available models: {sorted(available_models)}"
                    )
                logger.info(f"Ollama connected successfully: {self.base_url}, model: {self.model}")
                return True
            raise RuntimeError(f"Ollama returned HTTP {response.status_code}")
        except Exception as e:
            self.last_error = str(e)
            logger.warning(f"Cannot connect to Ollama: {e}")
            logger.info("Switching to demo mode")
            self.is_demo = True
            return False
    
    def list_models(self) -> List[str]:
        """列出可用的模型"""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            if response.status_code == 200:
                models = response.json().get("models", [])
                model_names = [m.get("name", "") for m in models if m.get("name")]
                logger.info(f"Available models: {model_names}")
                return model_names
        except Exception as e:
            self.last_error = str(e)
            logger.error(f"Cannot list models: {e}")
        return []
    
    def generate_response(self, prompt: str, context: Optional[str] = None) -> str:
        """Generate response"""
        if self.is_demo:
            return self._generate_demo_response(prompt)
        
        try:
            if not self.client:
                return self._generate_demo_response(prompt)
            
            full_prompt = f"Context information:\n{context}\n\nQuestion: {prompt}" if context else prompt
            
            response = self.client.generate(
                model=self.model,
                prompt=full_prompt,
                stream=False,
                think=OLLAMA_CONFIG.get("think", False),
                options={
                    "temperature": OLLAMA_CONFIG.get("temperature", 0.7),
                    "top_k": OLLAMA_CONFIG.get("top_k", 40),
                    "top_p": OLLAMA_CONFIG.get("top_p", 0.9),
                    "num_predict": OLLAMA_CONFIG.get("num_predict", 800)
                }
            )
            
            return response.get("response", "").strip()
        
        except Exception as e:
            logger.warning(f"Error generating response: {e}, using demo mode")
            return self._generate_demo_response(prompt)
    
    def _generate_demo_response(self, prompt: str) -> str:
        """Generate demo response for testing"""
        demo_responses = {
            "台北": "台北 3 天行程推薦:\n第一天：參觀國立故宮博物院（世界四大博物館之一）、士林夜市品嚐台北小吃\n第二天：登臨台北 101 觀景台、逛信義商圈購物\n第三天：遊覽九份老街、十分天燈許願、平溪線風景區",
            "高雄": "高雄 3 天行程推薦:\n第一天：蓮池潭風景區、佛光山寺廟\n第二天：美麗島捷運站、高雄港灣夜景\n第三天：駁二藝術特區、旗津海邊",
            "日月潭": "日月潭 2 天行程推薦:\n第一天：搭船環潭、騎自行車環湖\n第二天：參訪文武廟、逛日月潭名產街\n美食推薦：紅茶、特色小吃"
        }
        
        for dest in demo_responses:
            if dest in prompt:
                return demo_responses[dest]
        
        return "台灣旅遊推薦：台北、高雄、日月潭、九份、阿里山都是不錯的選擇。根據您的興趣和預算，我們可以為您量身打造最適合的行程。"
    
    def chat(self, messages: List[Dict[str, str]]) -> str:
        """Chat interface"""
        if self.is_demo:
            last_msg = messages[-1].get("content", "") if messages else ""
            return self._generate_demo_response(last_msg)
        
        try:
            if not self.client:
                last_msg = messages[-1].get("content", "") if messages else ""
                return self._generate_demo_response(last_msg)
            
            response = self.client.chat(
                model=self.model,
                messages=messages,
                stream=False,
                think=OLLAMA_CONFIG.get("think", False),
                options={
                    "temperature": OLLAMA_CONFIG.get("temperature", 0.7),
                    "top_k": OLLAMA_CONFIG.get("top_k", 40),
                    "top_p": OLLAMA_CONFIG.get("top_p", 0.9),
                    "num_predict": OLLAMA_CONFIG.get("num_predict", 800)
                }
            )
            return response.get("message", {}).get("content", "").strip()
        except Exception as e:
            logger.warning(f"Error in chat: {e}, using demo mode")
            last_msg = messages[-1].get("content", "") if messages else ""
            return self._generate_demo_response(last_msg)


class RAGSystem:
    """檢索增強生成 (Retrieval-Augmented Generation) 系統"""
    
    def __init__(self, ollama_client: OllamaClient, knowledge_base_path: Optional[str] = None,
                 knowledge_items: Optional[List[Dict[str, Any]]] = None):
        self.ollama_client = ollama_client
        self.knowledge_base = []
        self.vector_store = {}
        self.document_frequency = {}
        self.total_documents = 0
        
        if knowledge_items is not None:
            self.knowledge_base = knowledge_items
            self._build_vector_store()
        elif knowledge_base_path:
            self.load_knowledge_base(knowledge_base_path)
    
    def load_knowledge_base(self, filepath: str) -> None:
        """Load knowledge base (JSON format)"""
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
                self.knowledge_base = data if isinstance(data, list) else [data]
            
            logger.info(f"Knowledge base loaded: {len(self.knowledge_base)} items")
            self._build_vector_store()
        except Exception as e:
            logger.error(f"Cannot load knowledge base: {e}")
    
    def _build_vector_store(self) -> None:
        """Build a lightweight local TF-IDF-like index that supports Chinese text."""
        self.vector_store = {}
        self.document_frequency = {}
        for idx, item in enumerate(self.knowledge_base):
            key_info = self._item_text(item)
            term_counts = Counter(self._terms(key_info))
            for term in term_counts:
                self.document_frequency[term] = self.document_frequency.get(term, 0) + 1
            self.vector_store[idx] = {
                "text": key_info,
                "term_counts": term_counts,
                "original": item
            }
        self.total_documents = len(self.vector_store)
        logger.info(f"Vector store built: {len(self.vector_store)} items")

    @staticmethod
    def _item_text(item: Dict[str, Any]) -> str:
        # 相容 place_master 新欄位（英文）與舊版爬蟲欄位（中文）兩種命名。
        legacy_keys = ("名稱", "縣市", "區域", "分類", "描述", "地址", "交通", "網站", "來源")
        schema_keys = ("name", "city", "district", "category_lv1", "description", "address", "website", "source")
        values = [item.get(key, "") for key in legacy_keys] + [item.get(key, "") for key in schema_keys]
        return " ".join(str(value) for value in values if value)

    @staticmethod
    def _terms(text: str) -> List[str]:
        compact = re.sub(r"\s+", "", text.lower())
        terms = re.findall(r"[a-z0-9]+|[\u4e00-\u9fff]", compact)
        terms.extend(compact[index:index + 2] for index in range(max(0, len(compact) - 1)))
        return terms
    
    def retrieve_relevant_info(self, query: str, top_k: int = 5) -> List[Dict]:
        """Retrieve relevant information using precomputed term counts."""
        if not self.vector_store:
            return []

        query_counts = Counter(self._terms(query))
        if not query_counts:
            return []

        query_norm = math.sqrt(sum(count * count for count in query_counts.values())) or 1
        scores = []

        for idx, item in self.vector_store.items():
            document_counts = item["term_counts"]
            score = 0.0
            for term, count in query_counts.items():
                doc_count = document_counts.get(term, 0)
                if doc_count:
                    inverse_frequency = math.log(
                        (self.total_documents + 1) /
                        (self.document_frequency[term] + 1)
                    ) + 1
                    score += min(count, doc_count) * inverse_frequency

            score /= query_norm
            if score > 0:
                scores.append((idx, score))

        top_indices = heapq.nlargest(max(0, int(top_k)), scores, key=lambda pair: pair[1])
        results = []
        for idx, score in top_indices:
            item = dict(self.vector_store[idx]["original"])
            item["_retrieval_score"] = round(score, 4)
            results.append(item)

        logger.info(f"Retrieved {len(results)} relevant items")
        return results

    def generate_with_rag(self, query: str) -> Dict[str, Any]:
        """Generate response using RAG"""
        query = str(query or "").strip()
        if not query:
            raise ValueError("RAG query cannot be empty")

        # 1. Retrieve relevant data
        relevant_info = self.retrieve_relevant_info(query, top_k=RAG_CONFIG.get("top_k", 5))
        
        # 2. Build context（同時支援 place_master 新欄位與舊版中文欄位）
        context = "以下是可查證的旅遊資料；若資料不足，請明確說明，不要自行虛構：\n"
        for i, info in enumerate(relevant_info, 1):
            name = info.get("名稱") or info.get("name", "N/A")
            city = info.get("縣市") or info.get("city", "")
            district = info.get("區域") or info.get("district", "")
            description = info.get("描述") or info.get("description", "")
            context += f"\n{i}. {name}\n"
            context += f"   Location: {city}{district}\n"
            if description:
                context += f"   Description: {description[:300]}\n"
            for legacy_field, schema_field in (
                ("地址", "address"), ("開放時間", "open_hours_text"),
                ("票價", "avg_cost_twd"), ("人均價格", "avg_cost_twd"), ("網站", "website"),
            ):
                value = info.get(legacy_field) or info.get(schema_field)
                if value:
                    context += f"   {legacy_field}: {value}\n"
        
        # 3. Generate response
        response = self.ollama_client.generate_response(query, context)
        
        return {
            "query": query,
            "context": context,
            "response": response,
            "sources": relevant_info
        }


class TourismPlanner:
    """旅遊行程規劃器"""
    
    def __init__(self, rag_system: RAGSystem):
        self.rag = rag_system
    
    def plan_itinerary(self, 
                      destination: str,
                      days: int,
                      budget: float,
                      interests: List[str],
                      pace: str = "moderate") -> Dict[str, Any]:
        """規劃行程：先以 place_master 結構化資料做預算/天數/動線/主題約束求解，
        再請 LLM 依已驗證的行程撰寫敘述文字，避免模型自行虛構景點或價格。"""
        if not isinstance(days, int) or days < 1 or days > 30:
            raise ValueError("旅遊天數必須介於 1 至 30 天")
        if budget < 0:
            raise ValueError("預算不可為負數")
        interests = [str(interest).strip() for interest in (interests or []) if str(interest).strip()]

        schedule = build_itinerary(destination, days, budget, interests, pace=pace)

        if schedule.get("data_grounded"):
            recommended_places = flatten_recommended_places(schedule)
            context_lines = ["以下是已依預算與天數驗證過的實際行程，請只描述其中內容，不要新增或竄改地點與價格："]
            for day_idx, day in enumerate(schedule["days"], 1):
                context_lines.append(f"\n第 {day_idx} 天：")
                for stop in day:
                    context_lines.append(
                        f"  - {stop['time']} {stop['name']}（{stop['theme']}，約 {int(stop.get('avg_cost_twd') or 0)} 元）"
                    )
            context_lines.append(
                f"\n總預算上限 {budget} 元，此行程預估花費 {schedule['estimated_total']} 元，"
                f"{'在預算內' if schedule['compliant'] else '略超出預算，請提醒使用者'}。"
            )
            context = "\n".join(context_lines)
            prompt = f"請將以上 {destination} {days} 天行程整理成口語化的行程說明，並附上每日重點與預算提醒。"
            response = self.rag.ollama_client.generate_response(prompt, context)

            return {
                "destination": destination,
                "days": days,
                "budget": budget,
                "interests": interests,
                "plan": response,
                "recommended_places": recommended_places,
                "schedule": schedule["days"],
                "budget_summary": {
                    "budget_cap": schedule["budget_cap"],
                    "estimated_total": schedule["estimated_total"],
                    "remaining_budget": schedule["remaining_budget"],
                    "compliant": schedule["compliant"],
                },
                "themes_covered": schedule["themes_covered"],
                "route_smoothness_km": schedule["route_smoothness_km"],
            }

        # 找不到在地結構化資料時，退回純 RAG 生成（並標註未經數值驗證）
        prompt = f"""請幫我規劃一個 {destination} 的 {days} 天行程，預算是 {budget} 元。
        我的興趣是：{', '.join(interests)}。
        
        請提供：
        1. 行程概述
        2. 每天的行程安排
        3. 推薦的景點、餐廳和飯店
        4. 交通建議
        5. 預算分配
        """
        
        result = self.rag.generate_with_rag(prompt)
        
        return {
            "destination": destination,
            "days": days,
            "budget": budget,
            "interests": interests,
            "plan": result["response"],
            "recommended_places": result["sources"],
            "schedule": None,
            "budget_summary": {
                "budget_cap": budget,
                "estimated_total": None,
                "remaining_budget": None,
                "compliant": None,
            },
        }
    
    def get_destination_info(self, destination: str) -> Dict[str, Any]:
        """獲取目的地信息"""
        prompt = f"請介紹 {destination} 有什麼著名景點、美食和飯店"
        result = self.rag.generate_with_rag(prompt)
        
        return {
            "destination": destination,
            "info": result["response"],
            "places": result["sources"]
        }


def initialize_system(knowledge_base_path: Optional[str] = None, demo_mode: bool = False,
                       knowledge_items: Optional[List[Dict[str, Any]]] = None) -> TourismPlanner:
    """Initialize the entire system"""
    
    logger.info("Initializing tourism planning system...")
    
    # 1. Initialize Ollama client (automatically enters demo mode if connection fails)
    ollama_client = OllamaClient(demo_mode=demo_mode)
    
    # 2. Initialize RAG system
    rag_system = RAGSystem(ollama_client, knowledge_base_path, knowledge_items=knowledge_items)
    
    # 3. Initialize tourism planner
    planner = TourismPlanner(rag_system)
    
    logger.info("System initialization complete")
    return planner


def main():
    """測試主程序"""
    
    # 初始化系統（使用本地數據作為知識庫）
    knowledge_base = "./data/taiwan_tourism_data.json"
    
    planner = initialize_system(knowledge_base)
    
    # 測試 1：獲取目的地信息
    print("\n" + "="*50)
    print("測試 1：獲取目的地信息")
    print("="*50)
    
    dest_info = planner.get_destination_info("台北")
    print(f"目的地：{dest_info['destination']}")
    print(f"信息：{dest_info['info']}")
    
    # 測試 2：規劃行程
    print("\n" + "="*50)
    print("測試 2：規劃行程")
    print("="*50)
    
    itinerary = planner.plan_itinerary(
        destination="台北",
        days=3,
        budget=5000,
        interests=["文化", "美食", "夜生活"]
    )
    
    print(f"目的地：{itinerary['destination']}")
    print(f"天數：{itinerary['days']}")
    print(f"預算：{itinerary['budget']} 元")
    print(f"興趣：{', '.join(itinerary['interests'])}")
    print(f"\n行程建議：\n{itinerary['plan']}")


if __name__ == "__main__":
    main()
