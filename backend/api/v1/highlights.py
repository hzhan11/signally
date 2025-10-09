import logging
import uuid
from typing import Optional, List, Dict, Any, Union
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from backend.api.deps import ChromaDBSingleton

router = APIRouter()

SUPPORTED_PREDICTIONS = {"高开", "低开"}

class GenerateHighlightsRequest(BaseModel):
    stock_id: Optional[str] = Field(None, description="指定股票代码；为空则对所有在 conclusions 中出现的股票处理")
    rebuild: bool = Field(False, description="是否重建(删除并重新生成指定股票的 highlights)")

class HighlightItem(BaseModel):
    id: str
    stock_id: str
    datetime: str
    hit: Union[bool, str, None] = None  # bool 或 'unavailable'
    last_close_price: Optional[float] = None
    open_15min_price: Optional[float] = None
    conclusion: Optional[str] = None
    reason: Optional[str] = None
    confidence: Optional[float] = None
    diff: Optional[float] = None

class GenerateHighlightsResponse(BaseModel):
    stock_id: str
    generated: int
    items: List[HighlightItem]

class HighlightsListResponse(BaseModel):
    stock_id: str
    total: int
    items: List[HighlightItem]

# -------------------------
# Utility functions
# -------------------------

def _build_price_maps(info_results: Dict[str, Any], stock_id: str):
    """Build maps for open15 and close prices keyed by date (YYYYMMDD)."""
    open15_map: Dict[str, float] = {}
    close_map: Dict[str, float] = {}
    metas = info_results.get("metadatas", []) or []
    for meta in metas:
        if not isinstance(meta, dict):
            continue
        if meta.get("attached_stock_id") != stock_id:
            continue
        dt = meta.get("datetime")
        t = meta.get("type")
        if not dt or not t:
            continue
        val_raw = meta.get("value")
        try:
            val = float(val_raw)
        except (TypeError, ValueError):
            continue
        if t == "open_15m_avg":
            open15_map[dt] = val
        elif t == "close":
            close_map[dt] = val
    logging.info(f"[highlights.generate] _build_price_maps stock={stock_id} open15={len(open15_map)} close={len(close_map)}")
    return open15_map, close_map

def _find_prev_trading_date(trading_dates_sorted: List[str], date_str: str) -> Optional[str]:
    prev = None
    for d in trading_dates_sorted:
        if d < date_str:
            prev = d
        elif d >= date_str:
            break
    return prev

# -------------------------
# GET: generate / update highlights (no request body)
# -------------------------
@router.get("/generate", response_model=List[GenerateHighlightsResponse])
async def generate_highlights():
    """生成 / 更新所有 active 股票的 highlights (无请求体)。"""
    db = ChromaDBSingleton()

    concl_sc = db.get_collection("conclusions")
    info_sc = db.get_collection("info")
    hl_sc = db.get_collection("highlights")
    stocks_sc = db.get_collection("stocks")

    stocks_results = stocks_sc.get(include=["metadatas"]) or {}
    stock_ids = stocks_results.get("ids", []) or []
    stock_metas = stocks_results.get("metadatas", []) or []
    active_stocks = {sid for i, sid in enumerate(stock_ids) if isinstance(stock_metas[i], dict) and stock_metas[i].get("status") == "active"}
    logging.info(f"[highlights.generate] active_stocks={list(active_stocks)}")

    concl_results = concl_sc.get(include=["metadatas", "documents"]) or {}
    concl_metas = concl_results.get("metadatas", []) or []
    concl_docs = concl_results.get("documents", []) or []
    if not concl_metas:
        raise HTTPException(status_code=404, detail="No conclusions found")

    concl_stocks = {m.get("stock") for m in concl_metas if isinstance(m, dict) and m.get("stock")}
    target_stocks = sorted(concl_stocks & active_stocks)
    logging.info(f"[highlights.generate] target_stocks={target_stocks}")

    info_results = info_sc.get(include=["metadatas"]) or {}

    existing_hl = hl_sc.get(include=["metadatas"]) or {}
    ex_ids = existing_hl.get("ids", []) or []
    ex_metas = existing_hl.get("metadatas", []) or []
    existing_index: Dict[str, Dict[str, str]] = {}
    for i, mid in enumerate(ex_ids):
        meta = ex_metas[i] if i < len(ex_metas) else {}
        if not isinstance(meta, dict):
            continue
        sid = meta.get("stock_id")
        dt = meta.get("datetime")
        if not sid or not dt:
            continue
        existing_index.setdefault(sid, {})[dt] = mid

    responses: List[GenerateHighlightsResponse] = []

    for stock_id in target_stocks:
        open15_map, close_map = _build_price_maps(info_results, stock_id)
        trading_dates_sorted = sorted(set(open15_map.keys()) | set(close_map.keys()))
        logging.info(f"[highlights.generate] stock={stock_id} trading_dates={trading_dates_sorted}")

        per_date: Dict[str, Dict[str, Any]] = {}
        for i, meta in enumerate(concl_metas):
            if not isinstance(meta, dict) or meta.get("stock") != stock_id:
                continue
            pred = meta.get("prediction")
            if pred not in SUPPORTED_PREDICTIONS:
                continue
            dt = meta.get("datetime")
            if not dt:
                continue
            conf_raw = meta.get("confidence")
            try:
                conf_val = float(conf_raw) if conf_raw is not None else 0.0
            except (TypeError, ValueError):
                conf_val = 0.0
            prev = per_date.get(dt)
            if (prev is None) or (conf_val > prev.get("_conf", -1)):
                per_date[dt] = {"prediction": pred, "confidence": conf_raw, "doc": concl_docs[i] if i < len(concl_docs) else "", "_conf": conf_val}
        logging.info(f"[highlights.generate] stock={stock_id} selected_dates={list(per_date.keys())}")

        items: List[HighlightItem] = []
        stock_existing_dates = existing_index.get(stock_id, {})

        for dt, data in sorted(per_date.items()):
            prediction = data["prediction"]
            confidence = data["confidence"]
            doc = (data.get("doc") or "").strip()
            open15 = open15_map.get(dt)
            prev_date = _find_prev_trading_date(trading_dates_sorted, dt)
            prev_close = close_map.get(prev_date) if prev_date else None
            have_prices = (open15 is not None) and (prev_close is not None)
            diff_val = (open15 - prev_close) if have_prices else -1.0
            if have_prices:
                hit: Union[bool, str, None] = (diff_val > 0) if prediction == "高开" else (diff_val < 0)
            else:
                hit = "unavailable"
            open_val_out = open15 if open15 is not None else -1.0
            prev_close_out = prev_close if prev_close is not None else -1.0
            highlight_id = stock_existing_dates.get(dt) or f"{stock_id}_{dt}_highlight"
            metadata = {"stock_id": stock_id, "datetime": dt, "last_close_price": prev_close_out, "open_15min_price": open_val_out, "conclusion": prediction, "reason": doc, "hit": hit, "confidence": confidence if confidence is not None else -1.0, "diff": diff_val}
            summary_parts = [dt, f"预测{prediction}"]
            summary_parts.append(f"开盘15分均价 {open15:.2f}" if open15 is not None else "开盘15分均价 未得出")
            if prev_close is not None and prev_date:
                summary_parts.append(f"前一交易日({prev_date})收盘 {prev_close:.2f}")
            else:
                summary_parts.append("前一交易日收盘 未得出")
            summary_parts.append("命中" if isinstance(hit, bool) and hit else ("未命中" if isinstance(hit, bool) else "数据不足"))
            summary_text = "，".join(summary_parts)
            hl_sc.upsert(ids=[highlight_id], metadatas=[metadata], documents=[summary_text])
            logging.info(f"[highlights.generate] upsert id={highlight_id} meta={metadata}")
            items.append(HighlightItem(id=highlight_id, stock_id=stock_id, datetime=dt, hit=hit, last_close_price=prev_close_out, open_15min_price=open_val_out, conclusion=prediction, reason=doc, confidence=confidence if confidence is not None else -1.0, diff=diff_val))
        responses.append(GenerateHighlightsResponse(stock_id=stock_id, generated=len(items), items=items))

    logging.info(f"[highlights.generate] finished responses_count={len(responses)}")
    return responses

# -------------------------
# GET: list highlights for a stock
# -------------------------
@router.get("/list/{stock_id}", response_model=HighlightsListResponse)
async def list_highlights(stock_id: str):
    logging.info(f"[highlights.list] stock_id={stock_id}")
    db = ChromaDBSingleton()
    hl_sc = db.get_collection("highlights")
    results = hl_sc.get(include=["metadatas", "documents"]) or {}
    metas = results.get("metadatas", []) or []
    ids = results.get("ids", []) or []

    items: List[HighlightItem] = []
    for i, meta in enumerate(metas):
        if not isinstance(meta, dict):
            continue
        if meta.get("stock_id") != stock_id:
            continue
        items.append(HighlightItem(
            id=ids[i] if i < len(ids) else str(uuid.uuid4()),
            stock_id=stock_id,
            datetime=meta.get("datetime"),
            hit=meta.get("hit"),
            last_close_price=meta.get("last_close_price"),
            open_15min_price=meta.get("open_15min_price"),
            conclusion=meta.get("conclusion"),
            reason=meta.get("reason"),
            confidence=meta.get("confidence"),
            diff=meta.get("diff"),
        ))

    items.sort(key=lambda x: x.datetime or "", reverse=True)
    logging.info(f"[highlights.list] stock_id={stock_id} items={len(items)}")
    return HighlightsListResponse(stock_id=stock_id, total=len(items), items=items)