import type { DiagnoseResponse } from '@/types/diagnosis';
import type { DiagnosisResult } from '@/types/dashboard';

/**
 * 将后端 diagnose API 返回的数据，映射为前端 DiagnosisResult 结构。
 * 
 * 后端 v1 已经算好所有分析模块，前端只需直接取用 report 字段。
 * 此函数保留用于：字段兜底、缺失值填充、未来格式兼容。
 */
export function adaptLegacyToDashboard(response: DiagnoseResponse): DiagnosisResult {
  const report = response.report;

  return {
    ...report,
    // 兜底：LLM 增强层可能缺失
    llm_enhancement: report.llm_enhancement || {
      headline_refined: report.dashboard.headline,
      anomalies: [],
      trend_outlook: '暂无趋势判断',
      path_suggestions: [],
    },
    // 兜底：detail_text
    detail_text: report.detail_text || '',
  };
}
