"""
功率错配分析模块 — Total Variation Distance (TVD)

核心逻辑：
- 供给分布 P：基于场站桩数的功率档位分布
- 需求分布 Q：基于 grid_vehicle_profile.power_level_mix 的功率需求分布
- TVD = 0.5 * Σ|P_i - Q_i|，范围 [0, 1]

与电池容量分析互补：
- TVD 回答"多错"（量化错配程度）
- 电池容量回答"为什么错"（解释层）
"""

from typing import Dict, List, Optional
from collections import defaultdict

from core.brand_analyzer import extract_battery_capacity

# ── 功率档映射 ──
# grid power_level_mix key → 桩数字段名
POWER_KEY_TO_PILE_FIELD = {
    "<30kW": "le_30kw_count",
    "30-120kW": "gt_30_le_120kw_count",
    "120-360kW": "gt_120_le_360kw_count",
    "≥360kW": "gt_360kw_count",
}

# 功率档展示顺序（从低到高）
POWER_RANGES_ORDER = ["<30kW", "30-120kW", "120-360kW", "≥360kW"]

# 功率档建议文案模板
POWER_RANGE_LABELS = {
    "<30kW": "慢充桩",
    "30-120kW": "快充桩",
    "120-360kW": "超充桩",
    "≥360kW": "极充桩",
}

# pile_breakdown key → 展示名称
PILE_BREAKDOWN_LABELS = {
    "slow": "慢充桩",
    "fast": "快充桩",
    "super": "超充桩",
}

# pile_breakdown key → 主要对应功率档（用于建议文案）
PILE_BREAKDOWN_RANGES = {
    "slow": ["<30kW"],
    "fast": ["30-120kW", "120-360kW"],
    "super": ["120-360kW", "≥360kW"],
}


def _normalize_distribution(values: List[float]) -> List[float]:
    """归一化到概率分布（和为 1）"""
    total = sum(values)
    if total == 0:
        return [0.0] * len(values)
    return [v / total for v in values]


def _build_region_supply_profile(grid_stations: List[dict]) -> Dict[str, float]:
    """
    聚合当前区域内所有场站的功率供给分布。
    返回：{"<30kW": 0.35, "30-120kW": 0.40, ...}
    """
    counts = defaultdict(int)
    for s in grid_stations:
        for power_range in POWER_RANGES_ORDER:
            field = POWER_KEY_TO_PILE_FIELD[power_range]
            counts[power_range] += s.get(field, 0) or 0
    total = sum(counts.values())
    if total == 0:
        return {r: 0.0 for r in POWER_RANGES_ORDER}
    return {r: counts[r] / total for r in POWER_RANGES_ORDER}


def _analyze_pile_breakdown(
    pb: dict,
    demand_distribution: List[float],
    region_supply: Dict[str, float],
    range_comparisons: List[dict],
    battery_context: dict,
) -> dict:
    """
    基于用户输入的 pile_breakdown，生成三段式对比分析。
    """
    # ── 第 1 段：区域需求画像 ──
    demand_breakdown = []
    for i, power_range in enumerate(POWER_RANGES_ORDER):
        pct = demand_distribution[i] * 100
        demand_breakdown.append({
            "power_range": power_range,
            "label": POWER_RANGE_LABELS[power_range],
            "demand_pct": round(pct, 1),
        })

    dominant_demand = max(demand_breakdown, key=lambda x: x["demand_pct"])

    region_demand_text = (
        f"通过数据分析，当前区域下周边车辆的充电功率需求呈"
        f"「{dominant_demand['label']}为主」格局（占比 {dominant_demand['demand_pct']:.1f}%）。"
    )

    if battery_context and "error" not in battery_context:
        avg_kwh = battery_context.get("weighted_avg_kwh")
        dom_range = battery_context.get("dominant_range", "")
        dom_pct = battery_context.get("dominant_pct", 0)
        if avg_kwh:
            region_demand_text += (
                f"主流电池容量 {dom_range}kWh（占 {dom_pct:.1f}%），"
                f"加权平均 {avg_kwh:.1f}kWh，对应充电功率约 {avg_kwh * 0.5:.0f}-{avg_kwh * 1.5:.0f}kW。"
            )

    # ── 第 2 段：区域供给现状 ──
    if region_supply:
        region_supply_lines = []
        for r in POWER_RANGES_ORDER:
            label = POWER_RANGE_LABELS[r]
            pct = region_supply.get(r, 0) * 100
            region_supply_lines.append(f"{label} {pct:.1f}%")
        region_supply_text = (
            f"当前区域内充电桩功率分布：{' / '.join(region_supply_lines)}。"
        )
        # 判断区域整体结构
        high_power_pct = region_supply.get("≥360kW", 0) + region_supply.get("120-360kW", 0)
        if high_power_pct < 0.15:
            region_supply_text += "高功率桩（超充+极充）供给偏保守。"
        elif high_power_pct > 0.35:
            region_supply_text += "高功率桩占比较高，可能存在同质化竞争。"
        else:
            region_supply_text += "功率结构相对均衡。"
    else:
        region_supply_text = "当前区域供给数据不足，无法判断整体结构。"

    # ── 第 3 段：用户场站对比分析 ──
    # 计算用户总桩数
    total_pb_piles = sum((pb.get(k, 0) or 0) for k in ["slow", "fast", "super"])

    station_items = []
    for pb_key in ["slow", "fast", "super"]:
        count = pb.get(pb_key, 0)
        if count is None:
            count = 0
        label = PILE_BREAKDOWN_LABELS[pb_key]
        mapped_ranges = PILE_BREAKDOWN_RANGES[pb_key]

        # 计算该类型桩覆盖的所有档位的总需求占比
        total_demand_pct = 0.0
        covered_labels = []
        for r in mapped_ranges:
            idx = POWER_RANGES_ORDER.index(r)
            pct = demand_distribution[idx] * 100
            total_demand_pct += pct
            covered_labels.append(POWER_RANGE_LABELS[r])

        # 计算用户该类型桩的供给占比
        supply_pct = (count / total_pb_piles * 100) if total_pb_piles > 0 else 0.0

        # 供需差值（供给 - 需求）
        gap = supply_pct - total_demand_pct

        if count == 0:
            if total_demand_pct > 15:
                judgment = "❌ 缺失"
                reason = f"当前区域 {'/'.join(covered_labels)} 合计需求占比 {total_demand_pct:.1f}%，您场站该类型为零"
            else:
                judgment = "—"
                reason = f"当前区域 {'/'.join(covered_labels)} 合计需求占比 {total_demand_pct:.1f}%，无需配置"
        elif gap > 20:
            judgment = "⚠️ 过剩风险"
            reason = f"您场站该类型占比 {supply_pct:.1f}%（{count} 台），高于区域需求 {total_demand_pct:.1f}%，存在闲置风险"
        elif gap < -20:
            judgment = "❌ 供给不足"
            reason = f"您场站该类型占比 {supply_pct:.1f}%（{count} 台），低于区域需求 {total_demand_pct:.1f}%，建议增补"
        else:
            judgment = "✓ 基本匹配"
            reason = f"您场站该类型占比 {supply_pct:.1f}%（{count} 台），与区域需求 {total_demand_pct:.1f}% 基本匹配"

        station_items.append({
            "label": label,
            "count": count,
            "supply_pct": round(supply_pct, 1),
            "demand_pct": round(total_demand_pct, 1),
            "judgment": judgment,
            "reason": reason,
        })

    return {
        "region_demand_text": region_demand_text,
        "region_supply_text": region_supply_text,
        "station_items": station_items,
    }


def analyze_power_mismatch(station: dict, profile: dict = None, grid_stations: List[dict] = None) -> dict:
    """
    分析场站功率供给与周边需求的错配程度。

    输入：
        station: 场站完整数据
        profile: 用户输入的画像（含 pile_breakdown）
        grid_stations: 同区域（grid）内所有场站列表
    输出：功率错配分析结果
    """
    gp = station.get("grid_vehicle_profile")
    if not gp:
        return {
            "error": "无 grid_vehicle_profile 数据，无法分析功率错配",
            "confidence": "N/A",
        }

    # ── 1. 提取供给分布 P（基于桩数）──
    supply_counts = []
    supply_breakdown = []
    for power_range in POWER_RANGES_ORDER:
        pile_field = POWER_KEY_TO_PILE_FIELD[power_range]
        count = station.get(pile_field, 0) or 0
        supply_counts.append(float(count))
        supply_breakdown.append({
            "power_range": power_range,
            "label": POWER_RANGE_LABELS[power_range],
            "pile_count": count,
        })

    total_piles = sum(supply_counts)
    if total_piles == 0:
        return {
            "error": "场站桩数全部为 0，无法分析功率错配",
            "confidence": "N/A",
        }

    P = _normalize_distribution(supply_counts)

    # ── 2. 提取需求分布 Q（基于 grid power_level_mix）──
    plm = gp.get("power_level_mix", {})
    demand_values = []
    demand_breakdown = []
    for power_range in POWER_RANGES_ORDER:
        demand_pct = plm.get(power_range, 0.0)
        demand_values.append(demand_pct)
        demand_breakdown.append({
            "power_range": power_range,
            "label": POWER_RANGE_LABELS[power_range],
            "demand_pct": round(demand_pct * 100, 1),
        })

    Q = _normalize_distribution(demand_values)

    # ── 3. 计算 TVD ──
    tvd = 0.5 * sum(abs(p - q) for p, q in zip(P, Q))

    # ── 4. 逐档对比，找最大错配 ──
    range_comparisons = []
    max_gap = 0.0
    dominant_mismatch = None

    for i, power_range in enumerate(POWER_RANGES_ORDER):
        supply_pct = P[i] * 100
        demand_pct = Q[i] * 100
        gap = supply_pct - demand_pct  # 正=供给过剩，负=供给不足

        comparison = {
            "power_range": power_range,
            "label": POWER_RANGE_LABELS[power_range],
            "supply_pct": round(supply_pct, 1),
            "demand_pct": round(demand_pct, 1),
            "gap_pct": round(gap, 1),
            "direction": "过剩" if gap > 10 else ("不足" if gap < -10 else "基本匹配"),
        }
        range_comparisons.append(comparison)

        if abs(gap) > max_gap:
            max_gap = abs(gap)
            dominant_mismatch = comparison

    # ── 5. 错配方向判断 ──
    oversupply_ranges = [r for r in range_comparisons if r["direction"] == "过剩"]
    undersupply_ranges = [r for r in range_comparisons if r["direction"] == "不足"]

    if oversupply_ranges and undersupply_ranges:
        mismatch_direction = "结构性错配"
    elif oversupply_ranges:
        mismatch_direction = "供给过剩"
    elif undersupply_ranges:
        mismatch_direction = "供给不足"
    else:
        mismatch_direction = "基本匹配"

    # ── 6. TVD 等级 ──
    if tvd <= 0.15:
        tvd_level = "高度匹配"
        tvd_description = "供给与需求功率分布基本一致"
    elif tvd <= 0.35:
        tvd_level = "轻度错配"
        tvd_description = "存在局部功率档偏差，建议微调"
    elif tvd <= 0.55:
        tvd_level = "中度错配"
        tvd_description = "功率结构明显不合理，需针对性改造"
    else:
        tvd_level = "严重错配"
        tvd_description = "功率供给与需求严重背离，建议重新评估硬件配置"

    # ── 7. 电池容量解释层 ──
    vtp = gp.get("vehicle_tag_global_profile", {})
    battery_context = extract_battery_capacity(vtp) if vtp else {"error": "无标签数据"}

    # ── 8. 区域供给画像（聚合同区域所有场站）──
    region_supply = _build_region_supply_profile(grid_stations or []) if grid_stations else {}

    # ── 9. 用户 pile_breakdown 对比分析 ──
    pile_breakdown_analysis = None
    if profile and profile.get("pile_breakdown"):
        pile_breakdown_analysis = _analyze_pile_breakdown(
            profile["pile_breakdown"], Q, region_supply, range_comparisons, battery_context
        )

    # ── 10. 生成建议文案（加区域限定前缀）──
    recommendations = []

    if dominant_mismatch:
        dr = dominant_mismatch["power_range"]
        label = dominant_mismatch["label"]
        gap = dominant_mismatch["gap_pct"]
        if dominant_mismatch["direction"] == "过剩":
            recommendations.append(
                f"在当前区域下，{label}（{dr}）供给过剩 {gap}%，"
                f"可考虑将部分 {label} 改造为更贴近需求的功率档"
            )
        elif dominant_mismatch["direction"] == "不足":
            recommendations.append(
                f"在当前区域下，{label}（{dr}）供给不足 {abs(gap)}%，"
                f"周边需求集中但桩数不够，建议增补"
            )

    # 结合电池容量给出精准功率建议
    if "weighted_avg_kwh" in battery_context:
        avg_kwh = battery_context["weighted_avg_kwh"]
        dominant_range = battery_context.get("dominant_range", "")
        suggestion = battery_context.get("power_suggestion", "")
        recommendations.append(
            f"当前区域周边车辆主流电池 {dominant_range}kWh（加权平均 {avg_kwh}kWh），"
            f"{suggestion}"
        )

    # 总装机功率 vs 需求功率中位数对比
    total_installed = station.get("total_installed_power", 0)
    avg_charge_power = gp.get("avg_charging_power_kw", 0)
    if total_installed and avg_charge_power:
        power_ratio = total_installed / max(avg_charge_power, 1)
        if power_ratio > 3:
            recommendations.append(
                f"总装机功率 {total_installed}kW 是当前区域平均充电功率 {avg_charge_power:.0f}kW 的 {power_ratio:.1f} 倍，"
                f'存在明显的"大炮打蚊子"风险'
            )

    recommendation_text = "；".join(recommendations) if recommendations else "功率配置与周边需求基本匹配"

    return {
        "title": "功率错配分析",
        "tvd_score": round(tvd, 3),
        "tvd_level": tvd_level,
        "tvd_description": tvd_description,
        "mismatch_direction": mismatch_direction,
        "confidence": "⭐⭐⭐",
        "note": "TVD 基于桩数供给分布与区域需求分布计算。桩数为实测硬数据，需求分布为区域级聚合观测值。",

        "supply_vs_demand": range_comparisons,
        "dominant_mismatch": dominant_mismatch,
        "battery_context": battery_context,
        "recommendation": recommendation_text,

        # 新增：区域供给画像 + 用户场站对比
        "region_supply": region_supply,
        "pile_breakdown_analysis": pile_breakdown_analysis,

        # 原始数据（供前端图表渲染）
        "raw": {
            "supply_distribution": {r["power_range"]: r["supply_pct"] for r in range_comparisons},
            "demand_distribution": {r["power_range"]: r["demand_pct"] for r in range_comparisons},
            "total_piles": total_piles,
            "total_installed_power_kw": total_installed,
            "avg_charging_power_kw": round(avg_charge_power, 1) if avg_charge_power else None,
        },
    }


def analyze_power_mismatch_batch(stations: List[dict]) -> List[dict]:
    """批量分析多个场站的功率错配"""
    return [analyze_power_mismatch(s) for s in stations]
