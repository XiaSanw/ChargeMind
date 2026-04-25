import { BatteryCharging, Car, Gauge } from 'lucide-react';

interface BrandItem {
  brand: string;
  share_pct: number;
  cars: number;
  main_power_level?: string;
}

interface Props {
  data: Record<string, unknown>;
}

export default function BrandAnalysisCard({ data }: Props) {
  const brandMatrix = data.brand_matrix as Record<string, unknown> | undefined;
  const batteryCapacity = data.battery_capacity as Record<string, unknown> | undefined;

  if (!brandMatrix && !batteryCapacity) {
    return (
      <div className="rounded-2xl border border-border bg-card p-6">
        <h3 className="text-lg font-semibold mb-2">🚗 品牌与车辆画像</h3>
        <p className="text-sm text-muted-foreground">无品牌分析数据</p>
      </div>
    );
  }

  const brands = (brandMatrix?.brands || []) as BrandItem[];
  const concentration = brandMatrix?.concentration as Record<string, unknown> | undefined;

  // 统计专用桩品牌（排除"非自有桩品牌"这个通用类别）
  const exclusiveBrands = brands.filter(b => b.brand !== '非自有桩品牌');
  const exclusiveCount = exclusiveBrands.length;
  const topExclusive = exclusiveBrands.slice(0, 3);

  return (
    <div className="rounded-2xl border border-border bg-card p-6 space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold">🚗 品牌与车辆画像</h3>
        <span className="text-xs text-muted-foreground">{brandMatrix?.confidence as string || '⭐⭐⭐'}</span>
      </div>

      {/* 框1：品牌构成 + 专用桩洞察 */}
      {brands.length > 0 && (
        <div className="rounded-lg bg-secondary/30 p-3 space-y-3">
          <div className="flex items-center gap-2">
            <Car size={14} className="text-blue-400" />
            <span className="text-sm font-medium">{(brandMatrix?.title as string) || '品牌构成'}</span>
          </div>

          {/* 品牌条形图 */}
          <div className="space-y-1.5">
            {brands.slice(0, 5).map((b, i) => (
              <div key={i} className="flex items-center gap-2 text-sm">
                <span className="w-16 text-xs text-muted-foreground">{b.brand}</span>
                <div className="flex-1 h-4 bg-secondary/50 rounded-md overflow-hidden">
                  <div
                    className="h-full bg-blue-500/60 rounded-md"
                    style={{ width: `${Math.min(b.share_pct, 100)}%` }}
                  />
                </div>
                <span className="w-12 text-xs text-right">{b.share_pct}%</span>
              </div>
            ))}
          </div>

          {/* 集中度 */}
          {concentration && (
            <div className="flex items-center gap-4 text-xs text-muted-foreground border-t border-border/50 pt-2">
              <span>CR3: {((concentration.cr3 as number) * 100).toFixed(0)}%</span>
              <span>CR5: {((concentration.cr5 as number) * 100).toFixed(0)}%</span>
              <span>格局: {concentration.structure as string}</span>
            </div>
          )}

          {/* 专用桩洞察引导 */}
          {exclusiveCount > 0 && (
            <div className="rounded-md bg-primary/5 border border-primary/10 p-2.5 space-y-1">
              <div className="flex items-center gap-2">
                <Gauge size={13} className="text-primary" />
                <span className="text-xs font-medium text-primary">专用桩品牌洞察</span>
              </div>
              <p className="text-xs text-muted-foreground leading-relaxed">
                周边车流涉及 <span className="font-semibold text-foreground">{exclusiveCount}</span> 个品牌专用桩类型
                {topExclusive.length > 0 && (
                  <>（{topExclusive.map(b => b.brand).join('、')} 等）</>
                )}。
                {exclusiveCount >= 3
                  ? '品牌集中度较高，建议配置高功率通用快充以覆盖多品牌需求。'
                  : '品牌分布较分散，通用桩为主，可针对性引入头部品牌合作桩。'}
              </p>
            </div>
          )}
        </div>
      )}

      {/* 框2：电池容量与功率建议 */}
      {batteryCapacity && (
        <div className="rounded-lg bg-secondary/30 p-3 space-y-1">
          <div className="flex items-center gap-2">
            <BatteryCharging size={14} className="text-emerald-400" />
            <span className="text-sm font-medium">{(batteryCapacity.title as string) || '电池容量'}</span>
          </div>
          <p className="text-sm text-muted-foreground">{(batteryCapacity.power_suggestion as string) || ''}</p>
          <div className="flex items-center gap-4 text-xs text-muted-foreground">
            <span>主流: {batteryCapacity.dominant_range as string}kWh（{(batteryCapacity.dominant_pct as number)?.toFixed(1) || '?'}%）</span>
            <span>加权平均: {batteryCapacity.weighted_avg_kwh as number}kWh</span>
          </div>
        </div>
      )}
    </div>
  );
}
