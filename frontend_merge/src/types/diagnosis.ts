import type { DiagnosisResult } from './dashboard';

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

// ── 后端 /diagnose 实际返回结构（v1）──

export interface RerankInfo {
  used: boolean;
  method: string;
  grid_priority: boolean;
  same_grid_count?: number;
  candidate_count?: number;
  selected_count?: number;
  error?: string;
}

export interface RAGResult {
  similar_stations: Array<Record<string, unknown>>;
  rerank_info: RerankInfo;
}

export interface DiagnoseResponse {
  profile: StationProfile;
  report: DiagnosisResult;
  rag: RAGResult;
}

export type PageType = 'landing' | 'input' | 'enrich' | 'report';
