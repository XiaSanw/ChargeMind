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
    "<30kW": "低速桩",
    "30-120kW": "中速桩",
    "120-360kW": "快充桩",
    "≥360kW": "超充桩",
}


def _normalize_distribution(values: List[float]) -> List[float]:
    """归一化到概率分布（和为 1）"""
    total = sum(values)
    if total == 0:
        return [0.0] * len(values)
    return [v / total for v in values]


def analyze_power_mismatch(station: dict) -> dict:
    """
    分析场站功率供给与周边需求的错配程度。
    
    输入：场站完整数据（stations_with_grid.jsonl 中的一行）
    输出：功率错配分析结果，含 TVD 分数、供需对比、电池容量解释层
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
    # 结构性错配：某高档供给过剩 + 某低档供给不足
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
    
    # ── 8. 生成建议文案 ──
    recommendations = []
    
    if dominant_mismatch:
        dr = dominant_mismatch["power_range"]
        label = dominant_mismatch["label"]
        gap = dominant_mismatch["gap_pct"]
        if dominant_mismatch["direction"] == "过剩":
            recommendations.append(
                f"{label}（{dr}）供给过剩 {gap}%，"
                f"可考虑将部分 {label} 改造为更贴近需求的功率档"
            )
        elif dominant_mismatch["direction"] == "不足":
            recommendations.append(
                f"{label}（{dr}）供给不足 {abs(gap)}%，"
                f"周边需求集中但桩数不够，建议增补"
            )
    
    # 结合电池容量给出精准功率建议
    if "weighted_avg_kwh" in battery_context:
        avg_kwh = battery_context["weighted_avg_kwh"]
        dominant_range = battery_context.get("dominant_range", "")
        suggestion = battery_context.get("power_suggestion", "")
        recommendations.append(
            f"周边车辆主流电池 {dominant_range}kWh（加权平均 {avg_kwh}kWh），"
            f"{suggestion}"
        )
    
    # 总装机功率 vs 需求功率中位数对比
    total_installed = station.get("total_installed_power", 0)
    avg_charge_power = gp.get("avg_charging_power_kw", 0)
    if total_installed and avg_charge_power:
        power_ratio = total_installed / max(avg_charge_power, 1)
        if power_ratio > 3:
            recommendations.append(
                f"总装机功率 {total_installed}kW 是周边平均充电功率 {avg_charge_power:.0f}kW 的 {power_ratio:.1f} 倍，"
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
        "note": "TVD 基于桩数供给分布与 grid 需求分布计算。桩数为实测硬数据，需求分布为 grid 级聚合观测值。",
        
        "supply_vs_demand": range_comparisons,
        "dominant_mismatch": dominant_mismatch,
        "battery_context": battery_context,
        "recommendation": recommendation_text,
        
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
