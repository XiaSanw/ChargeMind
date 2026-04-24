export interface RadarItem {
  score: number;
  comment: string;
}

export interface RadarData {
  位置价值: RadarItem;
  硬件配置: RadarItem;
  运营效率: RadarItem;
  收益能力: RadarItem;
  竞争格局: RadarItem;
  增长潜力: RadarItem;
}

export interface Dashboard {
  headline: string;
  overall_score: number;
  radar: RadarData;
  scoring_logic: string;
}

export interface KPICardData {
  label: string;
  value: string;
  trend: 'up' | 'down' | 'flat';
  benchmark: string;
  detail: string;
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

export interface TrendScenario {
  name: string;
  values: number[];
  description: string;
}

export interface TrendProjection {
  months: number[];
  scenarios: TrendScenario[];
}

export interface PathItem {
  title: string;
  category: string;
  annual_gain: number;
  probability: number;
  effort: 'low' | 'medium' | 'high';
  source: string;
  detail: string;
}

export interface DiagnosisResult {
  dashboard: Dashboard;
  kpi_cards: KPICardData[];
  benchmark: Benchmark;
  trend_projection: TrendProjection;
  paths: PathItem[];
  detail_text: string;
}
