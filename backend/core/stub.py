"""
算法 Stub — 基于规则的预测（非真实模型）
明确标记为模拟预测，后续由课题组训练的真实模型替换
"""

# 区域平均利用率（来自实际数据统计）
REGION_AVG_UTIL = {
    "南山区": 0.0739,
    "福田区": 0.0467,
    "宝安区": 0.0311,
    "龙岗区": 0.0303,
    "龙华区": 0.0121,
    "罗湖区": 0.0467,
    "光明区": 0.0311,
    "坪山区": 0.0121,
    "盐田区": 0.0739,
    "大鹏新区": 0.0121,
    "前海": 0.0739,
    "未知": 0.0453,
}

# 业态系数（经验值）
BIZ_FACTOR = {
    "交通枢纽": 1.3,
    "商业区": 1.0,
    "办公区": 0.9,
    "住宅区": 0.7,
    "工业区": 1.1,
    "旅游景区": 0.6,
}

# 电价基准（元/度）
DEFAULT_PRICE = 0.6


def algorithm_stub(profile: dict) -> dict:
    """
    基于区域基准和业态系数的规则预测。
    此为 Stub，非真实机器学习模型。
    """
    region = profile.get("region") or "未知"
    biz_types = profile.get("business_type") or []
    total_power = profile.get("total_installed_power") or 100
    pile_count = profile.get("pile_count") or 10
    monthly_rent = profile.get("monthly_rent") or 50000
    staff_count = profile.get("staff_count") or 3
    price = profile.get("avg_price") or DEFAULT_PRICE

    # 基准利用率
    base_util = REGION_AVG_UTIL.get(region, 0.0453)

    # 业态系数（取命中类型中最大的）
    factor = 1.0
    if biz_types:
        factor = max(BIZ_FACTOR.get(b, 1.0) for b in biz_types)

    # 规模系数（桩数越多，利用率略高，但边际递减）
    scale_factor = min(1 + (pile_count - 10) * 0.01, 1.3)

    predicted_util = base_util * factor * scale_factor
    predicted_util = min(predicted_util, 1.0)  # 截断

    # 收益计算（简化公式）
    daily_kwh = total_power * predicted_util * 24
    annual_revenue = daily_kwh * 365 * price
    annual_cost = monthly_rent * 12 + staff_count * 80000
    annual_profit = annual_revenue - annual_cost

    return {
        "predicted_utilization": round(predicted_util, 3),
        "annual_revenue": round(annual_revenue, 2),
        "annual_cost": round(annual_cost, 2),
        "annual_profit": round(annual_profit, 2),
        "confidence": 0.3,
        "is_stub": True,
        "note": "基于区域基准与业态系数的规则预测，非真实机器学习模型，后续由课题组替换",
        "breakdown": {
            "base_utilization": base_util,
            "biz_factor": factor,
            "scale_factor": round(scale_factor, 3),
            "region": region,
            "biz_types": biz_types,
        },
    }
