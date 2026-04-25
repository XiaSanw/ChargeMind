import { Target, TrendingUp, Scale } from 'lucide-react';

interface Props {
  data: Record<string, unknown>;
}

export default function CompetitivePositionCard({ data }: Props) {
  const cp = data.competitive_position as Record<string, unknown> | undefined;

  if (!cp) {
    return (
      <div className="rounded-2xl border border-border bg-card p-6">
        <h3 className="text-lg font-semibold mb-2">🎯 竞争定位分析</h3>
        <p className="text-sm text-muted-foreground">无竞争定位数据</p>
      </div>
    );
  }

  const capacity = cp.capacity_vs_actual as Record<string, unknown> | undefined;
  const price = cp.competitive_benchmark_price as Record<string, unknown> | undefined;
  const eu = cp.equilibrium_utilization as Record<string, unknown> | undefined;

  return (
    <div className="rounded-2xl border border-border bg-card p-6 space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold">🎯 竞争定位分析</h3>
        <span className="text-xs text-muted-foreground">⭐⭐⭐</span>
      </div>

      {/* Summary */}
      {typeof cp.summary === 'string' && (
        <p className="text-sm text-foreground leading-relaxed">{cp.summary}</p>
      )}

      {/* 容量 vs 实际份额 */}
      {capacity && (
        <div className="rounded-lg bg-secondary/30 p-3 space-y-2">
          <div className="flex items-center gap-2">
            <Scale size={14} className="text-blue-400" />
            <span className="text-sm font-medium">容量份额 vs 实际份额</span>
            <span className="text-xs text-muted-foreground ml-auto">{capacity.confidence as string}</span>
          </div>
          <div className="grid grid-cols-3 gap-2 text-center">
            <div>
              <div className="text-xs text-muted-foreground">容量份额</div>
              <div className="text-lg font-bold">{Number(capacity.capacity_share_pct)}%</div>
            </div>
            <div>
              <div className="text-xs text-muted-foreground">实际份额</div>
              <div className="text-lg font-bold">{Number(capacity.actual_share_pct)}%</div>
            </div>
            <div>
              <div className="text-xs text-muted-foreground">偏差</div>
              <div className={`text-lg font-bold ${(capacity.share_gap_pct as number) > 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                {Number(capacity.share_gap_pct) > 0 ? '+' : ''}{Number(capacity.share_gap_pct)}%
              </div>
            </div>
          </div>
          {typeof capacity.interpretation === 'string' && (
            <div className="text-xs text-center text-muted-foreground">
              判断: {capacity.interpretation}
            </div>
          )}
        </div>
      )}

      {/* 竞争基准价 */}
      {price && (
        <div className="rounded-lg bg-secondary/30 p-3 space-y-2">
          <div className="flex items-center gap-2">
            <Target size={14} className="text-amber-400" />
            <span className="text-sm font-medium">竞争基准价差</span>
            <span className="text-xs text-muted-foreground ml-auto">{price.confidence as string}</span>
          </div>
          <div className="grid grid-cols-3 gap-2 text-center">
            <div>
              <div className="text-xs text-muted-foreground">本场站</div>
              <div className="text-lg font-bold">¥{Number(price.my_price)}/度</div>
            </div>
            <div>
              <div className="text-xs text-muted-foreground">竞品基准</div>
              <div className="text-lg font-bold">¥{Number(price.benchmark_price)}/度</div>
            </div>
            <div>
              <div className="text-xs text-muted-foreground">价差</div>
              <div className={`text-lg font-bold ${(price.price_gap_pct as number) > 0 ? 'text-red-400' : 'text-emerald-400'}`}>
                {Number(price.price_gap_pct) > 0 ? '+' : ''}{Number(price.price_gap_pct)}%
              </div>
            </div>
          </div>
        </div>
      )}

      {/* 均衡利用率 */}
      {eu && eu.low !== null && (
        <div className="rounded-lg bg-secondary/30 p-3 space-y-2">
          <div className="flex items-center gap-2">
            <TrendingUp size={14} className="text-purple-400" />
            <span className="text-sm font-medium">均衡利用率区间（推演）</span>
            <span className="text-xs text-muted-foreground ml-auto">{eu.confidence as string}</span>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold">
              [{((eu.low as number) * 100).toFixed(2)}% — {((eu.high as number) * 100).toFixed(2)}%]
            </div>
            <div className="text-xs text-muted-foreground mt-1">
              弹性假设: {Array.isArray(eu.elasticity_range) ? (eu.elasticity_range as number[]).join('-') : ''}
            </div>
          </div>
          {typeof eu.base_util_source === 'string' && (
            <div className="text-xs text-muted-foreground">{eu.base_util_source}</div>
          )}
        </div>
      )}
    </div>
  );
}
