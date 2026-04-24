export type BusinessType = '住宅区' | '办公区' | '商业区' | '工业区' | '交通枢纽' | '旅游景区';

export interface StationProfile {
  station_name?: string;
  region?: string;
  business_type?: BusinessType[];
  total_installed_power?: number;
  pile_count?: number;
  monthly_rent?: number;
  staff_count?: number;
  avg_price?: number;
  peak_hour?: string;
  valley_hour?: string;
}

export interface ExtractRequest {
  user_input: string;
}

export interface ExtractResponse {
  profile: StationProfile;
  llm_used: boolean;
  error?: string;
}

export type QuestionType = 'text' | 'number' | 'select' | 'multiselect';

export interface NextQuestion {
  key: string;
  question: string;
  type: QuestionType;
  options?: string[];
}

export interface EnrichResponse {
  complete: boolean;
  next_question?: NextQuestion;
  missing_count: number;
  all_missing_keys?: string[];
}

export interface AlgorithmResult {
  predicted_utilization: number;
  annual_revenue: number;
  annual_cost: number;
  annual_profit: number;
  confidence: number;
  is_stub: boolean;
  note: string;
  breakdown?: Record<string, unknown>;
}

export interface SimilarStation {
  station_id: string;
  document: string;
  metadata: {
    station_name: string;
    region: string;
    business_type: string;
    total_installed_power: number;
    avg_utilization: number;
    avg_daily_energy_kwh: number;
    peak_hour: string;
    [key: string]: unknown;
  };
  similarity_score: number;
}

export interface RAGResult {
  similar_stations: SimilarStation[];
  analysis: string;
}

export interface ConflictItem {
  type: string;
  algorithm: string;
  rag: string;
  resolution: string;
}

export interface RecommendationItem {
  title: string;
  source: string;
  detail: string;
}

export interface ReportData {
  executive_summary: string;
  algorithm_prediction: AlgorithmResult;
  rag_analysis: string;
  conflicts: ConflictItem[];
  recommendations: RecommendationItem[];
}

export interface DiagnoseResponse {
  profile: StationProfile;
  algorithm: AlgorithmResult;
  rag: RAGResult;
  report: ReportData;
}

export type PageType = 'input' | 'enrich' | 'report';
