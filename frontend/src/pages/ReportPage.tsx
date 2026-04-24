import { useCallback } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { useDiagnosis } from '@/store/DiagnosisContext';
import type { SimilarStation, RecommendationItem, ConflictItem } from '@/types/diagnosis';

function LoadingOverlay() {
  const phases = [
    '正在解析场站画像...',
    '正在检索相似场站（RAG 引擎）...',
    '正在生成优化建议（DeepSeek v4-pro）...',
  ];

  return (
    <div className="min-h-screen flex flex-col items-center justify-center px-4">
      <div className="text-center space-y-6 max-w-md">
        <div className="relative inline-flex items-center justify-center">
          <div className="absolute w-20 h-20 rounded-full border-2 border-primary/20" />
          <div className="absolute w-20 h-20 rounded-full border-2 border-transparent border-t-primary animate-spin" />
          <div className="w-12 h-12 rounded-full bg-primary/10 flex items-center justify-center">
            <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-primary"><path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z"/></svg>
          </div>
        </div>
        <div className="space-y-2">
          <h2 className="text-xl font-semibold">双引擎诊断中...</h2>
          <p className="text-sm text-muted-foreground animate-pulse">
            {phases[Math.floor(Date.now() / 3000) % phases.length]}
          </p>
        </div>
        <div className="h-1.5 rounded-full bg-secondary overflow-hidden">
          <div className="h-full rounded-full bg-primary animate-[loading_2s_ease-in-out_infinite]" style={{ width: '60%' }} />
        </div>
      </div>
    </div>
  );
}

function SimilarStationCard({ station, index }: { station: SimilarStation; index: number }) {
  const meta = station.metadata;
  const util = meta.avg_utilization;
  const utilPercent = typeof util === 'number' ? (util * 100).toFixed(1) : util;

  return (
    <div className="rounded-xl border border-border bg-input p-4 space-y-2">
      <div className="flex items-center justify-between">
        <span className="text-sm font-medium text-foreground">
          {index + 1}. {meta.station_name || '未命名场站'}
        </span>
        <span className="text-xs px-2 py-0.5 rounded-full bg-primary/10 text-primary">
          相似度 {(station.similarity_score * 100).toFixed(0)}%
        </span>
      </div>
      <div className="grid grid-cols-2 gap-2 text-xs text-muted-foreground">
        <div>区域：{meta.region || '未知'}</div>
        <div>利用率：{utilPercent}%</div>
        <div>功率：{meta.total_installed_power || '未知'}kW</div>
        <div>日均：{meta.avg_daily_energy_kwh || '未知'}度</div>
      </div>
    </div>
  );
}

function SourceTag({ source }: { source: string }) {
  const map: Record<string, { color: string; label: string }> = {
    '[算法预测]': { color: 'bg-blue-500/10 text-blue-400', label: '算法预测' },
    '[知识库类比]': { color: 'bg-emerald-500/10 text-emerald-400', label: '知识库类比' },
    '[行业规律推断]': { color: 'bg-slate-500/10 text-slate-400', label: '行业规律推断' },
    '[算法预测] + [知识库类比]': { color: 'bg-blue-500/10 text-blue-400', label: '算法+知识库' },
  };
  const cfg = map[source] || { color: 'bg-slate-500/10 text-slate-400', label: source };
  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded-md text-xs font-medium ${cfg.color}`}>
      {cfg.label}
    </span>
  );
}

function AlgorithmPanel({ algorithm }: { algorithm: { predicted_utilization: number; annual_revenue: number; annual_cost: number; annual_profit: number; confidence: number; is_stub: boolean; note: string; breakdown?: Record<string, unknown> } }) {
  const utilPercent = (algorithm.predicted_utilization * 100).toFixed(1);
  const profitWan = (algorithm.annual_profit / 10000).toFixed(1);
  const revenueWan = (algorithm.annual_revenue / 10000).toFixed(1);
  const costWan = (algorithm.annual_cost / 10000).toFixed(1);

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-2">
        <div className="w-8 h-8 rounded-lg bg-blue-500/10 flex items-center justify-center">
          <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-blue-400"><path d="M12 20V10"/><path d="M18 20V4"/><path d="M6 20v-4"/></svg>
        </div>
        <h3 className="text-lg font-semibold">算法预测</h3>
      </div>

      {algorithm.is_stub && (
        <div className="rounded-xl border border-amber-500/20 bg-amber-500/5 p-3 text-sm text-amber-300">
          <div className="flex items-start gap-2">
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="mt-0.5 shrink-0"><path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z"/><line x1="12" x2="12" y1="9" y2="13"/><line x1="12" x2="12.01" y1="17" y2="17"/></svg>
            <span>{algorithm.note}</span>
          </div>
        </div>
      )}

      <div className="grid grid-cols-2 gap-3">
        <div className="rounded-xl bg-input border border-border p-4 text-center">
          <div className="text-2xl font-bold text-foreground">{utilPercent}%</div>
          <div className="text-xs text-muted-foreground mt-1">预测利用率</div>
        </div>
        <div className="rounded-xl bg-input border border-border p-4 text-center">
          <div className={`text-2xl font-bold ${Number(profitWan) >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
            {Number(profitWan) > 0 ? '+' : ''}{profitWan}万
          </div>
          <div className="text-xs text-muted-foreground mt-1">预测年利润</div>
        </div>
        <div className="rounded-xl bg-input border border-border p-4 text-center">
          <div className="text-xl font-bold text-foreground">{revenueWan}万</div>
          <div className="text-xs text-muted-foreground mt-1">预测年收益</div>
        </div>
        <div className="rounded-xl bg-input border border-border p-4 text-center">
          <div className="text-xl font-bold text-foreground">{costWan}万</div>
          <div className="text-xs text-muted-foreground mt-1">预测年成本</div>
        </div>
      </div>

      <div className="flex items-center gap-2 text-sm text-muted-foreground">
        <span>置信度：</span>
        <div className="flex-1 h-2 rounded-full bg-secondary overflow-hidden">
          <div className="h-full rounded-full bg-blue-400" style={{ width: `${(algorithm.confidence * 100).toFixed(0)}%` }} />
        </div>
        <span>{(algorithm.confidence * 100).toFixed(0)}%</span>
      </div>
    </div>
  );
}

function RAGPanel({ rag }: { rag: { similar_stations: SimilarStation[]; analysis: string } }) {
  return (
    <div className="space-y-4">
      <div className="flex items-center gap-2">
        <div className="w-8 h-8 rounded-lg bg-emerald-500/10 flex items-center justify-center">
          <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-emerald-400"><path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"/><polyline points="3.27 6.96 12 12.01 20.73 6.96"/><line x1="12" x2="12" y1="22.08" y2="12"/></svg>
        </div>
        <h3 className="text-lg font-semibold">知识库类比</h3>
      </div>

      <div className="space-y-3">
        <p className="text-sm text-muted-foreground">
          从 10,942 条深圳场站数据中检索到 {rag.similar_stations.length} 个相似场站
        </p>
        {rag.similar_stations.slice(0, 5).map((s, i) => (
          <SimilarStationCard key={s.station_id} station={s} index={i} />
        ))}
      </div>

      {rag.analysis && (
        <div className="rounded-xl border border-border bg-input p-4">
          <h4 className="text-sm font-medium mb-2">RAG 分析洞察</h4>
          <div className="prose prose-invert prose-sm max-w-none">
            <ReactMarkdown remarkPlugins={[remarkGfm]}>{rag.analysis}</ReactMarkdown>
          </div>
        </div>
      )}
    </div>
  );
}

export default function ReportPage() {
  const { diagnoseResult, isDiagnosing, error, reset, setError } = useDiagnosis();

  const handleRetry = useCallback(() => {
    setError(null);
    reset();
  }, [setError, reset]);

  if (isDiagnosing) {
    return <LoadingOverlay />;
  }

  if (error) {
    return (
      <div className="min-h-screen flex flex-col items-center justify-center px-4">
        <div className="text-center space-y-4 max-w-md">
          <div className="inline-flex items-center justify-center w-14 h-14 rounded-full bg-red-500/10">
            <svg xmlns="http://www.w3.org/2000/svg" width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-red-400"><circle cx="12" cy="12" r="10"/><line x1="15" x2="9" y1="9" y2="15"/><line x1="9" x2="15" y1="9" y2="15"/></svg>
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

  if (!diagnoseResult) {
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

  const { profile, algorithm, rag, report } = diagnoseResult;
  const region = profile.region || '未知';
  const biz = profile.business_type?.join('、') || '未知';

  return (
    <div className="min-h-screen px-4 py-8 md:py-12">
      <div className="mx-auto max-w-6xl space-y-8">
        {/* Header */}
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
          <div>
            <h1 className="text-2xl md:text-3xl font-bold">诊断报告</h1>
            <p className="text-muted-foreground mt-1">
              {region} · {biz} · {profile.pile_count || '?'} 桩 · {profile.total_installed_power || '?'} kW
            </p>
          </div>
          <button
            onClick={reset}
            className="inline-flex items-center gap-2 self-start rounded-xl border border-border bg-card px-4 py-2 text-sm font-medium hover:bg-secondary transition-all"
          >
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M3 12a9 9 0 1 0 9-9 9.75 9.75 0 0 0-6.74 2.74L3 8"/><path d="M3 3v5h5"/></svg>
            重新诊断
          </button>
        </div>

        {/* Executive Summary */}
        <div className="rounded-2xl border border-border bg-card p-6">
          <p className="text-lg leading-relaxed">{report.executive_summary}</p>
        </div>

        {/* Dual Panel */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="rounded-2xl border border-border bg-card p-6">
            <AlgorithmPanel algorithm={algorithm} />
          </div>
          <div className="rounded-2xl border border-border bg-card p-6">
            <RAGPanel rag={rag} />
          </div>
        </div>

        {/* Conflicts */}
        {report.conflicts && report.conflicts.length > 0 && (
          <div className="rounded-2xl border border-amber-500/20 bg-amber-500/5 p-6">
            <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
              <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-amber-400"><path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z"/><line x1="12" x2="12" y1="9" y2="13"/><line x1="12" x2="12.01" y1="17" y2="17"/></svg>
              思维碰撞：发现 {report.conflicts.length} 处冲突
            </h3>
            <div className="space-y-3">
              {report.conflicts.map((c: ConflictItem, i: number) => (
                <div key={i} className="rounded-xl bg-background/50 p-4 space-y-2">
                  <div className="text-sm font-medium text-amber-300">{c.type}</div>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-2 text-sm">
                    <div className="text-muted-foreground"><span className="text-blue-400">算法：</span>{c.algorithm}</div>
                    <div className="text-muted-foreground"><span className="text-emerald-400">RAG：</span>{c.rag}</div>
                    <div className="text-foreground"><span className="text-amber-400">调和：</span>{c.resolution}</div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Recommendations */}
        {report.recommendations && report.recommendations.length > 0 && (
          <div className="rounded-2xl border border-border bg-card p-6">
            <h3 className="text-lg font-semibold mb-4">优化建议</h3>
            <div className="space-y-3">
              {report.recommendations.map((r: RecommendationItem, i: number) => (
                <div key={i} className="flex items-start gap-3 rounded-xl bg-input p-4">
                  <div className="mt-0.5 shrink-0 w-6 h-6 rounded-full bg-primary/10 flex items-center justify-center text-xs font-bold text-primary">
                    {i + 1}
                  </div>
                  <div className="space-y-1">
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className="font-medium text-foreground">{r.title}</span>
                      <SourceTag source={r.source} />
                    </div>
                    <p className="text-sm text-muted-foreground">{r.detail}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Full Report Markdown */}
        {report.rag_analysis && (
          <div className="rounded-2xl border border-border bg-card p-6">
            <h3 className="text-lg font-semibold mb-4">详细分析报告</h3>
            <div className="prose prose-invert prose-sm max-w-none">
              <ReactMarkdown remarkPlugins={[remarkGfm]}>{report.rag_analysis}</ReactMarkdown>
            </div>
          </div>
        )}

        {/* Footer */}
        <p className="text-center text-xs text-muted-foreground pb-8">
          ChargeMind Demo · 算法预测为基于规则的 Stub · 数据来源：深圳 10,942 条场站记录
        </p>
      </div>
    </div>
  );
}
