"""
竞品价格对标模块（简化版）— min/avg/max 三档对比

与 #3 竞争定位分析的区别：
- #3：全天均价对比（competitive_benchmark_price），用于竞争定位推演
- #8：min/avg/max 三档对比，展示价格结构差异（峰谷价差 vs 竞品峰谷价差）

设计原则：
- 不做时段对齐（不同运营商 periods 划分不一致，对齐复杂且易错）
- 价格 = electricity_fee + service_fee（总价格，用户实际支付）
- 竞品基准：同 grid_code 按桩数加权
- 所有价格单位：元/kWh
"""

from typing import Dict, List, Optional

from core.competition_analyzer import get_competitors, _total_piles


# ── 模块级辅助函数（可被外部复用）──

def _sum_prices(a: Optional[float], b: Optional[float]) -> Optional[float]:
    """合并两个价格字段，缺失项视为 0，全缺失则返回 None"""
    if a is None and b is None:
        return None
    return (a or 0) + (b or 0)


def _weighted_avg(values: List[float], weights: List[float]) -> Optional[float]:
    """加权平均。空列表返回 None"""
    if not values:
        return None
    return sum(values) / sum(weights)


def compute_spread_ratio(price_dict: Optional[dict]) -> Optional[float]:
    """
    计算峰谷比 = max / min。
    可用于本场站或竞品基准价。
    """
    if price_dict is None:
        return None
    pmin = price_dict.get("min")
    pmax = price_dict.get("max")
    if pmin is not None and pmax is not None and pmin > 0:
        return round(pmax / pmin, 2)
    return None


# ── 核心函数 ──

def _get_total_price(station: dict) -> Optional[dict]:
    """
    提取场站总价格（电费 + 服务费）的 min/avg/max。
    
    返回：{"min": float, "avg": float, "max": float} 或 None
    """
    elec = station.get("electricity_fee_parsed") or {}
    service = station.get("service_fee_parsed") or {}
    
    if not elec and not service:
        return None
    
    # electricity_fee 可能缺失（部分场站只有 service_fee）
    e_min = elec.get("min_price")
    e_avg = elec.get("avg_price")
    e_max = elec.get("max_price")
    
    s_min = service.get("min_price")
    s_avg = service.get("avg_price")
    s_max = service.get("max_price")
    
    total_min = _sum_prices(e_min, s_min)
    total_avg = _sum_prices(e_avg, s_avg)
    total_max = _sum_prices(e_max, s_max)
    
    if total_min is None and total_avg is None and total_max is None:
        return None
    
    return {
        "min": round(total_min, 4) if total_min is not None else None,
        "avg": round(total_avg, 4) if total_avg is not None else None,
        "max": round(total_max, 4) if total_max is not None else None,
    }


def _compute_benchmark_prices(competitors: List[dict]) -> Optional[dict]:
    """
    计算竞品 min/avg/max 的桩数加权基准价。
    
    每个档位独立加权：只取该档位有数据的竞品参与加权。
    """
    min_values, min_weights = [], []
    avg_values, avg_weights = [], []
    max_values, max_weights = [], []
    
    priced_count = 0
    
    for s in competitors:
        price = _get_total_price(s)
        if price is None:
            continue
        
        piles = _total_piles(s)
        if piles <= 0:
            piles = 1  # 兜底，避免除零
        
        priced_count += 1
        
        if price.get("min") is not None:
            min_values.append(price["min"] * piles)
            min_weights.append(piles)
        if price.get("avg") is not None:
            avg_values.append(price["avg"] * piles)
            avg_weights.append(piles)
        if price.get("max") is not None:
            max_values.append(price["max"] * piles)
            max_weights.append(piles)
    
    if priced_count == 0:
        return None
    
    return {
        "min": round(_weighted_avg(min_values, min_weights), 4) if min_values else None,
        "avg": round(_weighted_avg(avg_values, avg_weights), 4) if avg_values else None,
        "max": round(_weighted_avg(max_values, max_weights), 4) if max_values else None,
        "priced_competitor_count": priced_count,
    }


def analyze_price_benchmark(station: dict, all_stations: list) -> dict:
    """
    对单一场站做竞品价格对标（简化版 min/avg/max）。
    
    Args:
        station: 当前场站完整数据
        all_stations: 全量场站列表（用于筛选同 grid 竞品）
    
    Returns:
        {
            "station_id": str,
            "station_name": str,
            "grid_code": str,
            "competitor_count": int,
            "price_benchmark": {
                "title": "竞品价格对标",
                "my_prices": {"min": float|null, "avg": float|null, "max": float|null},
                "benchmark_prices": {"min": float|null, "avg": float|null, "max": float|null},
                "gaps": {"min_gap_pct": float|null, "avg_gap_pct": float|null, "max_gap_pct": float|null},
                "spread_ratio": float|null,  # 峰谷比 = max/min
                "benchmark_spread_ratio": float|null,
                "confidence": "⭐⭐⭐",
                "note": str,
            }
        }
    """
    sid = station.get("station_id", "?")
    sname = station.get("station_name", "?")
    grid = station.get("grid_code") or None
    
    # 获取竞品（同 grid，排除自身）
    competitors = get_competitors(station, all_stations)
    
    # 本场站价格
    my_price = _get_total_price(station)
    
    # 竞品基准价
    benchmark = _compute_benchmark_prices(competitors)
    
    # 计算价差（百分比）
    gaps = {}
    for key in ["min", "avg", "max"]:
        my_val = my_price.get(key) if my_price else None
        bench_val = benchmark.get(key) if benchmark else None
        if my_val is not None and bench_val is not None and bench_val != 0:
            gap_pct = round((my_val - bench_val) / bench_val * 100, 1)
            gaps[f"{key}_gap_pct"] = gap_pct
        else:
            gaps[f"{key}_gap_pct"] = None
    
    spread = compute_spread_ratio(my_price)
    bench_spread = compute_spread_ratio(benchmark)
    
    # 构建 note
    note_parts = []
    if my_price is None:
        note_parts.append("本场站无价格数据（电费/服务费均缺失）。")
    if benchmark is None:
        note_parts.append("同 grid 竞品无有效价格数据。")
    if my_price and benchmark:
        note_parts.append(
            f"基于同 grid {len(competitors)} 个竞品中 "
            f"{benchmark.get('priced_competitor_count', 0)} 个有价格数据的场站，"
            f"按桩数加权计算 min/avg/max 基准价。"
        )
    
    return {
        "station_id": sid,
        "station_name": sname,
        "grid_code": grid,
        "competitor_count": len(competitors),
        "price_benchmark": {
            "title": "竞品价格对标",
            "my_prices": my_price or {"min": None, "avg": None, "max": None},
            "benchmark_prices": {
                "min": benchmark.get("min") if benchmark else None,
                "avg": benchmark.get("avg") if benchmark else None,
                "max": benchmark.get("max") if benchmark else None,
            },
            "gaps": gaps,
            "spread_ratio": spread,
            "benchmark_spread_ratio": bench_spread,
            "confidence": "⭐⭐⭐",
            "note": " ".join(note_parts) if note_parts else "",
        },
    }


def analyze_all_price_benchmarks(all_stations: List[dict], sample: int = 0) -> List[dict]:
    """
    批量分析所有场站的价格对标。
    """
    results = []
    stations_to_analyze = all_stations[:sample] if sample > 0 else all_stations
    for s in stations_to_analyze:
        results.append(analyze_price_benchmark(s, all_stations))
    return results
