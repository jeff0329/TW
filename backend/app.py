"""
Flask API 伺服器
提供旅遊規劃的 REST API
"""

from flask import Flask, request, jsonify, render_template, session
from flask_cors import CORS
import logging
import json
import os
import secrets
import sys
from functools import wraps
from pathlib import Path
from datetime import datetime, timedelta
from werkzeug.security import check_password_hash, generate_password_hash

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.scraper import TDXScraper, DataProcessor
from backend.config import OUTPUT_DIR
from backend.ollama_integration import initialize_system, TourismPlanner
from backend.itinerary_planner import PlaceIndex
from data_pipeline import AuthorizedTravelAPI, DynamicTravelScraper, TourismDataPipeline, build_knowledge_base
from evaluation import budget_compliance, plan_quality_report, retrieval_recall

# 初始化 Flask 應用
app = Flask(
    __name__,
    template_folder=str(PROJECT_ROOT / "frontend" / "templates"),
    static_folder=str(PROJECT_ROOT / "frontend" / "static"),
)
CORS(app)
app.config.update(
    SECRET_KEY=os.getenv("FLASK_SECRET_KEY") or secrets.token_hex(32),
    PERMANENT_SESSION_LIFETIME=timedelta(days=30),
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
)

# 設定日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 全局變量
planner: TourismPlanner = None
tourism_data = []
pipeline = TourismDataPipeline()
USERS_FILE = Path(OUTPUT_DIR) / "users.json"
DEFAULT_SETTINGS = {
    "autoBudgetHint": True,
    "budgetBuffer": "5%",
    "dailyPace": "moderate",
    "prioritizeSaved": True,
    "shareTelemetry": False,
    "theme": "auto",
}


def _load_users():
    if not USERS_FILE.exists():
        return {}
    try:
        return json.loads(USERS_FILE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        logger.exception("Cannot load local user database")
        return {}


def _save_users(users):
    USERS_FILE.parent.mkdir(parents=True, exist_ok=True)
    USERS_FILE.write_text(json.dumps(users, ensure_ascii=False, indent=2), encoding="utf-8")


def _public_user(user):
    return {"id": user["id"], "name": user["name"], "email": user["email"], "guest": False}


def _current_user():
    user_id = session.get("user_id")
    return _load_users().get(user_id) if user_id else None


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not _current_user():
            return jsonify({"error": "請先登入"}), 401
        return view(*args, **kwargs)
    return wrapped


def _f(item, *keys, default=""):
    """依序取第一個非空欄位值，相容 place_master 新欄位與舊版爬蟲中文欄位。"""
    for key in keys:
        value = item.get(key)
        if value not in (None, ""):
            return value
    return default


def initialize_app():
    """Initialize the application"""
    global planner, tourism_data
    
    logger.info("Initializing Flask application...")

    # 優先使用 data/processed/place_master.json（政府開放資料正規化後的 schema-native 主檔）
    place_index = PlaceIndex.load()
    if place_index.places:
        tourism_data = place_index.places
        logger.info(f"Loaded {len(tourism_data)} schema-native places from place_master.json")
        try:
            planner = initialize_system(knowledge_items=tourism_data)
            logger.info("Tourism planning system initialized (place_master-based RAG)")
        except Exception as e:
            logger.warning(f"Cannot initialize Ollama: {e}")
            logger.info("Please ensure Ollama is installed and running 'ollama serve'")
        return

    # 回退：place_master 尚未產生時，使用舊版爬蟲資料流程
    data_dir = Path(OUTPUT_DIR)
    json_files = []
    if not data_dir.exists():
        logger.warning(f"Data directory does not exist: {data_dir}")
        logger.info("First time running, please execute: python scraper.py")
    else:
        json_files = sorted(data_dir.glob("taiwan_tourism_data_*.json"), reverse=True)
        if json_files:
            latest_file = json_files[0]
            logger.info(f"Loading data: {latest_file}")
            
            with open(latest_file, "r", encoding="utf-8") as f:
                tourism_data = pipeline.clean(json.load(f), latest_file.name)
            
            logger.info(f"Loaded {len(tourism_data)} tourism data items")
    if not tourism_data:
        for candidate in (Path("ollama_tourism_db.json"), Path("taiwan_final_success.json")):
            if candidate.exists():
                tourism_data = pipeline.clean(json.loads(candidate.read_text(encoding="utf-8")), candidate.name)
                logger.info(f"Loaded fallback data: {candidate} ({len(tourism_data)} items)")
                break
    
    # Initialize tourism planning system
    try:
        # Find the latest knowledge base file
        knowledge_file = None
        if json_files:
            knowledge_file = str(json_files[0])
        
        if tourism_data:
            knowledge_file = str(build_knowledge_base(tourism_data))
        planner = initialize_system(knowledge_file)
        logger.info("Tourism planning system initialized")
    except Exception as e:
        logger.warning(f"Cannot initialize Ollama: {e}")
        logger.info("Please ensure Ollama is installed and running 'ollama serve'")


@app.route('/')
def index():
    """Home page"""
    return app.send_static_file('index.html')


@app.route('/api/auth/register', methods=['POST'])
def register():
    data = request.get_json(silent=True) or {}
    name = str(data.get("name", "")).strip()
    email = str(data.get("email", "")).strip().lower()
    password = str(data.get("password", ""))
    if not name or len(name) > 80:
        return jsonify({"error": "請輸入 1 至 80 個字元的暱稱"}), 400
    if "@" not in email or len(email) > 254:
        return jsonify({"error": "請輸入有效的電子郵件"}), 400
    if len(password) < 8:
        return jsonify({"error": "密碼至少需要 8 個字元"}), 400
    users = _load_users()
    if any(user.get("email") == email for user in users.values()):
        return jsonify({"error": "此電子郵件已註冊"}), 409
    user_id = secrets.token_urlsafe(16)
    users[user_id] = {
        "id": user_id,
        "name": name,
        "email": email,
        "password_hash": generate_password_hash(password),
        "settings": dict(DEFAULT_SETTINGS),
        "created_at": datetime.now().isoformat(),
    }
    _save_users(users)
    session["user_id"] = user_id
    session.permanent = bool(data.get("remember", True))
    return jsonify({"user": _public_user(users[user_id])}), 201


@app.route('/api/auth/login', methods=['POST'])
def login():
    data = request.get_json(silent=True) or {}
    email = str(data.get("email", "")).strip().lower()
    password = str(data.get("password", ""))
    user = next((item for item in _load_users().values() if item.get("email") == email), None)
    if not user or not check_password_hash(user.get("password_hash", ""), password):
        return jsonify({"error": "電子郵件或密碼不正確"}), 401
    session["user_id"] = user["id"]
    session.permanent = bool(data.get("remember", True))
    return jsonify({"user": _public_user(user)}), 200


@app.route('/api/auth/me', methods=['GET'])
def auth_me():
    user = _current_user()
    if not user:
        return jsonify({"user": None}), 200
    return jsonify({"user": _public_user(user)}), 200


@app.route('/api/auth/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({"status": "success"}), 200


@app.route('/api/auth/forgot-password', methods=['POST'])
def forgot_password():
    data = request.get_json(silent=True) or {}
    email = str(data.get("email", "")).strip().lower()
    if "@" not in email:
        return jsonify({"error": "請輸入有效的電子郵件"}), 400
    return jsonify({"message": "如果此電子郵件已註冊，重設密碼說明將會寄出。"}), 200


@app.route('/api/settings', methods=['GET'])
@login_required
def get_settings():
    user = _current_user()
    settings = dict(DEFAULT_SETTINGS)
    settings.update(user.get("settings", {}))
    return jsonify({"settings": settings}), 200


@app.route('/api/settings', methods=['PUT'])
@login_required
def update_settings():
    data = request.get_json(silent=True) or {}
    allowed = set(DEFAULT_SETTINGS)
    allowed.add("displayName")
    invalid = set(data) - allowed
    if invalid:
        return jsonify({"error": f"不支援的設定欄位: {', '.join(sorted(invalid))}"}), 400
    users = _load_users()
    user = users[session["user_id"]]
    if "displayName" in data:
        display_name = str(data["displayName"]).strip()
        if not display_name or len(display_name) > 80:
            return jsonify({"error": "顯示名稱需為 1 至 80 個字元"}), 400
        user["name"] = display_name
    user.setdefault("settings", {}).update({key: data[key] for key in data})
    _save_users(users)
    return jsonify({"settings": user["settings"]}), 200


@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check"""
    return jsonify({
        "status": "ok",
        "timestamp": datetime.now().isoformat(),
        "data_loaded": len(tourism_data) > 0,
        "tourism_data_count": len(tourism_data),
        "planner_ready": planner is not None
    })


@app.route('/api/data/summary', methods=['GET'])
def data_summary():
    """Data statistics"""
    if not tourism_data:
        return jsonify({"error": "No tourism data available"}), 400
    
    summary = {
        "total_items": len(tourism_data),
        "types": {},
        "locations": set()
    }
    
    for item in tourism_data:
        item_type = _f(item, "type", "source_type", default="未分類")
        summary["types"][item_type] = summary["types"].get(item_type, 0) + 1
        
        location = _f(item, "縣市", "city", default="未知")
        summary["locations"].add(location)
    
    summary["locations"] = list(summary["locations"])
    
    return jsonify(summary)


@app.route('/api/search', methods=['GET'])
def search():
    """搜尋景點"""
    keyword = request.args.get('q', '').strip()
    location = request.args.get('location', '').strip()
    item_type = request.args.get('type', '').strip()  # 景點、餐廳、飯店
    
    if not keyword:
        return jsonify({"error": "請輸入搜尋關鍵字"}), 400
    
    results = []
    keyword_lower = keyword.lower()
    type_synonyms = {"景點": "scenic", "餐廳": "restaurant", "美食": "restaurant", "飯店": "hotel", "住宿": "hotel", "活動": "event"}
    
    for item in tourism_data:
        # 檢查關鍵字匹配
        name = str(_f(item, "名稱", "name")).lower()
        desc = str(_f(item, "描述", "description")).lower()
        
        if keyword_lower not in name and keyword_lower not in desc:
            continue
        
        # 檢查位置過濾
        if location and _f(item, "縣市", "city") != location:
            continue
        
        # 檢查類型過濾
        if item_type:
            actual_type = _f(item, "type", "source_type")
            if actual_type != item_type and actual_type != type_synonyms.get(item_type):
                continue
        
        results.append(item)
    
    return jsonify({
        "query": keyword,
        "results_count": len(results),
        "results": results[:20]  # 最多返回 20 筆
    })


@app.route('/api/locations', methods=['GET'])
def get_locations():
    """獲取所有位置"""
    locations = set()
    for item in tourism_data:
        loc = _f(item, "縣市", "city")
        if loc:
            locations.add(loc)
    
    return jsonify({
        "locations": sorted(list(locations))
    })


@app.route('/api/data/places', methods=['GET'])
def get_places():
    """提供前端行程規劃使用的真實景點資料。"""
    destination = request.args.get("destination", "").strip()
    requested_type = request.args.get("type", "景點").strip()
    try:
        limit = max(1, min(int(request.args.get("limit", 100)), 500))
    except ValueError:
        return jsonify({"error": "limit 必須是整數"}), 400
    if not destination:
        return jsonify({"error": "請提供目的地"}), 400

    def compact(value):
        return str(value or "").replace("台", "臺").replace("市", "").replace("縣", "").lower()

    target = compact(destination)
    city_targets = {compact(city) for city in (
        "台北", "新北", "桃園", "新竹", "苗栗", "台中", "彰化", "南投",
        "雲林", "嘉義", "台南", "高雄", "屏東", "花蓮", "台東", "宜蘭",
        "基隆", "新竹縣", "嘉義縣", "澎湖", "金門", "連江"
    )}
    is_city_query = target in city_targets
    places = []
    seen = set()
    type_synonyms = {"景點": "scenic", "餐廳": "restaurant", "美食": "restaurant", "飯店": "hotel", "住宿": "hotel", "活動": "event", "步道": "scenic"}
    allowed_types = {requested_type} if requested_type else {"景點", "步道", "活動"}
    allowed_source_types = {type_synonyms.get(t, t) for t in allowed_types}
    for item in tourism_data:
        actual_type = _f(item, "type", "source_type")
        if actual_type not in allowed_types and actual_type not in allowed_source_types:
            continue
        location_text = compact(f"{_f(item, '縣市', 'city')} {_f(item, '區域', 'district')}")
        name_text = compact(_f(item, "名稱", "name"))
        if is_city_query and target not in location_text:
            continue
        if not is_city_query and target not in location_text and target not in name_text:
            continue
        name = str(_f(item, "名稱", "name")).strip()
        if not name or name in seen:
            continue
        seen.add(name)
        places.append(item)
        if len(places) >= limit:
            break
    return jsonify({"destination": destination, "count": len(places), "places": places})


@app.route('/api/plan/generate', methods=['POST'])
def generate_plan():
    """生成行程"""
    data = request.get_json(silent=True) or {}
    
    destination = data.get('destination', '')
    days = data.get('days', 3)
    budget = data.get('budget', 10000)
    interests = data.get('interests', [])
    pace = str(data.get('style') or data.get('pace') or 'moderate').strip().lower()
    if pace not in ('packed', 'moderate', 'leisurely'):
        pace = 'moderate'
    
    if not destination:
        return jsonify({"error": "請輸入目的地"}), 400
    
    try:
        days = int(days)
        budget = float(budget)
        if days < 1 or days > 30:
            return jsonify({"error": "旅遊天數必須介於 1 至 30 天"}), 400
        if budget < 0:
            return jsonify({"error": "預算不可為負數"}), 400
        if not isinstance(interests, list):
            interests = [str(interests)] if interests else []

        if not planner:
            return jsonify({"error": "旅遊規劃系統未就緒，請確保 Ollama 已啟動"}), 503

        # 調用規劃器
        itinerary = planner.plan_itinerary(
            destination=destination,
            days=days,
            budget=budget,
            interests=interests,
            pace=pace
        )
        
        return jsonify({
            "status": "success",
            "itinerary": itinerary
        })
    
    except Exception as e:
        logger.error(f"Planning error: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/destination/<destination>', methods=['GET'])
def get_destination_info(destination):
    """Get destination detailed information"""
    if not planner:
        return jsonify({"error": "Tourism planning system not ready"}), 503
    
    try:
        info = planner.get_destination_info(destination)
        return jsonify(info)
    except Exception as e:
        logger.error(f"Query error: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/scrape/tdx', methods=['POST'])
@login_required
def scrape_tdx():
    """Manually execute TDX scraper"""
    try:
        logger.info("Starting TDX scraper execution...")
        
        scraper = TDXScraper()
        processor = DataProcessor()
        
        # Fetch data
        scenic_spots = scraper.fetch_scenic_spots()
        restaurants = scraper.fetch_restaurants()
        hotels = scraper.fetch_hotels()
        
        # Merge and process
        all_data = scenic_spots + restaurants + hotels
        unique_data = pipeline.clean(all_data, source="TDX")
        
        # Save data
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        processor.save_json(unique_data, f"taiwan_tourism_data_{timestamp}.json")
        processor.save_csv(unique_data, f"taiwan_tourism_data_{timestamp}.csv")

        global tourism_data, planner
        tourism_data = unique_data
        planner = initialize_system(str(build_knowledge_base(tourism_data)))
        
        return jsonify({
            "status": "success",
            "message": f"Scraper complete! Collected {len(unique_data)} data items",
            "scenic_spots": len(scenic_spots),
            "restaurants": len(restaurants),
            "hotels": len(hotels)
        })
    
    except Exception as e:
        logger.error(f"Scraper error: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/scrape/dynamic', methods=['POST'])
@login_required
def scrape_dynamic():
    """擷取已設定且經授權的動態旅遊網站。"""
    data = request.get_json(silent=True) or {}
    website = str(data.get("website", "kkday")).lower()
    keyword = str(data.get("keyword", "台灣旅遊")).strip()
    headless = data.get("headless", True)
    if isinstance(headless, str):
        headless = headless.strip().lower() not in {"false", "0", "no", "off"}
    try:
        raw = DynamicTravelScraper(website, headless=headless).search(keyword)
        cleaned = pipeline.clean(raw, source=website)
        path = pipeline.save(cleaned, f"dynamic_{website}_{datetime.now():%Y%m%d_%H%M%S}.json")
        global tourism_data, planner
        tourism_data = pipeline.clean(tourism_data + cleaned, source=website)
        planner = initialize_system(str(build_knowledge_base(tourism_data)))
        return jsonify({"status": "success", "website": website, "count": len(cleaned), "file": str(path), "quality": pipeline.quality_report(cleaned)})
    except Exception as e:
        logger.error(f"Dynamic scraper error: {e}")
        return jsonify({"error": str(e)}), 400


@app.route('/api/scrape/authorized', methods=['POST'])
@login_required
def scrape_authorized():
    """從已取得授權的旅遊 API 擷取資料。"""
    data = request.get_json(silent=True) or {}
    keyword = str(data.get("keyword", "台灣旅遊")).strip()
    try:
        raw = AuthorizedTravelAPI(
            url=str(data.get("url", "")).strip(),
            api_key=str(data.get("api_key", "")).strip(),
        ).search(keyword, limit=data.get("limit", 30))
        cleaned = pipeline.clean(raw, source="authorized_api")
        path = pipeline.save(cleaned, f"authorized_{datetime.now():%Y%m%d_%H%M%S}.json")
        global tourism_data, planner
        tourism_data = pipeline.clean(tourism_data + cleaned, source="authorized_api")
        planner = initialize_system(str(build_knowledge_base(tourism_data)))
        return jsonify({
            "status": "success",
            "source": "authorized_api",
            "count": len(cleaned),
            "file": str(path),
            "quality": pipeline.quality_report(cleaned),
        })
    except Exception as e:
        logger.error(f"Authorized API error: {e}")
        return jsonify({"error": str(e)}), 400


@app.route('/api/data/quality', methods=['GET'])
def data_quality():
    """回傳目前知識庫的資料品質報告。"""
    return jsonify(pipeline.quality_report(tourism_data))


@app.route('/api/evaluate/retrieval', methods=['POST'])
def evaluate_retrieval():
    """以 request body 的 query/expected_names 案例評估 RAG Recall@K。"""
    if not planner:
        return jsonify({"error": "旅遊規劃系統未就緒"}), 503
    data = request.get_json(silent=True) or {}
    return jsonify(retrieval_recall(planner.rag, data.get("cases", []), int(data.get("top_k", 5))))


@app.route('/api/evaluate/plan', methods=['POST'])
def evaluate_plan():
    """評估單次行程輸出的結構完整性與預算符合率。"""
    data = request.get_json(silent=True) or {}
    plan_result = data.get("result", data)
    try:
        budget = float(data.get("budget", plan_result.get("budget", 0)))
        return jsonify({
            "status": "success",
            "quality": plan_quality_report(plan_result),
            "budget": budget_compliance(plan_result, budget),
        })
    except (TypeError, ValueError) as e:
        return jsonify({"error": f"評估資料格式錯誤: {e}"}), 400


@app.errorhandler(404)
def not_found(error):
    """404 handler"""
    return jsonify({"error": "API endpoint not found"}), 404


@app.errorhandler(500)
def server_error(error):
    """500 handler"""
    return jsonify({"error": "Server error"}), 500


# 模組載入時就初始化，這樣不管用 python -m backend.app 或 gunicorn 啟動，planner 都會就緒
initialize_app()


if __name__ == '__main__':
    logger.info("="*50)
    logger.info("Flask API server starting")
    logger.info("="*50)
    logger.info("Address: http://localhost:5000")
    logger.info("="*50)
    
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=False,
        use_reloader=False
    )
