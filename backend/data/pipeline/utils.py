"""
Utility functions for the data cleaning pipeline.
"""

# ---------------------------------------------------------------------------
# Code mappings
# ---------------------------------------------------------------------------

LAND_PROPERTY_MAP = {
    1: "国有用地",
    2: "集体用地",
    3: "私有用地",
    4: "租赁用地",
    10: "商业用地",
    255: "其他",
}

VEHICLE_TYPE_MAP = {
    1: "公交车",
    2: "出租车",
    3: "物流车",
    4: "通勤车",
    5: "大巴车",
    6: "私家车",
    7: "环卫车",
    8: "泥头/重卡车",
    9: "公务车",
    10: "网约车",
    11: "港口码头作业车",
    255: "其他",
}

STATION_STATUS_MAP = {
    5: "运营中",
    50: "运营中",
}

GRID_PREFIX_MAP = {
    "L2NS": "南山区",
    "L2FT": "福田区",
    "L2LH": "龙华区",
    "L2LG": "龙岗区",
    "L2BABC": "宝安区",
    "L2BASJ": "宝安区",
    "L2BASG": "宝安区",
    "L2GM": "光明区",
    "L2PS": "坪山区",
    "L2LYT": "盐田区",
    "L2LDP": "大鹏新区",
    "L2LSS": "罗湖区",
}


# ---------------------------------------------------------------------------
# Fee parser
# ---------------------------------------------------------------------------

def parse_fee(fee_str):
    """
    Parse a fee string into a structured dict.

    Examples
    --------
    >>> parse_fee("")
    None
    >>> parse_fee("0.8")
    {'periods': [{'start': '00:00', 'end': '24:00', 'price': 0.8}],
     'avg_price': 0.8, 'min_price': 0.8, 'max_price': 0.8}
    >>> parse_fee("00:00~08:00,0.5;08:00~24:00,0.8")
    {'periods': [...], 'avg_price': ..., 'min_price': 0.5, 'max_price': 0.8}
    """
    if fee_str is None or (isinstance(fee_str, str) and fee_str.strip() == ""):
        return None

    s = str(fee_str).strip()

    # Simple number (no ~ and no ;)
    if "~" not in s and ";" not in s:
        try:
            price = float(s)
            if price != price:  # NaN check
                return None
            return {
                "periods": [{"start": "00:00", "end": "24:00", "price": price}],
                "avg_price": price,
                "min_price": price,
                "max_price": price,
            }
        except ValueError:
            return None

    periods = []
    prices = []
    for segment in s.split(";"):
        segment = segment.strip()
        if not segment:
            continue
        parts = segment.split(",")
        if len(parts) != 2:
            continue
        time_range, price_str = parts[0].strip(), parts[1].strip()
        if "~" not in time_range:
            continue
        start, end = time_range.split("~", 1)
        try:
            price = float(price_str)
        except ValueError:
            continue
        periods.append({"start": start.strip(), "end": end.strip(), "price": price})
        prices.append(price)

    if not prices:
        return None

    return {
        "periods": periods,
        "avg_price": round(sum(prices) / len(prices), 4),
        "min_price": round(min(prices), 4),
        "max_price": round(max(prices), 4),
    }


# ---------------------------------------------------------------------------
# Region inference
# ---------------------------------------------------------------------------

def infer_region_from_name(station_name):
    """
    Infer Shenzhen district from station name keywords.
    """
    if not isinstance(station_name, str):
        return None

    keywords = {
        "南山": "南山区",
        "福田": "福田区",
        "宝安": "宝安区",
        "龙岗": "龙岗区",
        "龙华": "龙华区",
        "光明": "光明区",
        "坪山": "坪山区",
        "盐田": "盐田区",
        "罗湖": "罗湖区",
        "大鹏": "大鹏新区",
        "前海": "前海",
    }

    for kw, region in keywords.items():
        if kw in station_name:
            return region
    return None


# ---------------------------------------------------------------------------
# Business type inference
# ---------------------------------------------------------------------------

def infer_business_type(station_name):
    """
    Infer business type(s) from station name keywords.
    Returns a list of matched types (can be multiple).
    """
    if not isinstance(station_name, str):
        return []

    # Priority: more specific rules first
    rules = [
        ("交通枢纽", ["地铁站", "地铁", "公交总站", "车站", "机场", "港口"]),
        ("商业区", ["商场", "购物中心", "MALL", "商业街"]),
        ("办公区", ["大厦", "中心", "广场", "科技园", "写字楼", "工业园"]),
        ("住宅区", ["小区", "花园", "家园", "公寓", "村", "苑", "公园大地", "公园华府", "公园道", "公园里"]),
        ("工业区", ["工厂", "工业区", "产业园", "物流园", "仓库"]),
        ("旅游景区", ["公园", "景区", "酒店", "度假村"]),
    ]

    matched = []
    for biz_type, keywords in rules:
        if any(kw in station_name for kw in keywords):
            # Avoid false positive: if "公园大地"/"公园华府" matched residential,
            # skip the broad "公园" match from tourism
            if biz_type == "旅游景区" and "公园" in station_name:
                if any(specific in station_name for specific in ["公园大地", "公园华府", "公园道", "公园里"]):
                    continue
            matched.append(biz_type)
    return matched


# ---------------------------------------------------------------------------
# Charger type extraction
# ---------------------------------------------------------------------------

def extract_charger_type(station_name):
    """
    Extract charger type (直流 / 交流) from station name.
    """
    if not isinstance(station_name, str):
        return None
    if "直流" in station_name or "快充" in station_name or "直流站" in station_name:
        return "直流"
    if "交流" in station_name or "慢充" in station_name or "交流桩" in station_name:
        return "交流"
    return None


# ---------------------------------------------------------------------------
# Grid-based region inference
# ---------------------------------------------------------------------------

def infer_region_from_grid(grid_code):
    """
    Infer Shenzhen district from grid code prefix.
    Example: L2NS01-XXX001 -> 南山区
    """
    if not isinstance(grid_code, str):
        return None
    grid_code = grid_code.strip()
    for prefix, region in GRID_PREFIX_MAP.items():
        if grid_code.startswith(prefix):
            return region
    return None
