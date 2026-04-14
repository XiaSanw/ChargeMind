DEMO_INPUT = (
    "我们在昆明市盘龙区有一个充电站，名字叫盘龙快充站。"
    "场地有20个120kW的直流快充桩，目前日均充电量约3000度。"
    "当前购电价是峰段1.2元、平段0.9元、谷段0.6元，服务费0.65元/度。"
    "场地月租金3万元，有3个运维人员。"
    "周边3公里内有5个竞品充电站。"
    "主要客户是网约车司机。"
    "目前没有储能设备，没有会员体系，支持分时段调价。"
)

FIELD_LABELS = {
    "station_name": "场站名称",
    "location": "所在位置",
    "pile_count": "充电桩数量",
    "pile_power_kw": "单桩功率(kW)",
    "daily_kwh": "日均充电量(kWh)",
    "price_peak": "峰段电价(元/kWh)",
    "price_flat": "平段电价(元/kWh)",
    "price_valley": "谷段电价(元/kWh)",
    "service_fee": "服务费(元/kWh)",
    "monthly_rent": "月租金(元)",
    "staff_count": "运维人数",
    "competitor_count": "周边竞品数",
    "customer_type": "主要客群",
}