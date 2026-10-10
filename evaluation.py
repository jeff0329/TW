"""旅遊 RAG 與行程結果的可重複評估。"""

import re
from typing import Any, Dict, Iterable, List


def retrieval_recall(rag: Any, cases: Iterable[Dict[str, Any]], top_k: int = 5) -> Dict[str, Any]:
    """以人工標註的來源名稱計算 Recall@K。"""
    rows: List[Dict[str, Any]] = []
    hits = 0
    total = 0
    for case in cases:
        expected = {str(name).strip() for name in case.get("expected_names", []) if str(name).strip()}
        actual = {str(item.get("名稱", "")).strip() for item in rag.retrieve_relevant_info(case["query"], top_k)}
        matched = expected & actual
        hits += len(matched)
        total += len(expected)
        rows.append({"query": case["query"], "expected": sorted(expected), "matched": sorted(matched)})
    return {"metric": f"recall@{top_k}", "score": round(hits / total, 4) if total else 0.0, "cases": rows}


def budget_compliance(plan_result: Any, budget: float) -> Dict[str, Any]:
    """優先採用行程規劃器已計算好的 budget_summary（精確數值）；
    若無結構化結果，才退而從模型回覆文字擷取金額（僅供粗略參考）。"""
    if isinstance(plan_result, dict):
        summary = plan_result.get("budget_summary")
        if isinstance(summary, dict) and summary.get("estimated_total") is not None:
            return {
                "metric": "budget_compliance",
                "budget": budget,
                "reported_total": summary.get("estimated_total"),
                "compliant": summary.get("compliant"),
                "source": "structured_planner",
            }
        text = str(plan_result.get("plan", ""))
    else:
        text = str(plan_result)

    matches = re.findall(r"(?:總預算|預算總計|合計|total)[^\d]{0,12}([\d,]+)", text, re.IGNORECASE)
    spent = float(matches[-1].replace(",", "")) if matches else None
    return {
        "metric": "budget_compliance",
        "budget": budget,
        "reported_total": spent,
        "compliant": spent <= budget if spent is not None else None,
        "source": "text_regex_fallback",
    }


def plan_quality_report(plan_result: Dict[str, Any]) -> Dict[str, Any]:
    """檢查行程結果是否包含基本可用欄位與 RAG 來源。"""
    plan = str(plan_result.get("plan", ""))
    sources = plan_result.get("recommended_places", [])
    required_terms = ("交通", "景點", "餐廳", "預算")
    return {
        "metric": "plan_quality",
        "has_plan": bool(plan.strip()),
        "required_sections": {term: term in plan for term in required_terms},
        "source_count": len(sources),
        "source_grounded": len(sources) > 0,
    }