import uuid
import os
from typing import Dict, List, Any, Union

from fastapi import HTTPException

from backend.api.deps import ChromaDBSingleton
from backend.api.v1.highlights import GenerateHighlightsResponse, HighlightItem, _find_prev_trading_date, \
    SUPPORTED_PREDICTIONS, _build_price_maps

# 禁用ChromaDB的遥测功能
os.environ['ANONYMIZED_TELEMETRY'] = 'False'
os.environ['CHROMA_TELEMETRY_DISABLED'] = 'True'

from chromadb import HttpClient
from chromadb.config import Settings
from backend.common import sconfig

# 创建客户端时明确禁用遥测
client = HttpClient(
    host="localhost",
    port=sconfig.settings.DB_PORT,
    settings=Settings(anonymized_telemetry=False)
)

def test_update_stock():
    sc = client.get_or_create_collection("stocks")
    sc.update(
        ids=["sh600010"],
        # 更新元数据，会覆盖已有 metadata 对应字段，如果想保留其他字段，需要先获取原来的 metadata
        metadatas=[{"name": "包钢股份", "usid": "NA","status":"inactive"}]
    )

def test_delete_info_data():
    client.delete_collection("info")

def test_add_log_connection():
    sc = client.get_collection("log")
    print(sc.count(), sc.name)

def test_delete_info_log():
    client.delete_collection("log")

def test_add_stock():
    new_documents = ["内蒙古包钢钢联股份有限公司的主营业务是矿产资源开发利用、钢铁产品的生产与销售。公司的主要产品是板材、钢管、型材、钢轨、线棒材、稀土钢新材料、稀土精矿、萤石、焦副产品。公司荣获工业和信息化部“工业产品生态设计示范企业”、内蒙古民族品牌建设标杆企业、内蒙古行业标志性品牌、内蒙古百强品牌等荣誉称号。"]  # 文档内容
    new_metadatas = [{"name": "包钢股份"}]  # 元数据
    new_ids = ["sh600010"]  # 唯一ID

    sc = client.get_or_create_collection("stocks")

    sc.add(
        documents=new_documents,
        metadatas=new_metadatas,
        ids=new_ids
    )

def test_stock_clean():
    sc = client.get_or_create_collection("stocks")
    sc.delete(ids=["sz002594"])

def test_get_stocks():
    sc = client.get_collection("stocks")
    print(sc.count())

def test_append_conclusion():

    sc = client.get_or_create_collection("conclusions")

    new_documents = ["比亚迪在北美发力"]  # 文档内容
    new_metadatas = [{"stock": "sz002594","datetime":"20250918","prediction":"高开","confidence":0.8}]
    new_ids = [f"sz002594_{str(uuid.uuid4())}"]  # 唯一ID

    sc.add(
        documents=new_documents,
        metadatas=new_metadatas,
        ids=new_ids
    )

def test_clear_conclusion():
    sc = client.get_or_create_collection("conclusions")
    sc.delete(ids=["sz002594_f39159c0-8192-4386-b268-ea958b0424ae","sz002594_15b22733-eb54-4cd5-8ffc-f87114208677","sz002594_6df9f334-6d46-4b5d-bbd7-30e73cc89805"])

def test_add_stock_price_info_data():
    sc = client.get_or_create_collection("info")

    info_data = [
        {"id":"71fae6d1-64ca-4a9c-b7f4-0af8d0912a8e", "datetime":"20250930", "content":""},
    ]

    for one in info_data:
        metadata = {
            "id": one["id"],
            "attached_stock_id": "sz002594",
            "datetime": one["datetime"],
            "type": "close",
            "value": "109.21"
        }

        sc.upsert(
            ids=[one["id"]],
            documents=[one["content"]],
            metadatas=[metadata]
        )

# 新增: 打印所有集合的全部数据（分页避免超内存）
def test_print_all():
    collections = client.list_collections()
    if not collections:
        print("[PRINT_ALL] no collections found")
        return

    page_size = 100
    for col in collections:
        print("")
        name = getattr(col, 'name', None) or getattr(col, 'id', 'unknown')
        try:
            sc = client.get_collection(name)
        except Exception as e:
            print(f"[PRINT_ALL] skip collection={name} (cannot get: {e})")
            continue
        try:
            total = sc.count()
        except Exception as e:
            print(f"[PRINT_ALL] collection={name} count error: {e}")
            continue
        print(f"[PRINT_ALL] collection={name} total={total}")
        if total == 0:
            print(f"[PRINT_ALL] collection={name} empty")
            continue
        offset = 0
        while offset < total:
            try:
                batch = sc.get(limit=page_size, offset=offset, include=['metadatas','documents'])
            except Exception as e:
                print(f"[PRINT_ALL] collection={name} get error at offset={offset}: {e}")
                break
            ids = batch.get('ids', []) if isinstance(batch, dict) else []
            documents = batch.get('documents', []) or []
            metadatas = batch.get('metadatas', []) or []
            if not ids:
                break
            for i, _id in enumerate(ids):
                meta = metadatas[i] if i < len(metadatas) else {}
                doc = documents[i] if i < len(documents) else ''
                short_doc = (doc[:80] + '...') if doc and len(doc) > 80 else doc
                # 按 key 排序后的 meta 输出（保持中文 / 非 ASCII 字符）
                if not isinstance(meta, dict):
                    meta_sorted_str = str(meta)
                else:
                    # 使用 k=v 形式更紧凑，按 key 排序
                    parts = [f"{k}={repr(meta[k])}" for k in sorted(meta.keys())]
                    meta_sorted_str = '{' + ', '.join(parts) + '}'
                print(f"- {name} #{offset + i} id={_id} meta={meta_sorted_str} doc={short_doc}")
            offset += len(ids)
    print("\n[PRINT_ALL] done")

# 新增: 按给定 id 在所有集合中删除匹配的文档
# 目标: 删除 id = "88171217-db91-49fa-8034-773078563013" (可通过环境变量覆盖)
# 用法: pytest backend\db\test_dbms.py::test_delete_from_any_collection -s
# 可设置环境变量 TARGET_ID 指定其他 id

def test_generate_highlights():
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
    print(f"[highlights.generate] active_stocks={list(active_stocks)}")

    concl_results = concl_sc.get(include=["metadatas", "documents"]) or {}
    concl_metas = concl_results.get("metadatas", []) or []
    concl_docs = concl_results.get("documents", []) or []
    if not concl_metas:
        raise HTTPException(status_code=404, detail="No conclusions found")

    concl_stocks = {m.get("stock") for m in concl_metas if isinstance(m, dict) and m.get("stock")}
    target_stocks = sorted(concl_stocks & active_stocks)
    print(f"[highlights.generate] target_stocks={target_stocks}")

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
        print(f"[highlights.generate] stock={stock_id} trading_dates={trading_dates_sorted}")

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
        print(f"[highlights.generate] stock={stock_id} selected_dates={list(per_date.keys())}")

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
            print(f"[highlights.generate] upsert id={highlight_id} meta={metadata}")
            items.append(HighlightItem(id=highlight_id, stock_id=stock_id, datetime=dt, hit=hit, last_close_price=prev_close_out, open_15min_price=open_val_out, conclusion=prediction, reason=doc, confidence=confidence if confidence is not None else -1.0, diff=diff_val))
        responses.append(GenerateHighlightsResponse(stock_id=stock_id, generated=len(items), items=items))

    print(f"[highlights.generate] finished responses_count={len(responses)}")

def test_delete_from_any_collection():
    target_ids = ["2a3410e3-e807-4c06-9c01-eed8627a276a","b0af6c40-8582-48cd-bb96-52eab33c4161","b6355969-b32b-44a1-8b0a-0b56eefb52e6"]
    collections = client.list_collections()
    found_any = False
    for target_id in target_ids:
        print(f"[DELETE_ANY] target_id={target_id}")
        for col in collections:
            name = getattr(col, 'name', None) or getattr(col, 'id', 'unknown')
            try:
                sc = client.get_collection(name)
            except Exception as e:
                print(f"[DELETE_ANY] skip collection={name} (cannot get: {e})")
                continue
            try:
                batch = sc.get(ids=[target_id], include=['metadatas'])
            except Exception as e:
                print(f"[DELETE_ANY] collection={name} get error: {e}")
                continue
            ids = batch.get('ids', []) if isinstance(batch, dict) else []
            if ids:
                try:
                    sc.delete(ids=[target_id])
                    print(f"[DELETE_ANY] deleted id={target_id} from collection={name}")
                    found_any = True
                except Exception as e:
                    print(f"[DELETE_ANY] failed delete id={target_id} from collection={name}: {e}")
            else:
                print(f"[DELETE_ANY] not found in collection={name}")
        if not found_any:
            print("[DELETE_ANY] target id not present in any collection")

# 新增: 按名称删除集合 (使用环境变量 TARGET_COLLECTION 覆盖)
# 用法:
#   1) 删除默认 info 集合: pytest backend\db\test_dbms.py::test_delete_collection_by_name -s
#   2) 指定集合: set TARGET_COLLECTION=stocks && pytest backend\db\test_dbms.py::test_delete_collection_by_name -s
#   3) 使用 PowerShell: $env:TARGET_COLLECTION='stocks'; pytest backend/db/test_dbms.py::test_delete_collection_by_name -s

def test_delete_collection_by_name():
    target = "conclusion"
    if not target:
        print("[DELETE_COLLECTION] empty target name")
        return
    try:
        client.delete_collection(target)
        print(f"[DELETE_COLLECTION] deleted collection={target}")
    except Exception as e:
        print(f"[DELETE_COLLECTION] failed collection={target}: {e}")

# 新增: 批量插入 09:30-09:45 open 平均值数据 (含端点)
# 数据来源：
#  sz002594 09:30:00-09:45:00 open 均值 (含端点):
#    20250917: 108.5347
#    20250918: 110.9253
#    20250919: 109.5453
#    20250923: 107.1540
#    20250925: 105.3440
# 说明：
#  - 采用固定 ID 格式: sz002594_<date>_open15m
#  - metadata 中保留 window 方便区分
#  - value 统一保留 4 位小数（字符串形式，保持与现有样例一致）
# 运行方式：pytest backend\db\test_dbms.py::test_insert_branch_data -s

def test_insert_branch_data():
    # 改为写入收盘价 close 数据
    sc = client.get_or_create_collection("info")
    stock_id = "sz002594"
    # 新数据（日期 -> close 价格，4 位小数）
    records = [
        {"date": "20250925", "close": 107.50},
    ]

    for r in records:
        rid = f"{stock_id}_{r['date']}_close"
        metadata = {
            "attached_stock_id": stock_id,
            "datetime": r["date"],
            "type": "close",
            "value": r['close'],
        }
        sc.upsert(
            ids=[rid],
            documents=[""],  # 文档为空占位
            metadatas=[metadata]
        )
        print(f"[INSERT] {rid} -> {metadata}")
    print("[INSERT] done (close prices)")

def test_evaluate_conclusions():
    """
    评估 conclusions 中的 高开/低开 预测是否与 实际 (开盘15分钟均价 vs 前一交易日收盘) 的差值方向一致。

    规则:
      - 获取 conclusions 中每条记录 (prediction in {高开, 低开, 平价})
      - 对应日期 D:
          open15 = info 中 type=open_15m_avg 且 datetime=D 的 value
          prev_close = info 中所有 type=close 且 datetime < D 的日期里最近的一天的 value
      - diff = open15 - prev_close
      - 判断:
          高开: diff > 0 -> 命中
          低开: diff < 0 -> 命中
          平价: 统一输出 预测无效 (不纳入命中统计)
      - 缺数据则标记 数据缺失
    输出示例:
      20250919 预测 低开(85%) ，当天开盘15分钟均价 109.54，前一交易日(20250918)收盘价 109.71，预测命中，预测依据：<结论文本>
    """
    tolerance = 0.01  # 当前未用于平价判断（平价直接标记预测无效）
    stock_id = "sz002594"

    try:
        concl_sc = client.get_or_create_collection("conclusions")
        info_sc = client.get_or_create_collection("info")
    except Exception as e:
        print(f"[EVAL] 获取集合失败: {e}")
        return

    try:
        concl_batch = concl_sc.get(limit=2000, include=["metadatas", "documents"]) or {}
    except Exception as e:
        print(f"[EVAL] 获取结论数据失败: {e}")
        return

    concl_metas = concl_batch.get("metadatas", []) or []
    concl_docs = concl_batch.get("documents", []) or []
    concl_ids = concl_batch.get("ids", []) or []

    # 组装带文档的结论条目
    concl_items = []
    for i, meta in enumerate(concl_metas):
        if not isinstance(meta, dict):
            continue
        if meta.get("stock") != stock_id:
            continue
        if not meta.get("prediction") or not meta.get("datetime"):
            continue
        doc = concl_docs[i] if i < len(concl_docs) else ""
        concl_items.append({
            "meta": meta,
            "doc": doc,
            "id": concl_ids[i] if i < len(concl_ids) else None
        })

    # info 数据
    open15_map = {}
    close_map = {}
    try:
        info_batch = info_sc.get(limit=10000, include=["metadatas"]) or {}
    except Exception as e:
        print(f"[EVAL] 获取 info 数据失败: {e}")
        return

    info_metas = info_batch.get("metadatas", []) or []
    for m in info_metas:
        if not isinstance(m, dict):
            continue
        dt = m.get("datetime")
        t = m.get("type")
        if not dt or not t:
            continue
        val_raw = m.get("value")
        try:
            val = float(val_raw)
        except (TypeError, ValueError):
            continue
        if t == "open_15m_avg":
            open15_map[dt] = val
        elif t == "close":
            close_map[dt] = val

    # 所有出现过的交易日
    trading_dates_sorted = sorted(set(open15_map.keys()) | set(close_map.keys()))

    def find_prev_trading_date(date_str: str):
        prev = None
        for d in trading_dates_sorted:
            if d < date_str:
                prev = d
            elif d >= date_str:
                break
        return prev

    def find_prev_close(date_str: str):
        prev_trading = find_prev_trading_date(date_str)
        if not prev_trading:
            return None, None
        return prev_trading, close_map.get(prev_trading)

    print("[EVAL] 预测评估结果:")
    for item in sorted(concl_items, key=lambda x: x["meta"].get("datetime")):
        meta = item["meta"]
        doc = (item.get("doc") or "").strip()
        d = meta.get("datetime")
        pred = meta.get("prediction")
        confidence = meta.get("confidence")
        # 格式化信心百分比
        if isinstance(confidence, (int, float)):
            conf_str = f"{round(confidence * 100)}%"
        else:
            conf_str = "--"

        open15 = open15_map.get(d)
        prev_date, prev_close = find_prev_close(d)

        if pred == "平价":
            status = "预测无效"
        else:
            if open15 is None or prev_date is None or prev_close is None:
                if prev_date is None:
                    status = "数据缺失(无上一交易日)"
                elif prev_close is None:
                    status = f"数据缺失(上一交易日{prev_date}无close)"
                else:
                    status = "数据缺失"
            else:
                diff = open15 - prev_close
                if pred == "高开":
                    status = "预测命中" if diff > 0 else "预测未命中"
                elif pred == "低开":
                    status = "预测命中" if diff < 0 else "预测未命中"
                else:
                    status = f"不支持的预测类型:{pred}"

        open15_txt = f"{open15:.2f}" if open15 is not None else "NA"
        prev_close_txt = f"{prev_close:.2f}" if prev_close is not None else "NA"
        prev_date_txt = prev_date if prev_date is not None else "NA"

        rationale = f"，预测依据：{doc}" if doc else ""
        print(f"{d} 预测 {pred}({conf_str}) ，当天开盘15分钟均价 {open15_txt}，前一交易日({prev_date_txt})收盘价 {prev_close_txt}，{status}{rationale}")

def test_cleanup_before_cutoff():
    """清理所有集合中 datetime < cutoff (默认 20251020) 的文档。

    用法 (CMD):
      set CLEAN_CUTOFF=20251020 & pytest backend\db\test_db_mgr.py::test_cleanup_before_cutoff -s
    PowerShell:
      $env:CLEAN_CUTOFF='20251020'; pytest backend/db/test_db_mgr.py::test_cleanup_before_cutoff -s

    说明:
      - cutoff 为字符串形式 YYYYMMDD，比较采用字典序 (同格式情况下有效)
      - 仅当 metadata 中存在 datetime 且长度为 8 的记录进行判定
      - stocks 集合通常无日期，跳过不删除
      - 删除操作按批次执行，避免一次性删除过多导致异常
    """
    cutoff = os.getenv("CLEAN_CUTOFF", "20251020")
    if not cutoff.isdigit() or len(cutoff) != 8:
        print(f"[CLEAN] 非法 cutoff={cutoff}，需为 YYYYMMDD 格式")
        return
    try:
        collections = client.list_collections() or []
    except Exception as e:
        print(f"[CLEAN] 获取集合列表失败: {e}")
        return
    if not collections:
        print("[CLEAN] 无集合可清理")
        return

    total_deleted = 0
    per_collection_stats = {}
    batch_size = 500
    for col in collections:
        name = getattr(col, 'name', None) or getattr(col, 'id', 'unknown')
        try:
            sc = client.get_collection(name)
        except Exception as e:
            print(f"[CLEAN] 跳过集合={name} (获取失败: {e})")
            continue
        # 分页拉取所有数据 (仅需 metadatas + ids)
        offset = 0
        to_delete: List[str] = []
        while True:
            try:
                batch = sc.get(limit=1000, offset=offset, include=["metadatas"])
            except Exception as e:
                print(f"[CLEAN] 集合={name} 在 offset={offset} 获取失败: {e}")
                break
            ids = batch.get("ids", []) if isinstance(batch, dict) else []
            metas = batch.get("metadatas", []) if isinstance(batch, dict) else []
            if not ids:
                break
            for i, _id in enumerate(ids):
                meta = metas[i] if i < len(metas) else {}
                if not isinstance(meta, dict):
                    continue
                dt = meta.get("datetime")
                if isinstance(dt, str) and len(dt) == 8 and dt.isdigit():
                    if dt < cutoff:
                        to_delete.append(_id)
            offset += len(ids)
        if not to_delete:
            per_collection_stats[name] = {"deleted": 0, "skipped": 0}
            print(f"[CLEAN] 集合={name} 无需删除记录")
            continue
        # 批量删除
        deleted_here = 0
        for i in range(0, len(to_delete), batch_size):
            slice_ids = to_delete[i:i+batch_size]
            try:
                sc.delete(ids=slice_ids)
                deleted_here += len(slice_ids)
            except Exception as e:
                print(f"[CLEAN] 集合={name} 删除批次失败 (size={len(slice_ids)}): {e}")
        total_deleted += deleted_here
        per_collection_stats[name] = {"deleted": deleted_here, "skipped": 0}
        print(f"[CLEAN] 集合={name} 已删除 {deleted_here} 条 (cutoff={cutoff})")

    print(f"[CLEAN] 完成，总删除条数={total_deleted}")
    # 汇总输出
    for cname, stats in per_collection_stats.items():
        print(f"[CLEAN] 统计 {cname}: deleted={stats['deleted']}")
