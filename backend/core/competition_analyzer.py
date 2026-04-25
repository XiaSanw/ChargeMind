"""
竞争定位分析模块 — 硬数据硬算，基于同 grid 竞品对标

核心指标：
1. 容量份额 vs 实际份额（⭐⭐⭐ 硬算）
2. 竞争基准价 + 价差（⭐⭐⭐ 硬算）
3. 均衡利用率区间（⭐⭐ 弹性假设推演）

设计原则：
- 分组单元：grid_code（同 grid 共享车流池），Haversine 为补充
- 价格加权：按桩数加权（不是距离倒数加权）
- base_util：基于容量份额理论值（不碰实际利用率，数据质量差）
- 所有推演指标必须带 note 说明假设来源
- 零 nash 命名
"""

from typing import Dict, List, Optional, Tuple
import math


def haversine_distance(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Haversine 距离计算（km），纯 math，无外部依赖"""
    R = 6371.0
    lat1_r, lng1_r = math.radians(lat1), math.radians(lng1)
    lat2_r, lng2_r = math.radians(lat2), math.radians(lng2)
    dlat, dlng = lat2_r - lat1_r, lng2_r - lng1_r
    a = math.sin(dlat / 2) ** 2 + math.cos(lat1_r) * math.cos(lat2_r) * math.sin(dlng / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def _total_piles(station: dict) -> int:
    """场站各功率档桩数总和"""
    return (
        (station.get("le_30kw_count") or 0)
        + (station.get("gt_30_le_120kw_count") or 0)
        + (station.get("gt_120_le_360kw_count") or 0)
        + (station.get("gt_360kw_count") or 0)
    )


def _get_service_fee(station: dict) -> Optional[float]:
    """提取场站服务费均价（元/kWh）"""
    sf = station.get("service_fee_parsed", {})
    if not sf:
        return None
    return sf.get("avg_price")


def _get_daily_car_trips(station: dict) -> Optional[float]:
    """提取场站所在 grid 的日均车流量"""
    gp = station.get("grid_vehicle_profile")
    if not gp:
        return None
    return gp.get("avg_daily_car_trips")


def get_competitors(
    station: dict,
    all_stations: list,
    radius_km: Optional[float] = None,
) -> List[dict]:
    """
    获取竞品场站列表。
    主分析维度：同 grid_code（排除自身）。
    可选补充：Haversine 半径过滤作为辅助筛选。
    """
    sid = station.get("station_id", "")
    grid = station.get("grid_code") or ""  # None → ""

    competitors = []
    if not grid:
        return competitors  # 无 grid_code 的场站无法做同 grid 竞品对标

    for s in all_stations:
        if s.get("station_id") == sid:
            continue
        if (s.get("grid_code") or "") != grid:
            continue
        if radius_km is not None:
            dist = haversine_distance(
                station.get("station_lat", 0),
                station.get("station_lng", 0),
                s.get("station_lat", 0),
                s.get("station_lng", 0),
            )
            if dist > radius_km:
                continue
        competitors.append(s)

    return competitors


def analyze_competition(station: dict, all_stations: list) -> dict:
    """
    对单一场站做竞争定位分析。

    Args:
        station: 当前场站完整数据
        all_stations: 竞品场站列表（已由调用方按 grid_code 筛选）

    Returns:
        竞争定位分析结果，含容量份额、竞争基准价、均衡利用率区间
    """
    sid = station.get("station_id", "?")
    sname = station.get("station_name", "?")
    grid = station.get("grid_code") or None  # None → None, not "None"
    my_piles = _total_piles(station)
    my_price = _get_service_fee(station)
    my_trips = _get_daily_car_trips(station)

    competitors = [s for s in all_stations if s.get("station_id") != sid]

    # ═══ 1. 容量份额 vs 实际份额（⭐⭐⭐） ═══
    capacity_result = _analyze_capacity_vs_actual(
        station, competitors, my_piles, my_trips
    )

    # ═══ 2. 竞争基准价（⭐⭐⭐） ═══
    price_result = _analyze_benchmark_price(station, competitors, my_price)

    # ═══ 3. 均衡利用率区间（⭐⭐ 推演） ═══
    eq_result = _analyze_equilibrium(
        capacity_result, price_result, station, competitors
    )

    # ═══ 4. 摘要 ═══
    summary = _build_summary(
        station=sname,
        grid=grid,
        competitor_count=len(competitors),
        capacity_result=capacity_result,
        price_result=price_result,
    )

    return {
        "station_id": sid,
        "station_name": sname,
        "grid_code": grid,
        "competitor_count": len(competitors),
        "competitive_position": {
            "title": "竞争定位分析",
            "capacity_vs_actual": capacity_result,
            "competitive_benchmark_price": price_result,
            "equilibrium_utilization": eq_result,
            "summary": summary,
        },
    }


# ═══════════════════════════════════════════════════════
#  指标 1：容量份额 vs 实际份额
# ═══════════════════════════════════════════════════════

def _analyze_capacity_vs_actual(
    station: dict,
    competitors: List[dict],
    my_piles: int,
    my_trips: Optional[float],
) -> dict:
    grid_total_piles = my_piles + sum(_total_piles(s) for s in competitors)

    if grid_total_piles == 0:
        return {
            "error": "同 grid 总桩数为 0",
            "confidence": "N/A",
        }

    capacity_share_pct = round(my_piles / grid_total_piles * 100, 1)

    # 实际份额
    actual_share_pct = None
    share_gap_pct = None
    interpretation = None

    if my_trips is not None:
        grid_total_trips = my_trips + sum(
            _get_daily_car_trips(s) or 0 for s in competitors
        )
        if grid_total_trips > 0:
            actual_share_pct = round(my_trips / grid_total_trips * 100, 1)
            gap = actual_share_pct - capacity_share_pct
            share_gap_pct = round(gap, 1)
            if gap > 5:
                interpretation = "超额吸引"
            elif gap < -5:
                interpretation = "份额流失"
            else:
                interpretation = "基本匹配"

    return {
        "capacity_share_pct": capacity_share_pct,
        "actual_share_pct": actual_share_pct,
        "share_gap_pct": share_gap_pct,
        "interpretation": interpretation,
        "confidence": "⭐⭐⭐",
        "note": "容量份额 = 本场站桩数 / 同区域总桩数。实际份额 = 本场站日均车流量 / 同区域总车流量。"
        + ("本场站无区域车流数据，实际份额不可用。" if my_trips is None else ""),
    }


# ═══════════════════════════════════════════════════════
#  指标 2：竞争基准价
# ═══════════════════════════════════════════════════════

def _analyze_benchmark_price(
    station: dict,
    competitors: List[dict],
    my_price: Optional[float],
) -> dict:
    # 算竞品桩数加权均价
    weighted_sum = 0.0
    total_weight = 0.0
    priced_competitors = 0

    for s in competitors:
        fee = _get_service_fee(s)
        piles = _total_piles(s)
        if fee is not None and piles > 0:
            weighted_sum += fee * piles
            total_weight += piles
            priced_competitors += 1

    if my_price is None:
        return {
            "benchmark_price": round(weighted_sum / total_weight, 4) if total_weight > 0 else None,
            "my_price": None,
            "price_gap_yuan": None,
            "price_gap_pct": None,
            "confidence": "⭐⭐⭐",
            "note": "本场站无服务费数据。基准价基于同区域竞品真实服务费按桩数加权。",
        }

    if total_weight == 0:
        return {
            "benchmark_price": None,
            "my_price": round(my_price, 4),
            "price_gap_yuan": None,
            "price_gap_pct": None,
            "confidence": "⭐⭐",
            "note": "同区域竞品无有效价格数据，无法计算基准价。",
        }

    benchmark = weighted_sum / total_weight
    gap_yuan = round(my_price - benchmark, 4)
    gap_pct = round(gap_yuan / benchmark * 100, 1)

    return {
        "benchmark_price": round(benchmark, 4),
        "my_price": round(my_price, 4),
        "price_gap_yuan": gap_yuan,
        "price_gap_pct": gap_pct,
        "confidence": "⭐⭐⭐",
        "note": f"基于同区域 {priced_competitors} 个竞品的真实服务费按桩数加权平均，非纳什均衡解。",
    }


# ═══════════════════════════════════════════════════════
#  指标 3：均衡利用率区间（弹性假设推演）
# ═══════════════════════════════════════════════════════

def _analyze_equilibrium(
    capacity_result: dict,
    price_result: dict,
    station: dict,
    competitors: List[dict],
) -> dict:
    """
    均衡利用率区间推演。
    公式：util = base_util × (1 + ε × (benchmark - my) / benchmark)

    base_util 基于容量份额理论值，不用实际利用率（数据质量差）。
    """
    capacity_share = capacity_result.get("capacity_share_pct")
    if capacity_share is None:
        return {
            "error": "无法计算均衡利用率（缺少容量份额）",
            "confidence": "N/A",
        }

    benchmark = price_result.get("benchmark_price")
    my_price = price_result.get("my_price")

    # base_util：容量份额 × 行业理论利用率上限
    # 逻辑：容量份额决定市场份额潜力，但实际利用率受行业供给过剩限制
    # 深圳充电桩供给严重过剩，理论利用率上限约 10%（中位数 3% 的 3 倍）
    THEORETICAL_UTIL_CAP = 0.10
    base_util = (capacity_share / 100.0) * THEORETICAL_UTIL_CAP
    base_util_source = (
        f"基于本场站在同区域容量占比 {capacity_share}% × "
        f"行业理论利用率上限 {THEORETICAL_UTIL_CAP*100:.0f}% = {base_util*100:.2f}%"
    )

    if benchmark is None or my_price is None or benchmark == 0:
        return {
            "low": None,
            "high": None,
            "base_util_source": base_util_source,
            "confidence": "⭐⭐",
            "note": "缺少基准价或本场站价格数据，无法做弹性区间推演。base_util 基于容量份额推演而非实际利用率（实际利用率数据质量差）。",
        }

    price_diff_ratio = (benchmark - my_price) / benchmark  # 正=本场站低于基准

    low_elasticity = 1.5
    high_elasticity = 2.5

    util_low = base_util * (1 + low_elasticity * price_diff_ratio)
    util_high = base_util * (1 + high_elasticity * price_diff_ratio)

    # 利用率不应为负或超过 100%
    util_low = max(0.0, min(1.0, util_low))
    util_high = max(0.0, min(1.0, util_high))

    # 确保 low < high
    if util_low > util_high:
        util_low, util_high = util_high, util_low

    return {
        "low": round(util_low, 4),
        "high": round(util_high, 4),
        "base_util": round(base_util, 4),
        "base_util_source": base_util_source,
        "elasticity_range": [low_elasticity, high_elasticity],
        "confidence": "⭐⭐",
        "note": (
            f"基于行业平均价格弹性 {low_elasticity}-{high_elasticity} 的窄区间推演（波动控制 2 倍以内）。"
            f"base_util={base_util:.4f} = 容量份额 {capacity_share:.1f}% × 行业利用率上限 {THEORETICAL_UTIL_CAP*100:.0f}%。"
            f"{THEORETICAL_UTIL_CAP*100:.0f}% 上限基于深圳充电桩严重供给过剩，"
            f"理论利用率天花板约 3 倍中位数（3% × 3 ≈ 10%）。"
            "本区间非精确预测，仅供方向性参考。"
        ),
    }


# ═══════════════════════════════════════════════════════
#  摘要
# ═══════════════════════════════════════════════════════

def _build_summary(
    station: str,
    grid: str,
    competitor_count: int,
    capacity_result: dict,
    price_result: dict,
) -> str:
    if grid:
        parts = [f"「{station}」所在区域附近的 {competitor_count} 个竞品中"]
    else:
        parts = [f"「{station}」无区域数据，暂无同区域竞品可对标"]

    # 价格位置
    my_price = price_result.get("my_price")
    bench = price_result.get("benchmark_price")
    gap_pct = price_result.get("price_gap_pct")
    if my_price is not None and bench is not None and gap_pct is not None:
        if gap_pct > 10:
            parts.append(f"定价偏高（+{gap_pct}%），服务费 ¥{my_price}/度 vs 基准 ¥{bench}/度")
        elif gap_pct < -10:
            parts.append(f"定价偏低（{gap_pct}%），服务费 ¥{my_price}/度 vs 基准 ¥{bench}/度")
        else:
            parts.append(f"定价居中（{gap_pct:+.1f}%），服务费 ¥{my_price}/度 vs 基准 ¥{bench}/度")

    # 份额错配
    interpretation = capacity_result.get("interpretation")
    capacity_share = capacity_result.get("capacity_share_pct")
    actual_share = capacity_result.get("actual_share_pct")
    if interpretation == "超额吸引":
        parts.append(f"容量份额 {capacity_share}% 但车流份额 {actual_share}%，存在超额吸引")
    elif interpretation == "份额流失":
        parts.append(f"容量份额 {capacity_share}% 但车流仅占 {actual_share}%，份额在流失")
    elif interpretation == "基本匹配":
        parts.append(f"容量份额 {capacity_share}% 与车流份额 {actual_share}% 基本匹配")

    return "；".join(parts) + "。"


# ═══════════════════════════════════════════════════════
#  批量分析
# ═══════════════════════════════════════════════════════

def analyze_all_stations(all_stations: List[dict], sample: int = 0) -> List[dict]:
    """
    批量分析所有场站。
    每条 station 用同 grid 的其他站作为竞品。
    """
    results = []
    stations_to_analyze = all_stations[:sample] if sample > 0 else all_stations
    for s in stations_to_analyze:
        competitors = get_competitors(s, all_stations)
        results.append(analyze_competition(s, competitors))
    return results
