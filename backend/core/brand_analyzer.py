"""
品牌分析与车辆画像提取模块
从 vehicle_tag_global_profile 解析品牌构成、电池容量、充电紧迫度、季节波动等特征

数据说明：
- 93 个标签/场站，其中 52 个含品牌信息（Band1-5 + OtherBand）
- Band 映射：Band1=BYD, Band2=Tesla, Band3=理想, Band4=埃安, Band5=小鹏
- 标签前缀：Sijiacd(私家车), Yunying(营运车), Gongwu(公务车), Gonglu(公路车)等
- 注意：不同字段的 date_type 可能不一致，需在聚合时做底数对齐
"""

from typing import Dict, List, Optional, Tuple
from collections import defaultdict
import math

# ── 品牌映射 ──
BRAND_MAP = {
    "Band1": "比亚迪",
    "Band2": "特斯拉",
    "Band3": "理想",
    "Band4": "埃安",
    "Band5": "小鹏",
    "OtherBand": "非自有桩品牌",
}

# 电池容量档位对应的大致 kWh 范围（用于展示）
# 基于行业常见分段推断
BATTERY_CAPACITY_RANGES = {
    1:  "<10",
    2:  "10-20",
    3:  "20-30",
    4:  "30-40",
    5:  "40-50",
    6:  "50-60",
    7:  "60-70",
    8:  "70-80",
    9:  "80-90",
    10: "90-100",
    11: "100-110",
    12: "110-120",
    13: "120-150",
    14: ">150",
}

# 电池容量档位中点值，用于计算加权平均
BATTERY_CAPACITY_MIDPOINTS = {
    1:  5,   2:  15,  3:  25,  4:  35,  5:  45,
    6:  55,  7:  65,  8:  75,  9:  85,  10: 95,
    11: 105, 12: 115, 13: 135, 14: 160,
}

# 基准日期类型（用于对齐底数）
BASE_DATE_TYPE = "夏季"


def _parse_tag(tag: str) -> Tuple[str, Optional[str], str]:
    """
    解析标签名，返回 (vehicle_type, brand_key, power_level)
    例：Sijiacd_Band2_P1 → ('私家车', 'Band2', 'P1')
        Gongwu_P2 → ('公务车', None, 'P2')
    """
    parts = tag.split("_")
    vtype_map = {
        "Sijiacd": "私家车",
        "Yunying": "营运车",
        "Gongwu": "公务车",
        "Gonglu": "公路车",
        "Chuzu": "出租车",
        "Huwei": "环卫车",
        "Wuye": "物业车",
        "Wuliu": "物流车",
        "Jiaolian": "教练车",
        "Wangyue": "网约车",
    }
    vtype = vtype_map.get(parts[0], parts[0])
    
    brand_key = None
    power_level = None
    for p in parts[1:]:
        if p.startswith("Band") or p == "OtherBand":
            brand_key = p
        elif p.startswith("P"):
            power_level = p
    return vtype, brand_key, power_level


def _get_cars_for_date_type(data: dict, date_type: str = BASE_DATE_TYPE) -> int:
    """从 total_cars_by_date_type 获取指定日期类型的车辆数，回退到任意可用值"""
    cars_by_dt = data.get("total_cars_by_date_type", {})
    if date_type in cars_by_dt:
        return cars_by_dt[date_type]
    # 回退：取最大值（通常数据最完整）
    if cars_by_dt:
        return max(cars_by_dt.values())
    return 0


# ═══════════════════════════════════════════════════════
#  特征 1：品牌构成矩阵（P0）
# ═══════════════════════════════════════════════════════

def extract_brand_matrix(vehicle_tag_profile: dict) -> dict:
    """
    提取私家车品牌构成矩阵。
    标题必须写"私家车市场竞争格局"——41 个无品牌标签覆盖不了全量。
    
    返回：{
        "title": "私家车市场竞争格局",
        "total_branded_cars": int,
        "brands": [
            {"brand": "特斯拉", "share_pct": 20.5, "cars": 1234, "power_level": "P1"},
            ...
        ],
        "concentration": {"cr3": 0.65, "cr5": 0.92},  # 品牌集中度
        "confidence": "⭐⭐⭐",
        "note": "仅统计含品牌标签的私家车/营运车..."
    }
    """
    brand_stats = defaultdict(lambda: {"cars": 0, "power_levels": defaultdict(int)})
    total_branded = 0
    
    for tag, data in vehicle_tag_profile.items():
        vtype, brand_key, power_level = _parse_tag(tag)
        if not brand_key:
            continue  # 无品牌标签跳过
        
        cars = _get_cars_for_date_type(data)
        if cars <= 0:
            continue
        
        brand_name = BRAND_MAP.get(brand_key, brand_key)
        brand_stats[brand_name]["cars"] += cars
        if power_level:
            brand_stats[brand_name]["power_levels"][power_level] += cars
        total_branded += cars
    
    if total_branded == 0:
        return {"error": "无品牌标签数据", "confidence": "N/A"}
    
    # 按占比排序
    brands = []
    for brand_name, stats in sorted(brand_stats.items(), key=lambda x: -x[1]["cars"]):
        share = stats["cars"] / total_branded
        # 取该品牌最主要的功率档
        main_power = max(stats["power_levels"].items(), key=lambda x: x[1])[0] if stats["power_levels"] else None
        brands.append({
            "brand": brand_name,
            "share_pct": round(share * 100, 1),
            "cars": stats["cars"],
            "main_power_level": main_power,
        })
    
    # 集中度计算（CR3 / CR5）
    sorted_shares = sorted([b["share_pct"] / 100 for b in brands], reverse=True)
    cr3 = sum(sorted_shares[:3])
    cr5 = sum(sorted_shares[:5])
    
    # 竞争格局判断
    if cr3 >= 0.7:
        structure = "高度集中"
    elif cr3 >= 0.5:
        structure = "中度集中"
    else:
        structure = "分散竞争"
    
    return {
        "title": "私家车市场竞争格局",
        "total_branded_cars": total_branded,
        "brands": brands,
        "concentration": {
            "cr3": round(cr3, 3),
            "cr5": round(cr5, 3),
            "structure": structure,
        },
        "confidence": "⭐⭐⭐",
        "note": f"仅统计含品牌标签的车辆（{total_branded:,}车次基准），不含公务车/出租车/环卫车等无品牌标签。",
    }


# ═══════════════════════════════════════════════════════
#  特征 2：电池容量集中度（P0）— TVD 错配的"为什么"解释层
# ═══════════════════════════════════════════════════════

def extract_battery_capacity(vehicle_tag_profile: dict) -> dict:
    """
    提取电池容量分布，为功率错配分析提供"为什么"的解释层。
    
    与 TVD 互补：
    - TVD：供给功率分布 vs 需求功率分布 → "多错"
    - 电池容量：14 档分布 → "为什么错"
    
    返回：{
        "title": "电池容量分布与功率建议",
        "capacity_distribution": [{"range": "50-60", "pct": 65.2, "midpoint": 55}, ...],
        "weighted_avg_kwh": 58.3,
        "dominant_range": "50-60",
        "power_suggestion": "120kW 桩已覆盖 85% 车辆需求",
        "confidence": "⭐⭐⭐",
    }
    """
    # 聚合所有标签的电池容量分布（按车辆数加权）
    total_weighted_ratio = [0.0] * 15  # 1-14
    total_cars = 0
    
    for tag, data in vehicle_tag_profile.items():
        bc = data.get("battery_capacity", {})
        dist = bc.get("distribution", {})
        if not dist:
            continue
        
        # 对齐底数：用 battery_capacity 自己的 date_type 对应的车辆数
        bc_date_type = bc.get("date_type", BASE_DATE_TYPE)
        cars = _get_cars_for_date_type(data, bc_date_type)
        if cars <= 0:
            continue
        
        for i in range(1, 15):
            key = f"ratio_cnt_{i}"
            ratio = dist.get(key, 0.0) / 100.0  # ratio 是百分比值（如 82.11），转小数
            total_weighted_ratio[i] += ratio * cars
        total_cars += cars
    
    if total_cars == 0:
        return {"error": "无电池容量数据", "confidence": "N/A"}
    
    # 归一化到百分比
    distribution = []
    weighted_sum = 0.0
    max_pct = 0.0
    dominant_idx = 1
    
    for i in range(1, 15):
        pct = total_weighted_ratio[i] / total_cars
        if pct > max_pct:
            max_pct = pct
            dominant_idx = i
        distribution.append({
            "range": BATTERY_CAPACITY_RANGES[i],
            "pct": round(pct, 2),
            "midpoint": BATTERY_CAPACITY_MIDPOINTS[i],
        })
        weighted_sum += pct * BATTERY_CAPACITY_MIDPOINTS[i]
    
    # 累计分布，找覆盖 80% 的容量档
    cumsum = 0.0
    cover_80_idx = 14
    for i in range(1, 15):
        cumsum += distribution[i - 1]["pct"]
        if cumsum >= 0.80 and cover_80_idx == 14:
            cover_80_idx = i
    
    # 功率建议：按覆盖 80% 的电池容量推算
    # 假设从 20% 充到 80%，需要 60% 电量
    cover_80_kwh = BATTERY_CAPACITY_MIDPOINTS[cover_80_idx]
    energy_needed = cover_80_kwh * 0.6  # 60% 电量
    power_15min = energy_needed * 60 / 15
    power_30min = energy_needed * 60 / 30
    
    # 基于 dominant range（主流电池）计算建议
    dominant_mid = BATTERY_CAPACITY_MIDPOINTS[dominant_idx]
    dominant_energy = dominant_mid * 0.6  # 20%→80% 需 60% 电量
    dominant_15min_power = dominant_energy * 60 / 15
    dominant_30min_power = dominant_energy * 60 / 30
    
    # 功率建议文案（基于 dominant range，更贴合实际主流需求）
    if dominant_15min_power <= 60:
        suggestion = (
            f"主流电池 {BATTERY_CAPACITY_RANGES[dominant_idx]}kWh（占 {max_pct*100:.0f}%），"
            f"从 20% 充到 80% 约需 {dominant_energy:.0f} 度电，"
            f"60kW 桩 {dominant_energy/60*60:.0f} 分钟即可满足"
        )
    elif dominant_15min_power <= 120:
        suggestion = (
            f"主流电池 {BATTERY_CAPACITY_RANGES[dominant_idx]}kWh（占 {max_pct*100:.0f}%），"
            f"120kW 桩 15 分钟内可从 20% 充至 80%"
        )
    elif dominant_15min_power <= 240:
        suggestion = (
            f"主流电池 {BATTERY_CAPACITY_RANGES[dominant_idx]}kWh（占 {max_pct*100:.0f}%），"
            f"需 180kW 以上桩才能 15 分钟快充，"
            f"120kW 桩约需 {dominant_energy/120*60:.0f} 分钟"
        )
    else:
        suggestion = (
            f"主流电池 {BATTERY_CAPACITY_RANGES[dominant_idx]}kWh（占 {max_pct*100:.0f}%），"
            f"360kW 超充对该电池容量的边际效用极低，"
            f"120kW 桩已足够（约 {dominant_energy/120*60:.0f} 分钟）"
        )
    
    return {
        "title": "电池容量分布与功率建议",
        "capacity_distribution": distribution,
        "weighted_avg_kwh": round(weighted_sum, 1),
        "dominant_range": BATTERY_CAPACITY_RANGES[dominant_idx],
        "dominant_pct": round(max_pct * 100, 1),
        "cover_80_range": BATTERY_CAPACITY_RANGES[cover_80_idx],
        "power_suggestion": suggestion,
        "charge_15min_power_kw": round(power_15min, 0),
        "charge_30min_power_kw": round(power_30min, 0),
        "confidence": "⭐⭐⭐",
    }


# ═══════════════════════════════════════════════════════
#  特征 3：季节波动分析（P0）— 趋势推演输入
# ═══════════════════════════════════════════════════════

def _clean_season_name(name: str) -> str:
    """去掉季节名称中的'典型日'，如'夏季典型日'→'夏季'"""
    return name.replace("典型日", "")


def extract_seasonal_fluctuation(vehicle_tag_profile: dict) -> dict:
    """
    提取季节波动，直接展示 + 作为趋势推演 LLM 的输入参数。
    
    返回：{
        "title": "季节波动分析",
        "seasons": {"夏季": 100000, "冬季": 120000, ...},
        "peak_season": "冬季",
        "trough_season": "国庆",
        "max_change_pct": 23.5,
        "trend_hint_for_llm": "冬季比国庆高 30%",
        "confidence": "⭐⭐⭐",
    }
    """
    # 聚合所有标签的车辆数
    season_totals = defaultdict(int)
    
    for tag, data in vehicle_tag_profile.items():
        cars_by_dt = data.get("total_cars_by_date_type", {})
        for dt, cars in cars_by_dt.items():
            clean_dt = _clean_season_name(dt)
            season_totals[clean_dt] += cars
    
    if not season_totals:
        return {"error": "无季节数据", "confidence": "N/A"}
    
    # 找出峰值和谷值
    peak_season = max(season_totals, key=season_totals.get)
    trough_season = min(season_totals, key=season_totals.get)
    peak_val = season_totals[peak_season]
    trough_val = season_totals[trough_season]
    
    max_change_pct = round((peak_val - trough_val) / max(trough_val, 1) * 100, 1)
    
    # 为 LLM 生成趋势推演提示
    hints = []
    base_name = _clean_season_name(BASE_DATE_TYPE)
    base = season_totals.get(base_name, peak_val)
    for season, val in season_totals.items():
        if season == base_name:
            continue
        diff_pct = round((val - base) / base * 100, 1)
        direction = "高" if diff_pct > 0 else "低"
        hints.append(f"{season}较{base_name}{direction}{abs(diff_pct)}%")
    
    return {
        "title": "季节波动分析",
        "seasons": dict(season_totals),
        "peak_season": peak_season,
        "trough_season": trough_season,
        "max_change_pct": max_change_pct,
        "season_changes": hints,
        "trend_hint_for_llm": f"{peak_season}比{trough_season}高{max_change_pct}%。{'；'.join(hints)}",
        "confidence": "⭐⭐⭐",
    }


# ═══════════════════════════════════════════════════════
#  特征 4：充电紧迫度（P1）— 原名"充电焦虑指数"，改为归一化排名
# ═══════════════════════════════════════════════════════

def compute_urgency_ranking(vehicle_tag_profile: dict, grid_all_profiles: Optional[List[dict]] = None) -> dict:
    """
    计算各标签的充电紧迫度（网格内归一化排名）。
    
    原名"充电焦虑指数"，评审建议：
    1. 改名"充电紧迫度"——去掉主观色彩
    2. 做网格内归一化排名而非绝对值
    3. 尽量对齐底数（取同一标签的 mileage 和 soc）
    
    urgency = (100 - avg_start_soc) * (mileage_day_km / 100)  # 原始计算
    然后做网格内归一化排名
    
    返回：{
        "title": "充电紧迫度分析",
        "tags_ranked": [
            {"tag": "Sijiacd_Band2_P1", "urgency_raw": 2.34, "rank_pct": 85, "label": "高紧迫"},
            ...
        ],
        "summary": "特斯拉 P1 车主紧迫度排前 20%，建议保障快充通道",
        "confidence": "⭐⭐",
        "note": "基于网格内归一化排名，非绝对焦虑水平",
    }
    """
    tag_urgencies = []
    
    for tag, data in vehicle_tag_profile.items():
        soc_data = data.get("soc_distribution", {})
        mileage_data = data.get("mileage", {})
        
        avg_start_soc = soc_data.get("avg_start_soc")
        mileage_day_km = mileage_data.get("mileage_day_km")
        
        if avg_start_soc is None or mileage_day_km is None:
            continue
        
        # 原始紧迫度：低 SOC + 高里程 = 高紧迫
        # 归一化：mileage 按 300km 封顶（行业日均上限）
        soc_factor = (100 - avg_start_soc) / 100
        mileage_factor = min(mileage_day_km / 300.0, 1.0)
        urgency = soc_factor * mileage_factor
        
        vtype, brand_key, power_level = _parse_tag(tag)
        brand_name = BRAND_MAP.get(brand_key, brand_key) if brand_key else None
        
        tag_urgencies.append({
            "tag": tag,
            "vehicle_type": vtype,
            "brand": brand_name,
            "power_level": power_level,
            "avg_start_soc": avg_start_soc,
            "mileage_day_km": mileage_day_km,
            "urgency_raw": round(urgency, 3),
        })
    
    if not tag_urgencies:
        return {"error": "无 SOC/里程数据", "confidence": "N/A"}
    
    # 网格内归一化排名（0-100，越高越紧迫）
    sorted_by_urgency = sorted(tag_urgencies, key=lambda x: x["urgency_raw"], reverse=True)
    n = len(sorted_by_urgency)
    
    for i, item in enumerate(sorted_by_urgency):
        rank_pct = round((i + 1) / n * 100)  # 1=最紧迫(100%), n=最不紧迫(0%)
        # 反转：排名越靠前（i越小），rank_pct 越高
        item["rank_pct"] = 100 - rank_pct + 1
        if item["rank_pct"] >= 80:
            item["label"] = "高紧迫"
        elif item["rank_pct"] >= 50:
            item["label"] = "中紧迫"
        else:
            item["label"] = "低紧迫"
    
    # 摘要：最紧迫的 3 个标签
    top3 = sorted_by_urgency[:3]
    top_brands = [t["brand"] or t["vehicle_type"] for t in top3 if t["brand"]]
    summary = f"{top_brands[0]}等车主充电紧迫度排前 {top3[0]['rank_pct']}%" if top_brands else "营运车充电紧迫度较高"
    
    return {
        "title": "充电紧迫度分析",
        "tags_ranked": sorted_by_urgency,
        "top_urgent": top3,
        "summary": summary,
        "confidence": "⭐⭐",
        "note": "基于网格内归一化排名（0-100，越高越紧迫），非绝对焦虑水平。 mileage 按 300km 封顶归一化。",
    }


# ═══════════════════════════════════════════════════════
#  特征 5：充电行为模式分类（P2）— 展示层，不给运营建议
# ═══════════════════════════════════════════════════════

def classify_charging_behavior(vehicle_tag_profile: dict) -> dict:
    """
    基于标签级数据做行为模式分类（展示层，不给运营决策建议）。
    
    四类：快充型 / 慢充型 / 通勤型 / 营运型
    分类逻辑：
    - 快充型：P3/P4 高功率档 + 高里程
    - 慢充型：P1/P2 低功率档 + 低里程
    - 通勤型：中等里程(30-80km) + 规律 SOC(起充 30-50%)
    - 营运型：Yunying/Chuzuche/Wangyue 前缀 + 高里程(>100km)
    
    注意：标签本身是聚合数据，分类结果是"典型标签模式"而非"典型车辆模式"。
    """
    patterns = defaultdict(list)
    
    for tag, data in vehicle_tag_profile.items():
        vtype, brand_key, power_level = _parse_tag(tag)
        mileage_data = data.get("mileage", {})
        soc_data = data.get("soc_distribution", {})
        
        mileage = mileage_data.get("mileage_day_km", 0)
        start_soc = soc_data.get("avg_start_soc", 50)
        
        cars = _get_cars_for_date_type(data)
        
        # 分类逻辑
        pattern = None
        if vtype in ("营运车", "出租车", "网约车"):
            pattern = "营运型"
        elif mileage > 100 and power_level in ("P3", "P4"):
            pattern = "快充型"
        elif mileage < 50 and power_level in ("P1", "P2"):
            pattern = "慢充型"
        elif 30 <= mileage <= 80 and 30 <= start_soc <= 60:
            pattern = "通勤型"
        else:
            pattern = "混合型"
        
        patterns[pattern].append({
            "tag": tag,
            "vehicle_type": vtype,
            "brand": BRAND_MAP.get(brand_key, brand_key) if brand_key else None,
            "power_level": power_level,
            "mileage": mileage,
            "start_soc": start_soc,
            "cars": cars,
        })
    
    # 按车辆数统计各模式占比
    total_cars = sum(sum(t["cars"] for t in tags) for tags in patterns.values())
    result = []
    for pattern, tags in sorted(patterns.items(), key=lambda x: -sum(t["cars"] for t in x[1])):
        cars = sum(t["cars"] for t in tags)
        result.append({
            "pattern": pattern,
            "cars": cars,
            "share_pct": round(cars / max(total_cars, 1) * 100, 1),
            "top_tags": tags[:3],  # 前 3 个代表标签
        })
    
    return {
        "title": "充电行为模式分布",
        "patterns": result,
        "total_cars": total_cars,
        "confidence": "⭐",
        "note": "基于标签级聚合数据的模式展示，非车辆级精确分类。仅供展示，不建议基于此做具体运营决策。",
    }


# ═══════════════════════════════════════════════════════
#  品牌专用桩对比分析（三段式）
# ═══════════════════════════════════════════════════════

# 品牌名标准化映射（统一中英文/大小写）
_BRAND_NAME_NORMALIZE = {
    "tesla": "特斯拉",
    "特斯拉": "特斯拉",
    "nio": "蔚来",
    "蔚来": "蔚来",
    "xpeng": "小鹏",
    "小鹏": "小鹏",
    "byd": "比亚迪",
    "比亚迪": "比亚迪",
    "li_auto": "理想",
    "理想": "理想",
    "其他": "其他",
    "others": "其他",
}


def _normalize_brand_name(name: str) -> str:
    """标准化品牌名称"""
    return _BRAND_NAME_NORMALIZE.get(name.lower().strip(), name)


def _build_region_brand_demand(brand_matrix: dict) -> dict:
    """
    从 brand_matrix 构建区域品牌需求画像。
    返回：{"top_brands": [{"brand": "特斯拉", "share_pct": 32.5, "cars": 1234}, ...], "total_cars": int}
    """
    if "error" in brand_matrix:
        return {"error": brand_matrix["error"]}

    brands = brand_matrix.get("brands", [])
    total_cars = brand_matrix.get("total_branded_cars", 0)

    top_brands = []
    for b in brands[:5]:
        top_brands.append({
            "brand": b["brand"],
            "share_pct": b["share_pct"],
            "cars": b["cars"],
            "main_power_level": b.get("main_power_level", ""),
        })

    return {
        "top_brands": top_brands,
        "total_cars": total_cars,
        "concentration": brand_matrix.get("concentration", {}),
    }


def _analyze_brand_pile_breakdown(
    brand_piles: dict,
    brand_matrix: dict,
) -> dict:
    """
    基于用户输入的 brand_piles 与区域车辆品牌占比，做三段式供需对比分析。

    三段式结构：
    1. 区域需求画像：当前区域车辆品牌分布（排除 OtherBand）
    2. 用户供给结构：用户场站品牌专用桩分布
    3. 供需对比诊断：逐品牌判断匹配/缺失/过剩

    需求占比计算：只统计有具体品牌的车辆（排除"非自有桩品牌"OtherBand）。
    即 demand_pct = 某品牌车次 / 所有具体品牌车次总和 × 100%
    """
    # 标准化用户输入的品牌名
    normalized_pb = {}
    for k, v in (brand_piles or {}).items():
        norm_name = _normalize_brand_name(k)
        normalized_pb[norm_name] = (normalized_pb.get(norm_name, 0) or 0) + (v or 0)

    # 排除数值为 0 的品牌，同时排除"其他"
    user_brands = {k: v for k, v in normalized_pb.items() if v > 0 and k not in ("其他", "非自有桩品牌")}
    total_brand_piles = sum(user_brands.values())

    # ── 第 1 段：区域车辆品牌需求画像 ──
    region_demand_text = ""
    top_brands = []
    brand_cars_map = {}     # 品牌 -> 车次
    demand_pct_map = {}     # 品牌 -> 排除 OtherBand 后的需求占比

    if "error" not in brand_matrix:
        brands = brand_matrix.get("brands", [])
        total_branded_cars = brand_matrix.get("total_branded_cars", 0)

        # 计算排除 OtherBand 后的总车次
        otherband_cars = 0
        for b in brands:
            brand_cars_map[b["brand"]] = b["cars"]
            if b["brand"] == "非自有桩品牌":
                otherband_cars = b["cars"]

        total_cars_excl_otherband = total_branded_cars - otherband_cars

        # 按排除 OtherBand 后的占比重新排序取 TOP
        sorted_brands = sorted(
            [b for b in brands if b["brand"] != "非自有桩品牌"],
            key=lambda x: -x["cars"]
        )
        top_brands = sorted_brands[:5]

        if top_brands:
            dominant = top_brands[0]
            # 需求占比基于排除 OtherBand 后的总量
            dominant_demand_pct = (dominant["cars"] / total_cars_excl_otherband * 100) if total_cars_excl_otherband > 0 else 0.0
            region_demand_text = (
                f"通过数据分析，当前区域下周边车辆品牌呈"
                f"「{dominant['brand']}为主」格局（占比 {dominant_demand_pct:.1f}%）。"
            )

            top3_lines = []
            for b in top_brands[:3]:
                pct = (b["cars"] / total_cars_excl_otherband * 100) if total_cars_excl_otherband > 0 else 0.0
                top3_lines.append(f"{b['brand']} {pct:.1f}%（{b['cars']:,}车次）")
            region_demand_text += f"品牌 TOP3：{' / '.join(top3_lines)}。"

            for b in sorted_brands:
                demand_pct_map[b["brand"]] = (
                    (b["cars"] / total_cars_excl_otherband * 100)
                    if total_cars_excl_otherband > 0 else 0.0
                )

    # ── 第 2 段：用户场站品牌专用桩供给结构 ──
    station_supply_text = ""
    if total_brand_piles > 0:
        supply_lines = []
        for brand_name, count in sorted(user_brands.items(), key=lambda x: -x[1]):
            pct = count / total_brand_piles * 100
            supply_lines.append(f"{brand_name} {pct:.0f}%（{count} 台）")
        station_supply_text = (
            f"您场站共配置 {total_brand_piles} 台品牌专用桩，"
            f"分布为：{' / '.join(supply_lines)}。"
        )
    else:
        station_supply_text = "您场站未配置品牌专用桩，当前均为通用桩。"

    # ── 第 3 段：用户场站品牌专用桩诊断 ──
    station_items = []

    # 分析品牌 = 品牌矩阵中出现过的具体品牌 ∪ 用户输入的品牌
    analyzed_brands = set(demand_pct_map.keys())
    analyzed_brands.update(normalized_pb.keys())
    analyzed_brands.discard("其他")
    analyzed_brands.discard("非自有桩品牌")

    for brand_name in sorted(analyzed_brands):
        count = normalized_pb.get(brand_name, 0) or 0
        demand_pct = demand_pct_map.get(brand_name, 0.0)

        # 用户该品牌桩占专用桩总数的供给占比
        supply_pct = (count / total_brand_piles * 100) if total_brand_piles > 0 else 0.0

        # 供需差值（供给占比 − 需求占比）
        gap = supply_pct - demand_pct

        if count == 0:
            if demand_pct < 5:
                judgment = "— 无需配置"
                reason = f"当前区域 {brand_name} 车辆占比仅 {demand_pct:.1f}%，占比偏低，无需专门配置"
            else:
                judgment = "❌ 缺失"
                reason = f"当前区域 {brand_name} 车辆占比 {demand_pct:.1f}%，您场站未配置该品牌专用桩"
        elif gap > 20:
            judgment = "⚠️ 过剩风险"
            reason = f"您场站该品牌专用桩占比 {supply_pct:.1f}%（{count} 台），高于区域车辆占比 {demand_pct:.1f}%"
        elif gap < -20:
            judgment = "❌ 供给不足"
            reason = f"您场站该品牌专用桩占比 {supply_pct:.1f}%（{count} 台），低于区域车辆占比 {demand_pct:.1f}%，建议增补"
        else:
            judgment = "✓ 基本匹配"
            reason = f"您场站该品牌专用桩 {count} 台，与区域车辆占比 {demand_pct:.1f}% 基本匹配"

        station_items.append({
            "brand": brand_name,
            "count": count,
            "supply_pct": round(supply_pct, 1),
            "demand_pct": round(demand_pct, 1),
            "judgment": judgment,
            "reason": reason,
        })

    return {
        "region_demand_text": region_demand_text,
        "station_supply_text": station_supply_text,
        "station_items": station_items,
    }


# ═══════════════════════════════════════════════════════
#  统一入口：从场站数据提取全部品牌画像
# ═══════════════════════════════════════════════════════

def extract_vehicle_profile(station: dict) -> dict:
    """
    从场站数据提取完整的车辆画像（品牌 + 电池 + 季节 + 紧迫度 + 行为模式）。
    """
    gp = station.get("grid_vehicle_profile") or {}
    vtp = gp.get("vehicle_tag_global_profile", {})
    
    if not vtp:
        return {"error": "无 vehicle_tag_global_profile 数据", "confidence": "N/A"}
    
    return {
        "station_id": station.get("station_id"),
        "station_name": station.get("station_name"),
        "grid_code": gp.get("grid_code"),
        "brand_matrix": extract_brand_matrix(vtp),
        "battery_capacity": extract_battery_capacity(vtp),
        "seasonal_fluctuation": extract_seasonal_fluctuation(vtp),
        "urgency_ranking": compute_urgency_ranking(vtp),
        "behavior_patterns": classify_charging_behavior(vtp),
    }
