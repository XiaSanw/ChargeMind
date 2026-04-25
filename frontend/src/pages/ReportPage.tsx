import { useMemo, useCallback } from 'react';
import { useDiagnosis } from '@/store/DiagnosisContext';
import { adaptLegacyToDashboard } from '@/lib/adaptLegacyToDashboard';
import Headline from '@/components/dashboard/Headline';
import StationRadarChart from '@/components/dashboard/RadarChart';
import KPICards from '@/components/dashboard/KPICards';

import PathCards from '@/components/dashboard/PathCards';
import DetailSection from '@/components/dashboard/DetailSection';
import PowerMismatchCard from '@/components/dashboard/PowerMismatchCard';
import BrandAnalysisCard from '@/components/dashboard/BrandAnalysisCard';
import CompetitivePositionCard from '@/components/dashboard/CompetitivePositionCard';

function LoadingOverlay() {
  const phases = [
    '正在解析场站画像...',
    '算法硬算分析中...',
    'RAG 检索相似场站...',
    'LLM 叙事包装中...',
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

  // 将后端返回的数据适配为前端仪表盘格式
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

  const {
    dashboard,
    kpi_cards,
    benchmark_stations,
    price_benchmark_result,
    seasonal,
    llm_enhancement,
    paths,
    detail_text,
  } = dashboardData;

  const pb = price_benchmark_result?.price_benchmark;

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

        {/* Warnings */}
        {dashboard.warnings.length > 0 && (
          <div className="space-y-2">
            {dashboard.warnings.map((w, i) => (
              <div
                key={i}
                className={`rounded-xl px-4 py-3 text-sm font-medium ${
                  w.severity === 'high'
                    ? 'bg-red-500/10 text-red-400 border border-red-500/20'
                    : 'bg-amber-500/10 text-amber-400 border border-amber-500/20'
                }`}
              >
                {w.message}
              </div>
            ))}
          </div>
        )}

        {/* Headline（一句话痛点诊断） */}
        <Headline text={dashboard.headline} />

        {/* 称号展示（位于雷达图卡片外侧上方） */}
        {dashboard.title && (
          <div className="text-center mb-2">
            <span className="inline-block px-4 py-1.5 rounded-full bg-primary/10 text-primary text-lg font-bold">
              {dashboard.title}
            </span>
            <p className="text-sm text-muted-foreground mt-1">{dashboard.title_reason}</p>
          </div>
        )}

        {/* Radar + KPI */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="rounded-2xl border border-border bg-card p-6">
            <StationRadarChart data={dashboard.radar} />
            <p className="text-xs text-muted-foreground text-center mt-2">
              {dashboard.scoring_logic}
            </p>
          </div>
          <div className="rounded-2xl border border-border bg-card p-6">
            <h3 className="text-lg font-semibold mb-4">关键指标</h3>
            <KPICards cards={kpi_cards} />
          </div>
        </div>

        {/* 功率错配 + 品牌分析 + 竞争定位 */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <PowerMismatchCard data={dashboardData.power_mismatch} />
          <BrandAnalysisCard data={dashboardData.brand_analysis} />
          <CompetitivePositionCard data={dashboardData.competitive_position} />
        </div>

        {/* 竞品价格对标 */}
        {pb && pb.my_prices?.avg !== null && (
          <div className="rounded-2xl border border-border bg-card p-6 space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-lg font-semibold">💰 竞品价格对标</h3>
              <span className="text-xs text-muted-foreground">{pb.confidence}</span>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {/* min */}
              <div className="rounded-xl bg-secondary/30 p-4 text-center">
                <div className="text-xs text-muted-foreground mb-1">低谷价格</div>
                <div className="text-xl font-bold">¥{pb.my_prices.min}/度</div>
                <div className="text-xs text-muted-foreground mt-1">
                  竞品 ¥{pb.benchmark_prices.min}/度
                  {pb.gaps.min_gap_pct !== null && (
                    <span className={pb.gaps.min_gap_pct > 0 ? 'text-red-400' : 'text-emerald-400'}>
                      {' '}{pb.gaps.min_gap_pct > 0 ? '+' : ''}{pb.gaps.min_gap_pct}%
                    </span>
                  )}
                </div>
              </div>
              {/* avg */}
              <div className="rounded-xl bg-secondary/30 p-4 text-center">
                <div className="text-xs text-muted-foreground mb-1">全天均价</div>
                <div className="text-xl font-bold">¥{pb.my_prices.avg}/度</div>
                <div className="text-xs text-muted-foreground mt-1">
                  竞品 ¥{pb.benchmark_prices.avg}/度
                  {pb.gaps.avg_gap_pct !== null && (
                    <span className={pb.gaps.avg_gap_pct > 0 ? 'text-red-400' : 'text-emerald-400'}>
                      {' '}{pb.gaps.avg_gap_pct > 0 ? '+' : ''}{pb.gaps.avg_gap_pct}%
                    </span>
                  )}
                </div>
              </div>
              {/* max */}
              <div className="rounded-xl bg-secondary/30 p-4 text-center">
                <div className="text-xs text-muted-foreground mb-1">高峰价格</div>
                <div className="text-xl font-bold">¥{pb.my_prices.max}/度</div>
                <div className="text-xs text-muted-foreground mt-1">
                  竞品 ¥{pb.benchmark_prices.max}/度
                  {pb.gaps.max_gap_pct !== null && (
                    <span className={pb.gaps.max_gap_pct > 0 ? 'text-red-400' : 'text-emerald-400'}>
                      {' '}{pb.gaps.max_gap_pct > 0 ? '+' : ''}{pb.gaps.max_gap_pct}%
                    </span>
                  )}
                </div>
              </div>
            </div>
            <div className="flex items-center justify-between text-xs text-muted-foreground">
              <span>本场站峰谷比: {pb.spread_ratio || 'N/A'}</span>
              <span>竞品峰谷比: {pb.benchmark_spread_ratio || 'N/A'}</span>
            </div>
            {pb.note && <p className="text-xs text-muted-foreground">{pb.note}</p>}
          </div>
        )}

        {/* 季节趋势 */}
        {'error' in seasonal === false && seasonal.peak_season && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="rounded-2xl border border-border bg-card p-6 space-y-3">
              <div className="flex items-center justify-between">
                <h3 className="text-lg font-semibold">📊 季节波动</h3>
                <span className="text-xs text-muted-foreground">{seasonal.confidence}</span>
              </div>
              <div className="space-y-2">
                {seasonal.season_changes?.map((change, i) => (
                  <div key={i} className="text-sm text-foreground">{change}</div>
                ))}
              </div>
              <div className="text-xs text-muted-foreground">
                峰值: {seasonal.peak_season} · 谷值: {seasonal.trough_season} · 最大波动: {seasonal.max_change_pct}%
              </div>
            </div>
            {llm_enhancement?.trend_outlook && (
              <div className="rounded-2xl border border-border bg-card p-6 space-y-3">
                <h3 className="text-lg font-semibold">📈 趋势方向</h3>
                <p className="text-sm text-foreground leading-relaxed">{llm_enhancement.trend_outlook}</p>
                <p className="text-xs text-muted-foreground">基于季节数据的 LLM 方向性判断（非精确预测）</p>
              </div>
            )}
          </div>
        )}

        {/* 相似场站 */}
        {benchmark_stations && benchmark_stations.length > 0 && (
          <div className="rounded-2xl border border-border bg-card p-6 space-y-4">
            <h3 className="text-lg font-semibold">🔍 相似场站 ({benchmark_stations.length}个)</h3>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
              {benchmark_stations.slice(0, 6).map((s, i) => {
                const meta = (s as Record<string, unknown>).metadata as Record<string, unknown> | undefined;
                return (
                  <div key={i} className="rounded-lg border border-border bg-card p-3 text-sm">
                    <div className="font-medium">{(meta?.station_name as string) || '未命名'}</div>
                    <div className="text-xs text-muted-foreground mt-1">
                      {(meta?.region as string) || ''} · {(meta?.business_type as string) || ''}
                    </div>
                    <div className="text-xs text-muted-foreground mt-1">
                      可信度: {(s as Record<string, unknown>).trust as string || '⭐⭐'}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* Paths */}
        <PathCards paths={paths} />

        {/* LLM 异常识别 */}
        {llm_enhancement?.anomalies && llm_enhancement.anomalies.length > 0 && (
          <div className="rounded-2xl border border-border bg-card p-6 space-y-3">
            <h3 className="text-lg font-semibold">⚠️ 异常识别</h3>
            <div className="space-y-2">
              {llm_enhancement.anomalies.map((a, i) => (
                <div
                  key={i}
                  className={`rounded-lg px-3 py-2 text-sm flex items-center gap-2 ${
                    a.severity === '高'
                      ? 'bg-red-500/10 text-red-400'
                      : a.severity === '中'
                      ? 'bg-amber-500/10 text-amber-400'
                      : 'bg-blue-500/10 text-blue-400'
                  }`}
                >
                  <span className="font-medium">{a.type}</span>
                  <span className="text-muted-foreground">{a.description}</span>
                  <span className="text-xs opacity-70 ml-auto">{a.severity}</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Detail */}
        <DetailSection content={detail_text} />

        {/* Footer */}
        <p className="text-center text-xs text-muted-foreground pb-8">
          ChargeMind Demo · 硬数据硬算 + LLM 叙事包装 · 数据来源：10,942 个深圳场站
        </p>
      </div>
    </div>
  );
}
