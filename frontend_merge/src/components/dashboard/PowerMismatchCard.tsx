import { Zap, Battery, MapPin } from 'lucide-react';

interface SupplyDemandItem {
  power_range: string;
  label: string;
  supply_pct: number;
  demand_pct: number;
  gap_pct: number;
  direction: string;
}

interface PileBreakdownItem {
  label: string;
  count: number;
  dominant_range: string;
  demand_pct: number;
  judgment: string;
  reason: string;
}

interface PileBreakdownAnalysis {
  region_demand_text: string;
  region_supply_text: string;
  station_items: PileBreakdownItem[];
}

interface Props {
  data: Record<string, unknown>;
}

export default function PowerMismatchCard({ data }: Props) {
  if (data.error) {
    return (
      <div className="rounded-2xl border border-border bg-card p-6">
        <h3 className="text-lg font-semibold mb-2">⚡ 功率错配分析</h3>
        <p className="text-sm text-muted-foreground">{data.error as string}</p>
      </div>
    );
  }

  const tvdScore = data.tvd_score as number;
  const tvdLevel = data.tvd_level as string;
  const supplyVsDemand = (data.supply_vs_demand || []) as SupplyDemandItem[];
  const dominant = data.dominant_mismatch as Record<string, unknown> | undefined;
  const batteryContext = data.battery_context as Record<string, unknown> | undefined;
  const pbAnalysis = data.pile_breakdown_analysis as PileBreakdownAnalysis | undefined;

  // TVD 颜色
  const tvdColor = tvdScore > 0.5 ? 'text-red-400' : tvdScore > 0.2 ? 'text-amber-400' : 'text-emerald-400';
  const tvdBg = tvdScore > 0.5 ? 'bg-red-500/10' : tvdScore > 0.2 ? 'bg-amber-500/10' : 'bg-emerald-500/10';

  return (
    <div className="rounded-2xl border border-border bg-card p-6 space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold">⚡ 功率错配分析</h3>
        <span className="text-xs text-muted-foreground">{data.confidence as string}</span>
      </div>

      {/* TVD 分数 */}
      <div className={`rounded-xl ${tvdBg} p-4 flex items-center justify-between`}>
        <div>
          <div className="text-xs text-muted-foreground mb-1">功率错配分数 (TVD)</div>
          <div className={`text-3xl font-bold ${tvdColor}`}>{tvdScore.toFixed(2)}</div>
        </div>
        <div className="text-right">
          <div className={`text-sm font-medium ${tvdColor}`}>{tvdLevel}</div>
          <div className="text-xs text-muted-foreground">{data.mismatch_direction as string}</div>
        </div>
      </div>

      {/* 供需对比 */}
      {supplyVsDemand.length > 0 && (
        <div className="space-y-2">
          <div className="text-xs text-muted-foreground">功率档供需对比</div>
          <div className="space-y-1.5">
            {supplyVsDemand.map((item, i) => (
              <div key={i} className="flex items-center gap-2 text-sm">
                <span className="w-16 text-xs text-muted-foreground">{item.label}</span>
                <div className="flex-1 h-5 bg-secondary/50 rounded-md overflow-hidden relative">
                  {/* 供给条 */}
                  <div
                    className="absolute left-0 top-0 h-full bg-blue-500/60 rounded-md"
                    style={{ width: `${Math.min(item.supply_pct, 100)}%` }}
                  />
                  {/* 需求条 */}
                  <div
                    className="absolute left-0 top-0 h-full bg-emerald-500/40 rounded-md"
                    style={{ width: `${Math.min(item.demand_pct, 100)}%` }}
                  />
                </div>
                <span className="w-20 text-xs text-right">
                  <span className="text-blue-400">供{item.supply_pct.toFixed(0)}%</span>
                  <span className="text-muted-foreground mx-0.5">/</span>
                  <span className="text-emerald-400">需{item.demand_pct.toFixed(0)}%</span>
                </span>
              </div>
            ))}
          </div>
          <div className="flex items-center gap-4 text-xs">
            <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-sm bg-blue-500/60" />供给</span>
            <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-sm bg-emerald-500/40" />需求</span>
          </div>
        </div>
      )}

      {/* 主导错配 */}
      {dominant && (
        <div className="rounded-lg bg-secondary/30 p-3 text-sm">
          <div className="flex items-center gap-2">
            <Zap size={14} className="text-amber-400" />
            <span className="font-medium">主导错配</span>
          </div>
          <p className="text-muted-foreground mt-1">
            在当前区域下，{dominant.label as string}（{dominant.power_range as string}）
            {dominant.direction as string} {(dominant.gap_pct as number).toFixed(1)}%
          </p>
        </div>
      )}

      {/* pile_breakdown 三段式分析 */}
      {pbAnalysis && (
        <div className="rounded-lg bg-secondary/30 p-3 text-sm space-y-3">
          <div className="flex items-center gap-2">
            <MapPin size={14} className="text-teal" />
            <span className="font-medium">区域功率画像与用户场站对比</span>
          </div>

          {/* 第 1 段：区域需求画像 */}
          <p className="text-muted-foreground leading-relaxed">{pbAnalysis.region_demand_text}</p>

          {/* 第 2 段：区域供给现状 */}
          <p className="text-muted-foreground leading-relaxed">{pbAnalysis.region_supply_text}</p>

          {/* 第 3 段：用户场站对比 */}
          <div className="space-y-2 pt-1">
            <div className="text-xs font-medium text-foreground">您场站的功率结构诊断：</div>
            {pbAnalysis.station_items.map((item, i) => (
              <div key={i} className="rounded-md bg-navy-light/40 border border-border/50 p-2.5">
                <div className="flex items-center justify-between gap-3">
                  <span className="font-medium text-foreground">{item.label}</span>
                  <span className="text-xs font-semibold whitespace-nowrap shrink-0">
                    {item.count} 台 · {item.judgment}
                  </span>
                </div>
                <p className="text-xs text-muted-foreground mt-1">{item.reason}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* 电池容量建议（兜底，如果 pile_breakdown 分析不存在则展示原电池建议） */}
      {!pbAnalysis && batteryContext && (
        <div className="rounded-lg bg-secondary/30 p-3 text-sm space-y-1">
          <div className="flex items-center gap-2">
            <Battery size={14} className="text-blue-400" />
            <span className="font-medium">电池容量与功率建议</span>
          </div>
          <p className="text-muted-foreground">{(batteryContext.power_suggestion as string) || ''}</p>
          <div className="flex items-center gap-4 text-xs text-muted-foreground">
            <span>加权平均: {batteryContext.weighted_avg_kwh as number}kWh</span>
            <span>主流区间: {batteryContext.dominant_range as string}（{(batteryContext.dominant_pct as number)?.toFixed(1) || '?'}%）</span>
          </div>
        </div>
      )}
    </div>
  );
}
