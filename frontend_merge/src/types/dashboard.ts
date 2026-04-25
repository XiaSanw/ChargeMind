// 后端 report JSON 直接映射 —— 后端已算好，前端只做展示

export interface RadarItem {
  score: number;
  comment: string;
  trust: string;       // ⭐⭐⭐ / ⭐⭐ / ⭐ / ⚠️
  sector_avg: number;  // 同区域均值参考线
}

export interface RadarData {
  地段禀赋: RadarItem;
  硬件适配: RadarItem;
  定价精准: RadarItem;
  运营产出: RadarItem;
  需求饱和度: RadarItem;
}

export interface DashboardWarning {
  type: string;
  severity: 'high' | 'medium' | 'low';
  message: string;
}

export interface Dashboard {
  headline: string;
  overall_score: number;
  title: string;           // 趣味称号
  title_reason: string;    // 称号依据
  radar: RadarData;
  scoring_logic: string;
  sector_avg: Record<string, number> | null;
  scoring_reasoning: Record<string, string> | null;
  warnings: DashboardWarning[];
  kpi_summary?: string;    // LLM 基于4个KPI的一句话综合分析
}

export interface KPICardData {
  label: string;
  value: string;
  trend: 'up' | 'down' | 'flat';
  benchmark: string;
  detail: string;
  trust: string;  // ⭐⭐⭐ / ⭐⭐ / ⭐
}

export interface BenchmarkMetric {
  key: string;
  name: string;
  unit: string;
  values: number[];
}

export interface Benchmark {
  labels: string[];
  metrics: BenchmarkMetric[];
  selected_metric: string;
}

export interface PathItem {
  title: string;
  category: string;
  annual_gain: number | null;  // null = 无精确收益模型
  effort: 'low' | 'medium' | 'high';
  trust: string;               // ⭐⭐⭐ / ⭐⭐ / ⭐
  calculation: string | null;  // 透明公式
  detail: string;
}

// ── #8 竞品价格对标 ──

export interface PriceBenchmark {
  title: string;
  my_prices: {
    min: number | null;
    avg: number | null;
    max: number | null;
  };
  benchmark_prices: {
    min: number | null;
    avg: number | null;
    max: number | null;
  };
  gaps: {
    min_gap_pct: number | null;
    avg_gap_pct: number | null;
    max_gap_pct: number | null;
  };
  spread_ratio: number | null;          // 本场站峰谷比
  benchmark_spread_ratio: number | null; // 竞品峰谷比
  confidence: string;
  note: string;
}

// ── 季节波动 ──

export interface SeasonalData {
  title: string;
  seasons: Record<string, number>;
  peak_season: string;
  trough_season: string;
  max_change_pct: number;
  season_changes: string[];
  trend_hint_for_llm: string;
  confidence: string;
}

// ── LLM 叙事包装 ──

export interface AnomalyItem {
  type: string;
  description: string;
  severity: '高' | '中' | '低';
}

export interface PathSuggestion {
  title: string;
  rationale: string;
}

export interface LLMEnhancement {
  headline_refined: string;
  anomalies: AnomalyItem[];
  trend_outlook: string;  // 方向性判断，禁止数字
  path_suggestions: PathSuggestion[];
}

// ── 完整诊断结果（直接对应后端 report 字段）──

export interface DiagnosisResult {
  dashboard: Dashboard;
  kpi_cards: KPICardData[];
  power_mismatch: Record<string, unknown>;
  brand_analysis: Record<string, unknown>;
  competitive_position: Record<string, unknown>;
  price_benchmark_result: {
    station_id: string;
    station_name: string;
    grid_code: string | null;
    competitor_count: number;
    price_benchmark: PriceBenchmark;
  };
  benchmark_stations: Array<Record<string, unknown>>;
  seasonal: SeasonalData;
  paths: PathItem[];
  llm_enhancement?: LLMEnhancement;  // LLM 可用时才有
  detail_text: string;
}
