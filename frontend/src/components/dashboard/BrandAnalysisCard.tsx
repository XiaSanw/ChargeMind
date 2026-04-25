import { BatteryCharging } from 'lucide-react';

interface BrandItem {
  brand: string;
  share_pct: number;
  cars: number;
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

  return (
    <div className="rounded-2xl border border-border bg-card p-6 space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold">🚗 品牌与车辆画像</h3>
        <span className="text-xs text-muted-foreground">{brandMatrix?.confidence as string || '⭐⭐⭐'}</span>
      </div>

      {/* 品牌构成 */}
      {brands.length > 0 && (
        <div className="space-y-2">
          <div className="text-xs text-muted-foreground">{(brandMatrix?.title as string) || '品牌构成'}</div>
          <div className="space-y-1.5">
            {brands.slice(0, 5).map((b, i) => (
              <div key={i} className="flex items-center gap-2 text-sm">
                <span className="w-14 text-xs text-muted-foreground">{b.brand}</span>
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
          {concentration && (
            <div className="flex items-center gap-4 text-xs text-muted-foreground">
              <span>CR3: {((concentration.cr3 as number) * 100).toFixed(0)}%</span>
              <span>CR5: {((concentration.cr5 as number) * 100).toFixed(0)}%</span>
              <span>格局: {concentration.structure as string}</span>
            </div>
          )}
        </div>
      )}

      {/* 电池容量 */}
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
