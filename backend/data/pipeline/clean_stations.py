"""
Main data cleaning script for Shenzhen charging station data.
"""
import json
import sys
from pathlib import Path
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(PROJECT_ROOT))

from backend.data.pipeline.utils import parse_fee, extract_charger_type, infer_business_type, infer_region_from_name, infer_region_from_grid, LAND_PROPERTY_MAP, STATION_STATUS_MAP, VEHICLE_TYPE_MAP

RAW_DIR = Path("/Users/xiasanw/work/2030数据")
CLEANED_DIR = PROJECT_ROOT / "data" / "cleaned"
BIASHEET1_PATH = RAW_DIR / "表1.xlsx"
B2_PATH = RAW_DIR / "b2.csv"
B4_PATH = RAW_DIR / "b4.csv"
GRID_PATH = RAW_DIR / "场站网格" / "b1_with_grid_strict_polygon.csv"
OUTPUT_JSONL = CLEANED_DIR / "stations_static.jsonl"
OUTPUT_SUMMARY = CLEANED_DIR / "stations_static_summary.csv"


def ensure_dir(path):
    path.parent.mkdir(parents=True, exist_ok=True)


def load_biao1():
    print("[1/6] Loading 表1.xlsx (sheet='biao1') ...")
    df = pd.read_excel(BIASHEET1_PATH, sheet_name="biao1", engine="openpyxl")
    # Normalize column names: strip whitespace and remove explanatory suffixes
    cleaned_cols = {}
    for c in df.columns:
        new_c = c.strip()
        if new_c.startswith("service_car_types"):
            new_c = "service_car_types"
        cleaned_cols[c] = new_c
    df = df.rename(columns=cleaned_cols)
    print(f"      Rows: {len(df):,}, Columns: {len(df.columns)}")
    return df


def load_b2():
    print("[2/6] Loading b2.csv ...")
    df = pd.read_csv(B2_PATH, encoding="utf-8-sig")
    print(f"      Rows: {len(df):,}, Columns: {len(df.columns)}")
    return df


def load_b4():
    print("[3/6] Loading b4.csv ...")
    df = pd.read_csv(B4_PATH, encoding="utf-8-sig")
    print(f"      Rows: {len(df):,}, Columns: {len(df.columns)}")
    return df


def _map_vehicle_types(val):
    if pd.isna(val):
        return []
    codes = str(val).split(",")
    labels = []
    for c in codes:
        c = c.strip()
        if c == "":
            continue
        try:
            code_int = int(float(c))
        except (ValueError, TypeError):
            continue
        label = VEHICLE_TYPE_MAP.get(code_int)
        if label:
            labels.append(label)
    return labels


def clean_biao1(df):
    print("[4/6] Cleaning biao1 ...")
    df = df.copy()
    df["operator_id"] = df["operator_id"].astype(str).str.strip()
    df["station_id"] = df["station_id"].astype(str).str.strip()
    if "land_property" in df.columns:
        df["land_property_desc"] = df["land_property"].map(LAND_PROPERTY_MAP)
    if "station_status" in df.columns:
        df["station_status_desc"] = df["station_status"].map(STATION_STATUS_MAP)
    if "service_car_types" in df.columns:
        df["service_car_types_desc"] = df["service_car_types"].apply(
            lambda x: _map_vehicle_types(x)
        )
    print(f"      Unique stations after cleaning: {df['station_id'].nunique():,}")
    return df


def clean_b2(df):
    print("      Cleaning b2 ...")
    df = df.copy()
    df["operator_id"] = df["operator_id"].astype(str).str.strip()
    df["station_id"] = df["station_id"].astype(str).str.strip()
    if "electricity_fee" in df.columns:
        df["electricity_fee_parsed"] = df["electricity_fee"].apply(parse_fee)
    if "service_fee" in df.columns:
        df["service_fee_parsed"] = df["service_fee"].apply(parse_fee)
    if "station_name" in df.columns:
        df["charger_type"] = df["station_name"].apply(extract_charger_type)
    else:
        df["charger_type"] = None
    # Fix: fill empty busine_hours with default
    if "busine_hours" in df.columns:
        df["busine_hours"] = df["busine_hours"].fillna("00:00~24:00")
    return df


def clean_b4(df):
    print("      Cleaning b4 (aggregating by station_id) ...")
    df = df.copy()
    df["station_id"] = df["station_id"].astype(str).str.strip()
    numeric_cols = df.select_dtypes(include=["number"]).columns.tolist()
    if "station_id" in numeric_cols:
        numeric_cols.remove("station_id")
    agg_dict = {col: "sum" for col in numeric_cols}
    if "operator_id" in df.columns:
        df["operator_id"] = df["operator_id"].astype(str).str.strip()
        agg_dict["operator_id"] = "first"
    grouped = df.groupby("station_id", as_index=False).agg(agg_dict)
    print(f"      Rows after aggregation: {len(grouped):,}")
    return grouped


def deduplicate_by_station_id(df, source_name):
    """按 station_id 去重，保留字段最完整的行"""
    before = len(df)
    # 计算每行的非空字段数
    df = df.copy()
    df["_non_null_count"] = df.notna().sum(axis=1)
    # 按 station_id 分组，保留非空字段最多的行
    df = df.sort_values("_non_null_count", ascending=False, kind="mergesort").drop_duplicates("station_id", keep="first")
    df = df.drop(columns=["_non_null_count"])
    after = len(df)
    print(f"      Deduplicated {source_name}: {before:,} -> {after:,} (removed {before-after:,})")
    return df


def merge_dataframes(df1, df2, df4):
    print("[5/6] Merging dataframes ...")
    
    # 去重
    df1 = deduplicate_by_station_id(df1, "biao1")
    df2 = deduplicate_by_station_id(df2, "b2")
    
    b2_cols = ["station_id", "electricity_fee_parsed", "service_fee_parsed",
               "busine_hours", "charger_type"]
    b2_cols = [c for c in b2_cols if c in df2.columns]
    df_merged = df1.merge(df2[b2_cols], on="station_id", how="left")
    b4_cols = [c for c in df4.columns if c not in df1.columns or c == "station_id"]
    df_merged = df_merged.merge(df4[b4_cols], on="station_id", how="left")
    print(f"      Final rows: {len(df_merged):,}, Unique station_ids: {df_merged['station_id'].nunique():,}")
    return df_merged


def load_grid_data():
    print("[3.5/6] Loading grid association data ...")
    df = pd.read_csv(GRID_PATH, encoding="utf-8-sig")
    df["station_id"] = df["station_id"].astype(str).str.strip()
    # Keep only needed columns
    cols = ["station_id", "所属网格编号"]
    cols = [c for c in cols if c in df.columns]
    df = df[cols].rename(columns={"所属网格编号": "grid_code"})
    print(f"      Rows: {len(df):,}, Unique stations: {df['station_id'].nunique():,}")
    return df


def add_inferred_fields(df, df_grid=None):
    print("      Adding inferred fields ...")
    df = df.copy()
    if "station_name" in df.columns:
        df["region_from_name"] = df["station_name"].apply(infer_region_from_name)
        df["business_type"] = df["station_name"].apply(infer_business_type)
    
    # Add region from grid data as fallback/primary
    if df_grid is not None and "grid_code" in df_grid.columns:
        # Deduplicate grid data to avoid multiplying rows
        df_grid_dedup = df_grid.drop_duplicates("station_id", keep="first")
        df = df.merge(df_grid_dedup[["station_id", "grid_code"]], on="station_id", how="left")
        df["region_from_grid"] = df["grid_code"].apply(infer_region_from_grid)
        # Use name-inferred region first, then grid-inferred
        df["region"] = df["region_from_name"].fillna(df["region_from_grid"])
        # Clean up temp columns
        df = df.drop(columns=["region_from_name", "region_from_grid"], errors="ignore")
    else:
        df["region"] = df.get("region_from_name")
        if "region_from_name" in df.columns:
            df = df.drop(columns=["region_from_name"])
    
    # Validate coordinates (Shenzhen bounding box: lng 113.7-114.8, lat 22.4-22.9)
    if "station_lng" in df.columns and "station_lat" in df.columns:
        invalid_coord = (
            (df["station_lng"] < 113.7) | (df["station_lng"] > 114.8) |
            (df["station_lat"] < 22.4) | (df["station_lat"] > 22.9)
        )
        df.loc[invalid_coord, "station_lng"] = None
        df.loc[invalid_coord, "station_lat"] = None
    
    return df


def _clean_for_json(obj):
    """Recursively replace NaN/Inf with None for JSON serialization."""
    if isinstance(obj, dict):
        return {k: _clean_for_json(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [_clean_for_json(item) for item in obj]
    elif isinstance(obj, float):
        if obj != obj or obj == float("inf") or obj == float("-inf"):
            return None
        return obj
    return obj


def build_summary(df):
    print("[6/6] Building summary ...")
    summary = {
        "metric": [],
        "value": [],
    }
    summary["metric"].append("total_stations")
    summary["value"].append(len(df))
    summary["metric"].append("unique_station_ids")
    summary["value"].append(df["station_id"].nunique())
    summary["metric"].append("with_electricity_fee")
    summary["value"].append(df["electricity_fee_parsed"].notna().sum())
    summary["metric"].append("with_service_fee")
    summary["value"].append(df["service_fee_parsed"].notna().sum())
    summary["metric"].append("with_busine_hours")
    summary["value"].append(df["busine_hours"].notna().sum())
    summary["metric"].append("with_charger_type")
    summary["value"].append(df["charger_type"].notna().sum())
    summary["metric"].append("with_region")
    summary["value"].append(df["region"].notna().sum())
    summary["metric"].append("with_business_type")
    summary["value"].append(df["business_type"].apply(lambda x: bool(x) if isinstance(x, list) else False).sum())
    if "total_power" in df.columns:
        summary["metric"].append("total_power_sum_kw")
        summary["value"].append(round(df["total_power"].sum(), 2))
    if "total_installed_power" in df.columns:
        summary["metric"].append("total_installed_power_sum_kw")
        summary["value"].append(round(df["total_installed_power"].sum(), 2))
    return pd.DataFrame(summary)


def main():
    print("=" * 60)
    print("Shenzhen Charging Station Data Cleaning Pipeline")
    print("=" * 60)

    # Load
    df_biao1 = load_biao1()
    df_b2 = load_b2()
    df_b4 = load_b4()
    df_grid = load_grid_data()

    # Clean
    df_biao1 = clean_biao1(df_biao1)
    df_b2 = clean_b2(df_b2)
    df_b4 = clean_b4(df_b4)

    # Merge
    df_merged = merge_dataframes(df_biao1, df_b2, df_b4)

    # Infer
    df_merged = add_inferred_fields(df_merged, df_grid)

    # Ensure output directory exists
    ensure_dir(OUTPUT_JSONL)
    ensure_dir(OUTPUT_SUMMARY)

    # Save JSONL
    print(f"Saving JSONL -> {OUTPUT_JSONL}")
    records = df_merged.to_dict(orient="records")
    with open(OUTPUT_JSONL, "w", encoding="utf-8") as f:
        for rec in records:
            clean_rec = _clean_for_json(rec)
            f.write(json.dumps(clean_rec, ensure_ascii=False) + "\n")
    print(f"      Written {len(records):,} records.")

    # Save summary
    df_summary = build_summary(df_merged)
    print(f"Saving summary -> {OUTPUT_SUMMARY}")
    df_summary.to_csv(OUTPUT_SUMMARY, index=False, encoding="utf-8-sig")
    print(f"      Written {len(df_summary):,} summary rows.")

    print("=" * 60)
    print("Done.")
    print("=" * 60)


if __name__ == "__main__":
    main()
