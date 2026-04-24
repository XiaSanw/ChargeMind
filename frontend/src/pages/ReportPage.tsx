import { useMemo, useCallback } from 'react';
import { useDiagnosis } from '@/store/DiagnosisContext';
import { adaptLegacyToDashboard } from '@/lib/adaptLegacyToDashboard';
import Headline from '@/components/dashboard/Headline';
import StationRadarChart from '@/components/dashboard/RadarChart';
import KPICards from '@/components/dashboard/KPICards';
import BenchmarkChart from '@/components/dashboard/BenchmarkChart';
import TrendChart from '@/components/dashboard/TrendChart';
import PathCards from '@/components/dashboard/PathCards';
import DetailSection from '@/components/dashboard/DetailSection';

function LoadingOverlay() {
  const phases = [
    '正在解析场站画像...',
    '算法 Stub 预测收益中...',
    'RAG 检索相似场站...',
    '生成仪表盘数据...',
  ];

  return (
    <div className="min-h-screen flex flex-col items-center justify-center px-4">
      <div className="text-center space-y-6 max-w-md">
        <div className="relative inline-flex items-center justify-center">
          <div className="absolute w-20 h-20 rounded-full border-2 border-primary/20" />
          <div className="absolute w-20 h-20 rounded-full border-2 border-transparent border-t-primary animate-spin" />
          <div className="w-12 h-12 rounded-full bg-primary/10 flex items-center justify-center">
            <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-primary">
              <path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z" />
            </svg>
          </div>
        </div>
        <div className="space-y-2">
          <h2 className="text-xl font-semibold">双引擎诊断中...</h2>
          <p className="text-sm text-muted-foreground animate-pulse">
            {phases[Math.floor(Date.now() / 2500) % phases.length]}
          </p>
        </div>
        <div className="h-1.5 rounded-full bg-secondary overflow-hidden">
          <div className="h-full rounded-full bg-primary animate-pulse" style={{ width: '60%' }} />
        </div>
      </div>
    </div>
  );
}

export default function ReportPage() {
  const { diagnoseResult, isDiagnosing, error, reset, setError } = useDiagnosis();

  const handleRetry = useCallback(() => {
    setError(null);
    reset();
  }, [setError, reset]);

  // 将后端返回的旧格式数据适配为新仪表盘格式
  const dashboardData = useMemo(() => {
    if (!diagnoseResult) return null;
    try {
      return adaptLegacyToDashboard(diagnoseResult);
    } catch (e) {
      console.error('适配仪表盘数据失败:', e);
      return null;
    }
  }, [diagnoseResult]);

  if (isDiagnosing) {
    return <LoadingOverlay />;
  }

  if (error) {
    return (
      <div className="min-h-screen flex flex-col items-center justify-center px-4">
        <div className="text-center space-y-4 max-w-md">
          <div className="inline-flex items-center justify-center w-14 h-14 rounded-full bg-red-500/10">
            <svg xmlns="http://www.w3.org/2000/svg" width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-red-400">
              <circle cx="12" cy="12" r="10" />
              <line x1="15" x2="9" y1="9" y2="15" />
              <line x1="9" x2="15" y1="9" y2="15" />
            </svg>
          </div>
          <h2 className="text-xl font-semibold">诊断出错</h2>
          <p className="text-muted-foreground">{error}</p>
          <button
            onClick={handleRetry}
            className="inline-flex items-center gap-2 rounded-xl bg-primary px-6 py-2.5 text-sm font-semibold text-primary-foreground hover:bg-primary/90 transition-all"
          >
            重新诊断
          </button>
        </div>
      </div>
    );
  }

  if (!dashboardData) {
    return (
      <div className="min-h-screen flex flex-col items-center justify-center px-4">
        <div className="text-center space-y-4">
          <h2 className="text-xl font-semibold">暂无诊断结果</h2>
          <p className="text-muted-foreground">请先完成场站信息录入</p>
          <button
            onClick={reset}
            className="inline-flex items-center gap-2 rounded-xl bg-primary px-6 py-2.5 text-sm font-semibold text-primary-foreground hover:bg-primary/90 transition-all"
          >
            开始诊断
          </button>
        </div>
      </div>
    );
  }

  const { dashboard, kpi_cards, benchmark, trend_projection, paths, detail_text } = dashboardData;

  return (
    <div className="min-h-screen px-4 py-8 md:py-12">
      <div className="mx-auto max-w-5xl space-y-8">
        {/* Header */}
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
          <div>
            <h1 className="text-2xl md:text-3xl font-bold">🏥 场站体检报告</h1>
            <p className="text-muted-foreground mt-1 text-sm">
              算法硬数据 × LLM 泛化直觉 · 双引擎交叉校验
            </p>
          </div>
          <button
            onClick={reset}
            className="inline-flex items-center gap-2 self-start rounded-xl border border-border bg-card px-4 py-2 text-sm font-medium hover:bg-secondary transition-all"
          >
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M3 12a9 9 0 1 0 9-9 9.75 9.75 0 0 0-6.74 2.74L3 8" />
              <path d="M3 3v5h5" />
            </svg>
            重新诊断
          </button>
        </div>

        {/* Headline */}
        <Headline text={dashboard.headline} />

        {/* Radar + KPI */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="rounded-2xl border border-border bg-card p-6">
            <h3 className="text-lg font-semibold mb-4">六维评估</h3>
            <StationRadarChart data={dashboard.radar} overallScore={dashboard.overall_score} />
            <p className="text-xs text-muted-foreground text-center mt-2">
              {dashboard.scoring_logic}
            </p>
          </div>
          <div className="rounded-2xl border border-border bg-card p-6">
            <h3 className="text-lg font-semibold mb-4">关键指标</h3>
            <KPICards cards={kpi_cards} />
          </div>
        </div>

        {/* Benchmark */}
        <BenchmarkChart benchmark={benchmark} />

        {/* Trend */}
        <TrendChart data={trend_projection} />

        {/* Paths */}
        <PathCards paths={paths} />

        {/* Detail */}
        <DetailSection content={detail_text} />

        {/* Footer */}
        <p className="text-center text-xs text-muted-foreground pb-8">
          ChargeMind Demo · 数据来源：算法 Stub + RAG 知识库（{diagnoseResult?.rag.similar_stations.length || 0} 个相似场站）
        </p>
      </div>
    </div>
  );
}
