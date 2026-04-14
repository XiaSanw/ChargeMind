def diagnose(params: dict) -> dict:
    """
    输入: extract_params() 返回的 dict
    输出: 完整诊断结果 dict，结构见下方 return
    """
    daily_kwh = params.get("daily_kwh") or 3000
    annual_kwh = daily_kwh * 365

    price_peak = params.get("price_peak") or 1.2
    price_flat = params.get("price_flat") or 0.9
    price_valley = params.get("price_valley") or 0.6
    service_fee = params.get("service_fee") or 0.65
    monthly_rent = params.get("monthly_rent") or 30000
    staff_count = params.get("staff_count") or 3
    staff_monthly_pay = 6000  # 假设人均月薪

    # =====================
    # 当前经营测算
    # =====================
    cur_peak_ratio = 0.40
    cur_flat_ratio = 0.35
    cur_valley_ratio = 0.25

    avg_purchase = (price_peak * cur_peak_ratio +
                    price_flat * cur_flat_ratio +
                    price_valley * cur_valley_ratio)
    avg_sell = avg_purchase + service_fee

    annual_revenue = annual_kwh * avg_sell / 10000        # 万元
    annual_power_cost = annual_kwh * avg_purchase / 10000 # 万元
    annual_rent = monthly_rent * 12 / 10000               # 万元
    annual_labor = staff_count * staff_monthly_pay * 12 / 10000
    annual_other = 0.96
    
    annual_total_cost = annual_power_cost + annual_rent + annual_labor + annual_other
    annual_profit = annual_revenue - annual_total_cost

    # =====================
    # 优化测算
    # =====================
    opt_peak_ratio = 0.25
    opt_flat_ratio = 0.35
    opt_valley_ratio = 0.40

    opt_avg_purchase = (price_peak * opt_peak_ratio +
                        price_flat * opt_flat_ratio +
                        price_valley * opt_valley_ratio)
    opt_avg_sell = opt_avg_purchase + service_fee

    # 预期提量
    opt_annual_kwh = annual_kwh * 1.15
    opt_revenue = opt_annual_kwh * opt_avg_sell / 10000
    opt_power_cost = opt_annual_kwh * opt_avg_purchase / 10000
    opt_rent = annual_rent
    # 排班优化减人
    opt_labor = (staff_count - 0.5) * staff_monthly_pay * 12 / 10000
    opt_other = annual_other

    opt_total_cost = opt_power_cost + opt_rent + opt_labor + opt_other
    opt_profit = opt_revenue - opt_total_cost

    profit_improvement = opt_profit - annual_profit

    # =====================
    # 动作拆解
    # =====================
    action_purchase_saving = (avg_purchase - opt_avg_purchase) * annual_kwh / 10000
    action_volume_gain = (opt_annual_kwh - annual_kwh) * opt_avg_sell / 10000
    action_labor_saving = annual_labor - opt_labor

    actions = [
        {
            "name": "峰谷结构优化",
            "type": "降本",
            "detail": f"谷段占比从{int(cur_valley_ratio*100)}%升至{int(opt_valley_ratio*100)}%，均价降至{opt_avg_purchase:.2f}元/度。",
            "profit_delta": round(action_purchase_saving, 1),
        },
        {
            "name": "夜间引流调价",
            "type": "增效",
            "detail": f"预计日均充电量提升15%，年充电量增加{int(opt_annual_kwh - annual_kwh)}度。",
            "profit_delta": round(action_volume_gain, 1),
        },
        {
            "name": "运维排班优化",
            "type": "降本",
            "detail": f"低谷期减员，人力当量降至{staff_count - 0.5}人。",
            "profit_delta": round(action_labor_saving, 1),
        },
    ]

    return {
        "current": {
            "annual_kwh": int(annual_kwh),
            "avg_purchase_price": round(avg_purchase, 2),
            "avg_sell_price": round(avg_sell, 2),
            "annual_revenue": round(annual_revenue, 1),
            "annual_total_cost": round(annual_total_cost, 1),
            "annual_profit": round(annual_profit, 1),
        },
        "optimized": {
            "annual_kwh": int(opt_annual_kwh),
            "avg_purchase_price": round(opt_avg_purchase, 2),
            "avg_sell_price": round(opt_avg_sell, 2),
            "annual_revenue": round(opt_revenue, 1),
            "annual_total_cost": round(opt_total_cost, 1),
            "annual_profit": round(opt_profit, 1),
        },
        "actions": actions,
        "summary": {
            "profit_improvement": round(profit_improvement, 1),
            "cost_reduction": round(annual_total_cost - opt_total_cost, 1),
            "revenue_increase": round(opt_revenue - annual_revenue, 1),
        },
        "assumptions": [
            f"人均月薪按{staff_monthly_pay}元估算",
            f"当前峰平谷充电占比按{int(cur_peak_ratio*100)}:{int(cur_flat_ratio*100)}:{int(cur_valley_ratio*100)}估算",
            "优化后日均充电量提升15%为经验估计值",
            f"其他运维成本按月均{int(annual_other/12*10000)}元估算",
        ],
    }