"""
诊断报告构建器 — 核心集成模块

聚合所有分析模块输出，构建完整的诊断报告 JSON。
报告结构严格对齐 docs/输出界面.md 规范。

数字策略（三层）：
- 诊断层（⭐⭐⭐）：点估计，公式透明
- 推演层（⭐⭐）：窄区间 [6%, 10%]，弹性 1.5-2.5
- 建议层（⭐⭐）：公式透明的数字，不给概率
"""

import json
import math
from typing import Dict, List, Optional
from pathlib import Path

from core.brand_analyzer import (
    extract_battery_capacity,
    extract_brand_matrix,
    extract_seasonal_fluctuation,
    extract_vehicle_profile,
)
from core.power_mismatch import analyze_power_mismatch
from core.price_benchmark import analyze_price_benchmark

# 数据路径
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_PATH = PROJECT_ROOT.parent / "data" / "cleaned" / "stations_with_grid.jsonl"

# 全局缓存（启动时加载）
_all_stations: List[dict] = []

def _load_all_stations() -> List[dict]:
    """加载所有场站数据（带缓存）"""
    global _all_stations
    if _all_stations:
        return _all_stations
    stations = []
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        for line in f:
            stations.append(json.loads(line))
    _all_stations = stations
    return stations


def _find_station_by_profile(profile: dict) -> Optional[dict]:
    """
    根据用户输入的 profile，从 JSONL 中匹配最佳场站。
    匹配优先级：region + business_type > region only > 第一个
    """
    stations = _load_all_stations()
    region = profile.get("region", "")
    biz_types = set(profile.get("business_type", []) or [])

    # 精确匹配：region + business_type
    for s in stations:
        s_region = s.get("region", "")
        s_biz = set(s.get("business_type", []) or [])
        if region and s_region and region in s_region and biz_types and biz_types & s_biz:
            return s

    # 退阶：仅匹配 region
    if region:
        for s in stations:
            s_region = s.get("region", "")
            if s_region and region in s_region:
                return s

    # 最终退阶：返回第一个（不应该发生）
    return stations[0] if stations else None


def _get_grid_stations(station: dict, all_stations: List[dict]) -> List[dict]:
    """获取同 grid 的所有场站（用于竞争定位分析）"""
    gp = station.get("grid_vehicle_profile") or {} or {}
    grid_code = station.get("grid_code") or gp.get("grid_code")
    if not grid_code:
        return []
    result = []
    for s in all_stations:
        if s.get("grid_code") == grid_code:
            result.append(s)
            continue
        s_gp = s.get("grid_vehicle_profile")
        if s_gp and s_gp.get("grid_code") == grid_code:
            result.append(s)
    return result


# ═══════════════════════════════════════════════════════
#  0. 同区域均值缓存（用于雷达图参考线）
# ═══════════════════════════════════════════════════════

_sector_avg_cache: Dict[str, Dict[str, float]] = {}


def _compute_sector_averages(station: dict, all_stations: List[dict]) -> Dict[str, float]:
    """
    计算同 region 场站的 5 维评分均值（简化版，用于雷达图参考线）。
    使用简化指标避免调用重型分析模块。
    """
    region = station.get("region", "")
    if not region:
        return {}

    cache_key = region
    if cache_key in _sector_avg_cache:
        return _sector_avg_cache[cache_key]

    # 收集同 region 场站
    same_region = [s for s in all_stations if region in (s.get("region", "") or "")]
    if len(same_region) < 2:
        return {}

    def _simple_location(s: dict) -> float:
        gp = s.get("grid_vehicle_profile") or {}
        if not gp:
            return 50
        cars = gp.get("avg_daily_car_trips", 0)
        if cars > 5000:
            return 75
        elif cars > 2000:
            return 60
        return 45

    def _simple_hardware(s: dict) -> float:
        piles = (s.get("le_30kw_count", 0) + s.get("gt_30_le_120kw_count", 0) +
                 s.get("gt_120_le_360kw_count", 0) + s.get("gt_360kw_count", 0))
        power = s.get("total_installed_power", 0)
        if piles == 0 or power == 0:
            return 50
        avg_power = power / piles
        # 极端功率（>360kW 平均）认为错配严重
        if avg_power > 300:
            return 30
        elif avg_power > 120:
            return 55
        else:
            return 70

    def _simple_operation(s: dict) -> float:
        power = s.get("total_installed_power", 0)
        piles = (s.get("le_30kw_count", 0) + s.get("gt_30_le_120kw_count", 0) +
                 s.get("gt_120_le_360kw_count", 0) + s.get("gt_360kw_count", 0))
        if power == 0 or piles == 0:
            return 40
        avg_power = power / piles
        base = 60 if 30 <= avg_power <= 120 else (40 if avg_power < 30 else 35)
        gp = s.get("grid_vehicle_profile")
        if gp:
            cars = gp.get("avg_daily_car_trips", 0)
            if cars > 5000:
                base += 15
            elif cars > 2000:
                base += 8
        return min(100, base)

    def _simple_saturation(s: dict) -> float:
        gp = s.get("grid_vehicle_profile")
        cars = gp.get("avg_daily_car_trips", 0) if gp else 0
        power = s.get("total_installed_power", 0)
        if power == 0:
            return 50
        ratio = cars / power
        if ratio > 1.0:
            return 85
        elif ratio > 0.5:
            return 70
        elif ratio > 0.2:
            return 55
        return 40

    n = len(same_region)
    avg = {
        "地段禀赋": sum(_simple_location(s) for s in same_region) / n,
        "硬件适配": sum(_simple_hardware(s) for s in same_region) / n,
        "定价精准": 50,  # 简化：区域平均定价取中值
        "运营产出": sum(_simple_operation(s) for s in same_region) / n,
        "需求饱和度": sum(_simple_saturation(s) for s in same_region) / n,
    }

    _sector_avg_cache[cache_key] = avg
    return avg


# ═══════════════════════════════════════════════════════
#  1. 5 维雷达图评分
# ═══════════════════════════════════════════════════════

def _score_location(station: dict) -> int:
    """地段禀赋：0-100"""
    gp = station.get("grid_vehicle_profile") or {}
    if not gp:
        return 50

    # 日均车流量（grid 级，同 grid 内排名）
    cars = gp.get("avg_daily_car_trips", 0)
    # 车型丰富度（vehicle_type_mix 标签数）
    vtm = gp.get("vehicle_type_mix", {})
    type_count = len(vtm)
    # 平均 SOC
    soc = gp.get("avg_soc", 50)
    # 净流入
    mig = gp.get("migration", {})
    net = mig.get("net_migration", 0)

    # 简单评分（满分 100）
    score = 30  # 基础分
    if cars > 5000:
        score += 25
    elif cars > 2000:
        score += 15
    if type_count >= 5:
        score += 15
    elif type_count >= 3:
        score += 10
    if 30 <= soc <= 50:
        score += 15  # SOC 适中说明需求活跃
    if net > 0:
        score += 15

    return min(100, max(0, score))


def _score_hardware(station: dict) -> int:
    """硬件适配：0-100。TVD 越低越好"""
    pm = analyze_power_mismatch(station)
    if "error" in pm:
        return 50
    tvd = pm.get("tvd_score", 0.5)
    # TVD 0 = 完美匹配(100分)，TVD 1 = 完全错配(0分)
    score = int((1 - tvd) * 100)
    return max(0, min(100, score))


def _score_pricing(station: dict, comp_result: dict) -> int:
    """定价精准：0-100。价差越小越好"""
    bench = comp_result.get("competitive_position", {}).get("competitive_benchmark_price", {})
    if not bench:
        return 50
    gap_pct = abs(bench.get("price_gap_pct", 0))
    # 价差 0% = 100分，价差 100% = 0分
    score = int(100 - gap_pct)
    return max(0, min(100, score))


def _score_operation(station: dict) -> int:
    """运营产出：0-100。⚠️ 利用率数据质量差，标⭐"""
    # 由于利用率数据不可靠，用装机功率和桩数做粗略估计
    power = station.get("total_installed_power", 0)
    piles = (station.get("le_30kw_count", 0) + station.get("gt_30_le_120kw_count", 0) +
             station.get("gt_120_le_360kw_count", 0) + station.get("gt_360kw_count", 0))

    if power == 0 or piles == 0:
        return 30

    # 平均单桩功率
    avg_pile_power = power / piles
    # 功率适中（30-120kW）得分高，极端功率得分低
    if 30 <= avg_pile_power <= 120:
        base = 60
    elif avg_pile_power < 30:
        base = 40
    else:
        base = 35  # 超快充利用率通常更低

    # 加上 grid 车流量修正
    gp = station.get("grid_vehicle_profile") or {}
    cars = gp.get("avg_daily_car_trips", 0)
    if cars > 5000:
        base += 20
    elif cars > 2000:
        base += 10

    return min(100, base)


def _score_demand_saturation(station: dict) -> int:
    """需求饱和度：0-100。网格需求 / 场站容量"""
    gp = station.get("grid_vehicle_profile") or {}
    if not gp:
        return 50

    cars = gp.get("avg_daily_car_trips", 0)
    power = station.get("total_installed_power", 0)

    if power == 0:
        return 50

    # 每 kW 装机对应的车流量
    ratio = cars / power
    # 经验阈值：ratio > 1.0 为饱和，< 0.2 为不足
    if ratio > 1.0:
        score = 90
    elif ratio > 0.5:
        score = 75
    elif ratio > 0.2:
        score = 60
    else:
        score = 40

    return score


def _build_radar(station: dict, comp_result: dict, all_stations: List[dict]) -> tuple:
    """构建 5 维雷达图数据，含同区域均值参考线"""
    scores = {
        "地段禀赋": _score_location(station),
        "硬件适配": _score_hardware(station),
        "定价精准": _score_pricing(station, comp_result),
        "运营产出": _score_operation(station),
        "需求饱和度": _score_demand_saturation(station),
    }

    # 同区域均值参考线
    sector_avg = _compute_sector_averages(station, all_stations)

    # 生成一句话评论
    comments = {
        "地段禀赋": "车流密集，一个字：旺" if scores["地段禀赋"] > 70 else "地段一般，车流量有限",
        "硬件适配": "大炮打蚊子，快充供过于求" if scores["硬件适配"] < 40 else "功率配置与需求基本匹配",
        "定价精准": "夹缝求生，两头不讨好" if scores["定价精准"] < 40 else "定价与竞品基本对齐",
        "运营产出": "守着金山要饭" if scores["运营产出"] < 40 else "运营效率正常",
        "需求饱和度": "网格需求充足，你吃不到而已" if scores["需求饱和度"] > 70 and scores["运营产出"] < 50 else "需求与供给基本平衡",
    }

    # 各维度可信度标签
    trust_labels = {
        "地段禀赋": "⭐⭐⭐",
        "硬件适配": "⭐⭐⭐",
        "定价精准": "⭐⭐⭐",
        "运营产出": "⭐",       # 利用率数据质量极差，用装机功率粗略估计
        "需求饱和度": "⭐⭐⭐",
    }

    radar = {}
    for dim, score in scores.items():
        radar[dim] = {
            "score": score,
            "comment": comments[dim],
            "trust": trust_labels[dim],
            "sector_avg": round(sector_avg.get(dim, 50)),
        }

    return radar, scores, sector_avg


def _build_scoring_reasoning(station: dict, scores: dict, pm: dict, comp_result: dict) -> dict:
    """
    用自然语言解释每个雷达维度分数的推导过程。
    """
    gp = station.get("grid_vehicle_profile") or {}
    reasoning = {}

    # 地段禀赋
    cars = gp.get("avg_daily_car_trips", 0) if gp else 0
    net = gp.get("migration", {}).get("net_migration", 0) if gp else 0
    reasoning["地段禀赋"] = (
        f"周边日均车流量 {cars:.0f} 车次，净流入 {net:.0f} 车次/日，"
        f"综合评分 {scores['地段禀赋']} 分。"
        f"{'车流密集，地段价值高。' if scores['地段禀赋'] > 60 else '车流量一般，地段潜力有限。'}"
    )

    # 硬件适配
    tvd = pm.get("tvd_score", 0) if "error" not in pm else 0.5
    reasoning["硬件适配"] = (
        f"功率错配 TVD = {tvd:.2f}（{'严重错配' if tvd > 0.5 else '轻度错配' if tvd > 0.2 else '基本匹配'}），"
        f"供给功率分布与周边需求偏差大，评分 {scores['硬件适配']} 分。"
    )

    # 定价精准
    bench = comp_result.get("competitive_position", {}).get("competitive_benchmark_price", {}) if isinstance(comp_result, dict) else {}
    gap = bench.get("price_gap_pct", 0) if bench else 0
    reasoning["定价精准"] = (
        f"服务费与竞品差距 {gap:+.0f}%，"
        f"{'定价偏离市场基准，需调整。' if abs(gap) > 20 else '定价与竞品基本对齐。'}"
        f"评分 {scores['定价精准']} 分。"
    )

    # 运营产出
    power = station.get("total_installed_power", 0)
    piles = (station.get("le_30kw_count", 0) + station.get("gt_30_le_120kw_count", 0) +
             station.get("gt_120_le_360kw_count", 0) + station.get("gt_360kw_count", 0))
    reasoning["运营产出"] = (
        f"装机功率 {power}kW，{piles} 个桩，"
        f"基于 5% 利用率假设粗略估算。"
        f"评分 {scores['运营产出']} 分（⭐ 估算，数据质量差）。"
    )

    # 需求饱和度
    ratio = cars / power if power > 0 else 0
    reasoning["需求饱和度"] = (
        f"每 kW 装机对应日均车流量 {ratio:.2f}，"
        f"{'需求远超供给，饱和度高。' if ratio > 1.0 else '需求与供给基本平衡。'}"
        f"评分 {scores['需求饱和度']} 分。"
    )

    return reasoning


# ═══════════════════════════════════════════════════════
#  2. 称号系统
# ═══════════════════════════════════════════════════════

def _determine_title(scores: dict, tvd_score: float) -> tuple:
    """
    根据 5 维得分和 TVD 确定称号。
    返回 (title, title_reason)
    """
    loc = scores["地段禀赋"]
    hw = scores["硬件适配"]
    price = scores["定价精准"]
    op = scores["运营产出"]
    sat = scores["需求饱和度"]

    # 优先级判断
    if all(s >= 65 for s in scores.values()):
        return "六边形战士", "五维均衡，无明显短板"

    if loc >= 80 and op <= 40:
        return "含着金钥匙出生", "地段极佳，但运营产出严重不匹配"

    if tvd_score > 0.5 and loc >= 60:
        return "大炮打蚊子", "地段极佳，但硬件与需求严重错配——建了大量超快充桩，周边车根本用不上"

    if hw >= 70 and price <= 40:
        return "夹缝求生", "硬件适配良好，但定价两头不讨好"

    if op <= 30 and sat >= 60:
        return "守着金山要饭", "周边需求充足，但场站完全吃不到流量"

    if tvd_score < 0.2 and op <= 40:
        return "佛系充电站", "功率配置保守，运营躺平，不卷不争"

    if price >= 70 and hw >= 60:
        return "精明定价者", "定价精准，硬件适配，只差地段或引流"

    return "潜力股", "有明显短板，但改善空间较大"


# ═══════════════════════════════════════════════════════
#  3. KPI 卡片
# ═══════════════════════════════════════════════════════

def _build_kpi_cards(station: dict, comp_result: dict, pm: dict) -> List[dict]:
    """构建 4 张 KPI 卡片"""
    cards = []

    # 1. 均衡利用率区间（⭐⭐ 推演）
    cp = comp_result.get("competitive_position") if isinstance(comp_result, dict) else {}
    cp = cp or {}
    eu = cp.get("equilibrium_utilization") if isinstance(cp, dict) else {}
    eu = eu or {}
    if eu and isinstance(eu, dict):
        low_val = eu.get("low")
        high_val = eu.get("high")
        if low_val is not None and high_val is not None:
            # 当区间很窄时保留更多小数位，避免 [1%-1%] 的困惑显示
            diff = high_val - low_val
            if diff < 0.0001:
                value_str = f"≈{low_val:.2%}"
            elif diff < 0.001:
                value_str = f"[{low_val:.2%}-{high_val:.2%}]"
            else:
                value_str = f"[{low_val:.1%}-{high_val:.1%}]"
        else:
            value_str = "N/A"
        cards.append({
            "label": "均衡利用率区间",
            "value": value_str,
            "trend": "flat",
            "benchmark": "竞品均值参考",
            "detail": "弹性假设 1.5-2.5",
            "trust": "⭐⭐",
        })

    # 2. 年收益预估（⭐ 估算）
    # 由于利用率数据质量极差，年收益只能给粗略估计
    power = station.get("total_installed_power", 0)
    piles = (station.get("le_30kw_count", 0) + station.get("gt_30_le_120kw_count", 0) +
             station.get("gt_120_le_360kw_count", 0) + station.get("gt_360kw_count", 0))
    # 粗略假设：平均利用率 5%，每度电收益 0.3 元
    rough_util = 0.05
    rough_profit_per_kwh = 0.3
    daily_energy = power * rough_util * 12  # 假设每天有效运营 12 小时
    annual_profit = daily_energy * rough_profit_per_kwh * 365

    cards.append({
        "label": "年收益预估",
        "value": f"{annual_profit/10000:+.1f}万",
        "trend": "down" if annual_profit < 0 else "up",
        "benchmark": "行业平均约 5-15 万/年",
        "detail": "基于粗略利用率假设（实际数据质量差）",
        "trust": "⭐",
    })

    # 3. 竞争基准价差（⭐⭐⭐ 硬数据）
    bench = comp_result.get("competitive_position", {}).get("competitive_benchmark_price", {})
    if bench:
        gap_pct = bench.get("price_gap_pct", 0)
        cards.append({
            "label": "竞争基准价差",
            "value": f"{gap_pct:+.0f}%",
            "trend": "up" if gap_pct > 0 else "down",
            "benchmark": f"基准价 ¥{bench.get('benchmark_price', 0):.2f}/度",
            "detail": "同 grid 竞品服务费加权均价",
            "trust": "⭐⭐⭐",
        })

    # 4. 高峰时段（⭐⭐⭐ 硬数据）
    gp = station.get("grid_vehicle_profile") or {}
    peak = gp.get("peak_hour_car_trips", 0)
    # 高峰时段从 grid 数据中推断（如果有）
    cards.append({
        "label": "高峰时段",
        "value": "13:00" if peak > 0 else "待观测",
        "trend": "flat",
        "benchmark": "行业高峰 12-14 点",
        "detail": "grid 观测峰值",
        "trust": "⭐⭐⭐" if peak > 0 else "⭐⭐",
    })

    return cards


# ═══════════════════════════════════════════════════════
#  4. 提升路径（硬算部分）
# ═══════════════════════════════════════════════════════

def _build_paths(station: dict, pm: dict, comp_result: dict) -> List[dict]:
    """构建提升路径（只给公式透明的数字）"""
    paths = []

    # 路径 1：峰谷电价优化（如果价格结构支持）
    price_parsed = station.get("electricity_fee_parsed")
    if price_parsed:
        # 粗略估算：如果有峰谷价差
        # 假设日均 240 度 × 40% 高峰 × ¥0.5 价差 × 365
        daily_energy = station.get("total_installed_power", 0) * 0.05 * 12
        saving = daily_energy * 0.4 * 0.5 * 365 / 10000  # 万元
        if saving > 0.5:
            paths.append({
                "title": "峰谷电价优化",
                "category": "成本优化",
                "annual_gain": round(saving, 1),
                "effort": "low",
                "trust": "⭐⭐",
                "calculation": f"基于5%利用率假设，日均{daily_energy:.0f}度×40%高峰×¥0.5价差×365天",
                "detail": "将高峰充电量移至低谷时段，直接利用峰谷电价差降本",
            })

    # 路径 2：功率改造（基于 TVD 错配）
    tvd = pm.get("tvd_score", 0)
    if tvd > 0.35:
        dominant = pm.get("dominant_mismatch")
        if dominant and dominant["direction"] in ("过剩", "结构性错配"):
            paths.append({
                "title": "功率结构调整",
                "category": "资产盘活",
                "annual_gain": None,  # 改造成本复杂，不给精确数字
                "effort": "high",
                "trust": "⭐⭐",
                "calculation": None,
                "detail": f"{dominant['label']}（{dominant['power_range']}）供给过剩 {dominant['gap_pct']:.0f}%，建议改造为更贴近需求的功率档",
            })

    # 路径 3：定价策略调整（基于竞争定位）
    bench = comp_result.get("competitive_position", {}).get("competitive_benchmark_price", {})
    if bench:
        gap_pct = bench.get("price_gap_pct", 0)
        if abs(gap_pct) > 20:
            direction = "下调" if gap_pct > 0 else "上调"
            paths.append({
                "title": "定价策略调整",
                "category": "博弈调价",
                "annual_gain": None,
                "effort": "low",
                "trust": "⭐⭐⭐",
                "calculation": None,
                "detail": f"当前服务费高于同 grid 竞品 {gap_pct:.0f}%，存在{direction}空间（无精确收益模型）",
            })

    # 按 effort 排序（low → medium → high）
    effort_order = {"low": 0, "medium": 1, "high": 2}
    paths.sort(key=lambda x: effort_order.get(x["effort"], 3))

    return paths


# ═══════════════════════════════════════════════════════
#  5. 主构建函数
# ═══════════════════════════════════════════════════════

def build_diagnosis_report(station: dict, all_stations: List[dict], similar_stations: list = None) -> dict:
    """
    构建完整的诊断报告。

    输入：
        station: 当前场站完整数据（JSONL 中的一行）
        all_stations: 所有场站列表（用于竞争定位分析）
        similar_stations: RAG 检索到的相似场站列表（可选）

    输出：完整的诊断报告 JSON（对齐 输出界面.md 规范）
    """
    # 1. 各模块分析
    pm = analyze_power_mismatch(station)
    brand = extract_vehicle_profile(station)
    grid_stations = _get_grid_stations(station, all_stations)

    # 竞争定位分析（如果 grid_stations 为空，用全部场站）
    try:
        from core.competition_analyzer import analyze_competition
        comp_result = analyze_competition(station, grid_stations if grid_stations else all_stations)
    except Exception as e:
        comp_result = {"error": str(e)}

    # 2. 5 维雷达图（含同区域均值参考线）
    radar, scores, sector_avg = _build_radar(station, comp_result, all_stations)

    # 3. 称号
    tvd_score = pm.get("tvd_score", 0.5) if "error" not in pm else 0.5
    title, title_reason = _determine_title(scores, tvd_score)

    # 4. Headline（一句话痛点，不含称号）
    bench = comp_result.get("competitive_position", {}).get("competitive_benchmark_price", {})
    price_gap = bench.get("price_gap_pct", 0) if bench else 0
    headline = ""  # headline 由 LLM 生成精炼痛点，不显示称号

    # 5. KPI 卡片
    kpi_cards = _build_kpi_cards(station, comp_result, pm)

    # 6. 提升路径
    paths = _build_paths(station, pm, comp_result)

    # 6.5 推导过程自然语言解释
    scoring_reasoning = _build_scoring_reasoning(station, scores, pm, comp_result)

    # 7. 季节波动
    gp = station.get("grid_vehicle_profile") or {}
    vtp = gp.get("vehicle_tag_global_profile", {})
    seasonal = extract_seasonal_fluctuation(vtp) if vtp else {"error": "无季节数据"}

    # 8. 检测无 grid 数据警告
    has_grid = bool(station.get("grid_vehicle_profile"))
    warnings = []
    if not has_grid:
        warnings.append({
            "severity": "high",
            "icon": "⚠️",
            "message": "本场站无 grid 画像数据，地段/硬件/饱和度分析基于有限信息",
            "detail": "grid_vehicle_profile 缺失，车型构成、功率需求、SOC、季节波动等模块无法计算。建议补充网格画像数据后重新诊断。",
        })

    # 8.5 竞品价格对标（简化版 min/avg/max）
    price_benchmark_result = analyze_price_benchmark(station, all_stations)

    # 8.6 生成 detail_text（Markdown 摘要）
    detail_text = _build_detail_text(station, comp_result, pm, brand)

    # 9. 组装报告
    report = {
        "dashboard": {
            "headline": headline,
            "overall_score": int(sum(scores.values()) / len(scores)),
            "title": title,
            "title_reason": title_reason,
            "radar": radar,
            "scoring_logic": "五维基于硬数据计算：地段(grid车流/SOC/净流入)、硬件(TVD错配分数)、定价(价差百分比)、运营(装机×利用率假设)、饱和度(车流/装机比)",
            "sector_avg": sector_avg,
            "scoring_reasoning": scoring_reasoning,
            "warnings": warnings,
        },
        "kpi_cards": kpi_cards,
        "power_mismatch": pm,
        "brand_analysis": brand,
        "competitive_position": comp_result,
        "price_benchmark_result": price_benchmark_result,
        "benchmark_stations": _annotate_benchmark_trust(similar_stations or []),
        "seasonal": seasonal,
        "paths": paths,
        "detail_text": detail_text,
    }

    return report


def _build_detail_text(station: dict, comp_result: dict, pm: dict, brand: dict) -> str:
    """生成 Markdown 格式的详细分析摘要。"""
    parts = []
    sname = station.get("station_name", "本场站")

    # ═══ 1. 竞争定位详细分析 ═══
    cp = comp_result.get("competitive_position", {}) if isinstance(comp_result, dict) else {}
    if cp:
        summary = cp.get("summary", "")
        if summary:
            parts.append(f"## 竞争定位\n\n{summary}")

        # 容量份额 vs 实际份额
        cva = cp.get("capacity_vs_actual", {})
        if cva and "error" not in cva:
            cap = cva.get("capacity_share_pct")
            act = cva.get("actual_share_pct")
            gap = cva.get("share_gap_pct")
            interp = cva.get("interpretation", "")
            lines = ["\n### 容量份额 vs 实际份额"]
            if cap is not None:
                lines.append(f"- 容量份额（桩数占比）: {cap}%")
            if act is not None:
                lines.append(f"- 实际份额（车流占比）: {act}%")
            if gap is not None:
                lines.append(f"- 偏差: {gap:+.1f}% → {interp}")
            parts.append("\n".join(lines))

        # 竞争基准价差
        bench = cp.get("competitive_benchmark_price", {})
        if bench and "error" not in bench:
            my_p = bench.get("my_price")
            b_p = bench.get("benchmark_price")
            gap_y = bench.get("price_gap_yuan")
            gap_pct = bench.get("price_gap_pct")
            lines = ["\n### 竞争基准价差"]
            if my_p is not None:
                lines.append(f"- 本场站服务费: ¥{my_p}/度")
            if b_p is not None:
                lines.append(f"- 同 grid 竞品基准: ¥{b_p}/度")
            if gap_y is not None and gap_pct is not None:
                direction = "高于" if gap_y > 0 else "低于"
                lines.append(f"- 价差: {direction}基准 {abs(gap_y):.2f}元/度（{gap_pct:+.1f}%）")
            note = bench.get("note", "")
            if note:
                lines.append(f"- 说明: {note}")
            parts.append("\n".join(lines))

        # 均衡利用率区间
        eu = cp.get("equilibrium_utilization", {})
        if eu and "error" not in eu and eu.get("low") is not None:
            low = eu.get("low")
            high = eu.get("high")
            base = eu.get("base_util")
            elast = eu.get("elasticity_range", [1.5, 2.5])
            note = eu.get("note", "")
            diff = high - low if high is not None and low is not None else 0
            if diff < 0.0001:
                range_str = f"≈{low:.2%}"
            elif diff < 0.001:
                range_str = f"[{low:.2%}-{high:.2%}]"
            else:
                range_str = f"[{low:.1%}-{high:.1%}]"
            lines = [
                "\n### 均衡利用率区间（推演）",
                f"- 区间: {range_str}",
                f"- 基础利用率: {base:.2%}（容量份额 × 行业上限 10%）" if base else "",
                f"- 价格弹性假设: {elast[0]}-{elast[1]}",
                f"- 说明: {note}" if note else "",
            ]
            parts.append("\n".join([l for l in lines if l]))

    # ═══ 2. 功率错配详细分析 ═══
    if "error" not in pm:
        tvd = pm.get("tvd_score", 0)
        level = pm.get("tvd_level", "")
        direction = pm.get("mismatch_direction", "")
        rec = pm.get("recommendation", "")
        parts.append(f"## 功率错配分析\n\nTVD = {tvd:.2f}（{level}），{direction}。{rec}")

        # 4 档功率供需对比表
        sv = pm.get("supply_vs_demand", [])
        if sv:
            lines = ["\n### 各功率档供需对比"]
            lines.append("| 功率档 | 供给占比 | 需求占比 | 偏差 | 判断 |")
            lines.append("|--------|----------|----------|------|------|")
            for item in sv:
                label = item.get("label", "")
                s_pct = item.get("supply_pct", 0)
                d_pct = item.get("demand_pct", 0)
                gap = item.get("gap_pct", 0)
                direc = item.get("direction", "")
                lines.append(f"| {label} | {s_pct:.1f}% | {d_pct:.1f}% | {gap:+.1f}% | {direc} |")
            parts.append("\n".join(lines))

        # 电池容量建议
        bc = pm.get("battery_context", {})
        if bc and "error" not in bc:
            suggestion = bc.get("power_suggestion", "")
            dominant = bc.get("dominant_range", "")
            dpct = bc.get("dominant_pct")
            wavg = bc.get("weighted_avg_kwh")
            lines = ["\n### 电池容量与功率建议"]
            if suggestion:
                lines.append(f"- {suggestion}")
            if dominant and dpct is not None:
                lines.append(f"- 主流电池容量: {dominant}kWh（占 {dpct:.1f}%）")
            if wavg is not None:
                lines.append(f"- 加权平均电池容量: {wavg:.1f}kWh")
            parts.append("\n".join(lines))

    # ═══ 3. 品牌画像详细分析 ═══
    bm = brand.get("brand_matrix", {}) if isinstance(brand, dict) else {}
    if "error" not in bm:
        title = bm.get("title", "私家车市场竞争格局")
        brands = bm.get("brands", [])
        conc = bm.get("concentration", {})
        structure = conc.get("structure", "") if isinstance(conc, dict) else ""
        cr3 = conc.get("cr3", 0) if isinstance(conc, dict) else 0
        cr5 = conc.get("cr5", 0) if isinstance(conc, dict) else 0

        lines = [f"## {title}"]
        lines.append(f"\n{sname}周边{title.replace('市场竞争格局', '')}呈**{structure}**态势（CR3 = {cr3:.0%}，CR5 = {cr5:.0%}）。")

        if brands:
            lines.append("\n### 品牌 TOP5")
            lines.append("| 品牌 | 占比 | 车次 |")
            lines.append("|------|------|------|")
            for b in brands[:5]:
                lines.append(f"| {b.get('brand', '')} | {b.get('share_pct', 0)}% | {b.get('cars', 0):,} |")
        parts.append("\n".join(lines))

    # 电池容量分布
    bat = brand.get("battery_capacity", {}) if isinstance(brand, dict) else {}
    if "error" not in bat:
        lines = ["\n### 电池容量分布"]
        suggestion = bat.get("power_suggestion", "")
        if suggestion:
            lines.append(f"- {suggestion}")
        dom = bat.get("dominant_range", "")
        dpct = bat.get("dominant_pct")
        if dom and dpct is not None:
            lines.append(f"- 主流区间: {dom}kWh（{dpct:.1f}%）")
        cov = bat.get("cover_80_range", "")
        if cov:
            lines.append(f"- 覆盖 80% 车辆: {cov}kWh")
        wavg = bat.get("weighted_avg_kwh")
        if wavg is not None:
            lines.append(f"- 加权平均: {wavg:.1f}kWh")
        parts.append("\n".join(lines))

    # 季节波动
    sf = brand.get("seasonal_fluctuation", {}) if isinstance(brand, dict) else {}
    if "error" not in sf:
        peak = sf.get("peak_season", "")
        trough = sf.get("trough_season", "")
        max_chg = sf.get("max_change_pct", 0)
        seasons = sf.get("season_changes", [])
        lines = ["\n## 季节波动分析"]
        lines.append(f"\n- 峰值: {peak}，谷值: {trough}，最大波动: {max_chg}%")
        if seasons:
            lines.append("- 各季节相对变化:")
            for s in seasons:
                lines.append(f"  - {s}")
        parts.append("\n".join(lines))

    return "\n\n".join(parts) if parts else "暂无详细分析文本。"


def _annotate_benchmark_trust(stations: list) -> list:
    """为 RAG 相似场站添加可信度标签"""
    for s in stations:
        meta = s.get("metadata", {})
        if meta.get("has_grid_profile"):
            s["trust"] = "⭐⭐⭐"
            s["trust_reason"] = "含 grid 画像数据（车流/车型/SOC/功率需求）"
        else:
            s["trust"] = "⭐⭐"
            s["trust_reason"] = "仅含基础运营数据（桩数/价格），无 grid 画像"
    return stations


def build_report_by_profile(profile: dict, similar_stations: list = None) -> dict:
    """
    根据用户输入的 profile，匹配最佳场站并生成完整报告。
    这是 /api/diagnose 的入口函数。
    """
    station = _find_station_by_profile(profile)
    if not station:
        return {"error": "无法找到匹配的场站数据"}

    all_stations = _load_all_stations()
    return build_diagnosis_report(station, all_stations, similar_stations)
