"""
ChargeMind Phase 2: 时序聚合 + 区域均值填充

输入：
  - data/cleaned/stations_static.jsonl（阶段1静态数据）
  - /Users/xiasanw/work/2030数据/result_power_by_slot.csv（时序功率数据）

输出（两份）：
  - data/cleaned/stations_raw.jsonl    ← 原始版，缺失标记为 null
  - data/cleaned/stations.jsonl        ← Demo版，缺失字段用区域均值填充
"""

import json
import sys
from pathlib import Path
from collections import defaultdict, Counter
from statistics import mean

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(PROJECT_ROOT))

RAW_TS_PATH = Path("/Users/xiasanw/work/2030数据/result_power_by_slot.csv")
STATIC_PATH = PROJECT_ROOT / "data" / "cleaned" / "stations_static.jsonl"
OUTPUT_RAW = PROJECT_ROOT / "data" / "cleaned" / "stations_raw.jsonl"
OUTPUT_DEMO = PROJECT_ROOT / "data" / "cleaned" / "stations.jsonl"
OUTPUT_SUMMARY = PROJECT_ROOT / "data" / "cleaned" / "stations_summary.csv"

SEASON_DATES = {
    "spring_festival": [
        "2025-01-27", "2025-01-28", "2025-01-29", "2025-01-30", "2025-01-31",
        "2025-02-01", "2025-02-02", "2025-02-03", "2025-02-04",
    ],
    "summer": [
        "2025-06-30", "2025-07-01", "2025-07-02", "2025-07-03",
        "2025-07-04", "2025-07-05", "2025-07-06", "2025-07-07",
    ],
    "national_day": [
        "2025-09-29", "2025-09-30", "2025-10-01", "2025-10-02", "2025-10-03",
    ],
    "winter": [
        "2025-12-15", "2025-12-16", "2025-12-17", "2025-12-18",
        "2025-12-19", "2025-12-20", "2025-12-21", "2025-12-22",
    ],
}


def load_static_data():
    print("[1/7] Loading static data ...")
    with open(STATIC_PATH, "r", encoding="utf-8") as f:
        stations = [json.loads(line) for line in f]
    print(f"      Loaded {len(stations):,} stations")
    return stations


def load_timeseries():
    print("[2/7] Loading timeseries data ...")
    df = pd.read_csv(
        RAW_TS_PATH,
        encoding="utf-8-sig",
        dtype={"运营商编号": str, "场站编号": str},
    )
    df.columns = [
        "operator_id", "station_id", "date", "hour",
        "power_lt_30kw", "power_30_120kw",
        "power_120_360kw", "power_gte_360kw", "total_power",
    ]
    df["station_id"] = df["station_id"].astype(str).str.strip()
    print(f"      Loaded {len(df):,} rows, {df['station_id'].nunique():,} unique stations")
    return df


def compute_station_metrics(df_ts, installed_power_map):
    print("[3/7] Computing metrics per station ...")
    results = {}
    grouped = df_ts.groupby("station_id")
    total = len(grouped)

    for idx, (station_id, group) in enumerate(grouped, 1):
        if idx % 1000 == 0 or idx == total:
            print(f"      Progress: {idx}/{total} stations ...")

        installed = installed_power_map.get(station_id)

        # 日充电量
        daily_energy = group.groupby("date")["total_power"].sum()
        avg_daily_energy = round(daily_energy.mean(), 2)

        # 利用率（每小时功率 / 装机功率）
        # 注：若 total_installed_power 偏小会导致利用率 >1，此时做截断
        avg_utilization = None
        if installed and installed > 0:
            hourly_util = (group["total_power"] / installed).clip(upper=1.0)
            avg_utilization = round(hourly_util.mean(), 4)

        # 高峰/低谷时段
        hourly_avg = group.groupby("hour")["total_power"].mean()
        peak_hour = str(hourly_avg.idxmax())
        valley_hour = str(hourly_avg.idxmin())

        # 分季统计
        season_stats = {}
        for season_name, dates in SEASON_DATES.items():
            season_data = group[group["date"].isin(dates)]
            if len(season_data) == 0:
                continue
            season_daily = season_data.groupby("date")["total_power"].sum()
            season_avg_energy = round(season_daily.mean(), 2)
            season_avg_util = None
            if installed and installed > 0:
                season_avg_util = round(
                    (season_data["total_power"] / installed).clip(upper=1.0).mean(), 4
                )
            season_stats[season_name] = {
                "avg_daily_energy_kwh": season_avg_energy,
                "avg_utilization": season_avg_util,
            }

        results[station_id] = {
            "avg_daily_energy_kwh": avg_daily_energy,
            "avg_utilization": avg_utilization,
            "peak_hour": peak_hour,
            "valley_hour": valley_hour,
            "season_stats": season_stats,
        }

    print(f"      Computed metrics for {len(results):,} stations")
    return results


def merge_metrics(stations, metrics):
    print("[4/7] Merging metrics into static data ...")
    for station in stations:
        sid = station["station_id"]
        if sid in metrics:
            station["avg_daily_energy_kwh"] = metrics[sid]["avg_daily_energy_kwh"]
            station["avg_utilization"] = metrics[sid]["avg_utilization"]
            station["peak_hour"] = metrics[sid]["peak_hour"]
            station["valley_hour"] = metrics[sid]["valley_hour"]
            station["season_stats"] = metrics[sid]["season_stats"]
            station["has_timeseries_data"] = True
        else:
            station["avg_daily_energy_kwh"] = None
            station["avg_utilization"] = None
            station["peak_hour"] = None
            station["valley_hour"] = None
            station["season_stats"] = None
            station["has_timeseries_data"] = False
    return stations


def _mode(lst):
    if not lst:
        return None
    c = Counter(lst)
    return c.most_common(1)[0][0]


def _compute_avg_entry(entries, min_samples=1):
    """计算一组场站的均值（众数用于时段）"""
    if len(entries) < min_samples:
        return None

    valid_energy = [e["avg_daily_energy_kwh"] for e in entries if e["avg_daily_energy_kwh"] is not None]
    valid_util = [e["avg_utilization"] for e in entries if e["avg_utilization"] is not None]
    valid_peak = [e["peak_hour"] for e in entries if e["peak_hour"] is not None]
    valid_valley = [e["valley_hour"] for e in entries if e["valley_hour"] is not None]

    # season_stats: 合并所有场站的同季节数据
    season_combined = defaultdict(lambda: {"energies": [], "utils": []})
    for e in entries:
        ss = e.get("season_stats") or {}
        for season, vals in ss.items():
            if vals.get("avg_daily_energy_kwh") is not None:
                season_combined[season]["energies"].append(vals["avg_daily_energy_kwh"])
            if vals.get("avg_utilization") is not None:
                season_combined[season]["utils"].append(vals["avg_utilization"])

    season_avg = {}
    for season, vals in season_combined.items():
        season_avg[season] = {
            "avg_daily_energy_kwh": round(mean(vals["energies"]), 2) if vals["energies"] else None,
            "avg_utilization": round(mean(vals["utils"]), 4) if vals["utils"] else None,
        }

    entry = {
        "avg_daily_energy_kwh": round(mean(valid_energy), 2) if valid_energy else None,
        "avg_utilization": round(mean(valid_util), 4) if valid_util else None,
        "peak_hour": _mode(valid_peak),
        "valley_hour": _mode(valid_valley),
        "season_stats": season_avg if season_avg else None,
    }
    return entry


def compute_regional_averages(stations, min_samples=1):
    print("[5/7] Computing regional averages ...")

    group_data = defaultdict(list)
    region_only_data = defaultdict(list)
    all_data = []

    for s in stations:
        if not s.get("has_timeseries_data"):
            continue
        region = s.get("region") or "未知"
        biz = tuple(sorted(s.get("business_type") or ()))

        entry = {
            "avg_daily_energy_kwh": s.get("avg_daily_energy_kwh"),
            "avg_utilization": s.get("avg_utilization"),
            "peak_hour": s.get("peak_hour"),
            "valley_hour": s.get("valley_hour"),
            "season_stats": s.get("season_stats"),
        }

        group_data[(region, biz)].append(entry)
        region_only_data[region].append(entry)
        all_data.append(entry)

    city_avg = _compute_avg_entry(all_data, min_samples=min_samples)

    regional_avgs = {}
    for key, entries in group_data.items():
        avg = _compute_avg_entry(entries, min_samples=min_samples)
        if avg:
            regional_avgs[key] = avg

    region_avgs_only = {}
    for region, entries in region_only_data.items():
        avg = _compute_avg_entry(entries, min_samples=min_samples)
        if avg:
            region_avgs_only[region] = avg

    print(f"      Regional+biz groups: {len(regional_avgs)}")
    print(f"      Region-only groups: {len(region_avgs_only)}")
    return regional_avgs, region_avgs_only, city_avg


def _is_empty_avg(avg_entry):
    if avg_entry is None:
        return True
    return all(
        v is None for k, v in avg_entry.items()
        if k not in ("season_stats",)
    )


def fill_missing(stations, regional_avgs, region_avgs_only, city_avg):
    print("[6/7] Filling missing metrics with regional averages ...")
    filled_count = 0

    for s in stations:
        if s.get("has_timeseries_data"):
            s["metrics_estimated"] = False
            continue

        region = s.get("region") or "未知"
        biz = tuple(sorted(s.get("business_type") or ()))

        avg_entry = regional_avgs.get((region, biz))
        source = f"regional_avg_{region}_{'_'.join(biz) if biz else 'all'}"

        if avg_entry is None or _is_empty_avg(avg_entry):
            avg_entry = region_avgs_only.get(region)
            source = f"regional_avg_{region}"

        if avg_entry is None or _is_empty_avg(avg_entry):
            avg_entry = city_avg
            source = "city_wide_avg"

        if avg_entry and not _is_empty_avg(avg_entry):
            s["avg_daily_energy_kwh"] = avg_entry["avg_daily_energy_kwh"]
            s["avg_utilization"] = avg_entry["avg_utilization"]
            s["peak_hour"] = avg_entry["peak_hour"]
            s["valley_hour"] = avg_entry["valley_hour"]
            s["season_stats"] = avg_entry.get("season_stats")
            s["metrics_estimated"] = True
            s["estimation_source"] = source
            filled_count += 1
        else:
            s["metrics_estimated"] = False

    print(f"      Filled {filled_count} stations with regional averages")
    return stations


def build_raw_version(stations):
    raw_stations = []
    for s in stations:
        raw = dict(s)
        if not raw.get("has_timeseries_data"):
            missing = []
            for field in ["avg_daily_energy_kwh", "avg_utilization", "peak_hour", "valley_hour", "season_stats"]:
                if raw.get(field) is None:
                    missing.append(field)
            raw["missing_fields"] = missing
            raw["data_quality_notes"] = "时序数据缺失，待课题组补充"
        else:
            raw["missing_fields"] = []
            raw["data_quality_notes"] = ""
        raw_stations.append(raw)
    return raw_stations


def save_jsonl(stations, path):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        for s in stations:
            f.write(json.dumps(s, ensure_ascii=False) + "\n")
    print(f"      Saved {len(stations):,} records -> {path}")


def build_summary(stations):
    print("[7/7] Building summary ...")
    has_ts = sum(1 for s in stations if s.get("has_timeseries_data"))
    estimated = sum(1 for s in stations if s.get("metrics_estimated"))

    summary = {
        "metric": [
            "total_stations",
            "with_timeseries_data",
            "metrics_estimated",
            "avg_daily_energy_available",
            "avg_utilization_available",
            "peak_hour_available",
            "season_stats_available",
        ],
        "value": [
            len(stations),
            has_ts,
            estimated,
            sum(1 for s in stations if s.get("avg_daily_energy_kwh") is not None),
            sum(1 for s in stations if s.get("avg_utilization") is not None),
            sum(1 for s in stations if s.get("peak_hour") is not None),
            sum(1 for s in stations if s.get("season_stats") is not None),
        ],
    }
    return pd.DataFrame(summary)


def main():
    print("=" * 60)
    print("ChargeMind Phase 2: Timeseries Aggregation + Regional Fill")
    print("=" * 60)

    stations = load_static_data()
    installed_power_map = {
        s["station_id"]: s.get("total_installed_power")
        for s in stations
    }

    df_ts = load_timeseries()
    metrics = compute_station_metrics(df_ts, installed_power_map)
    stations = merge_metrics(stations, metrics)

    # 原始版（未填充）
    raw_stations = build_raw_version(stations)
    save_jsonl(raw_stations, OUTPUT_RAW)

    # Demo版（区域均值填充）
    regional_avgs, region_avgs_only, city_avg = compute_regional_averages(stations)
    demo_stations = fill_missing([dict(s) for s in stations], regional_avgs, region_avgs_only, city_avg)
    save_jsonl(demo_stations, OUTPUT_DEMO)

    df_summary = build_summary(demo_stations)
    OUTPUT_SUMMARY.parent.mkdir(parents=True, exist_ok=True)
    df_summary.to_csv(OUTPUT_SUMMARY, index=False, encoding="utf-8-sig")
    print(f"      Saved summary -> {OUTPUT_SUMMARY}")

    print("=" * 60)
    print("Done.")
    print("=" * 60)


if __name__ == "__main__":
    main()