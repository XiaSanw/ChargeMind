import { Car, MapPin } from 'lucide-react';

interface BrandItem {
  brand: string;
  share_pct: number;
  cars: number;
  main_power_level?: string;
}

interface BrandPileItem {
  brand: string;
  count: number;
  supply_pct: number;
  demand_pct: number;
  judgment: string;
  reason: string;
}

interface BrandPileAnalysis {
  region_demand_text: string;
  station_supply_text: string;
  station_items: BrandPileItem[];
}

interface Props {
  data: Record<string, unknown>;
}

export default function BrandAnalysisCard({ data }: Props) {
  const brandMatrix = data.brand_matrix as Record<string, unknown> | undefined;
  const bpAnalysis = data.brand_pile_analysis as BrandPileAnalysis | undefined;

  if (!brandMatrix) {
    return (
      <div className="rounded-2xl border border-border bg-card p-6">
        <h3 className="text-lg font-semibold mb-2">🚗 品牌与车辆画像</h3>
        <p className="text-sm text-muted-foreground">无品牌分析数据</p>
      </div>
    );
  }

  const brands = (brandMatrix?.brands || []) as BrandItem[];
  const concentration = brandMatrix?.concentration as Record<string, unknown> | undefined;
  const top3 = brands.slice(0, 3);

  return (
    <div className="rounded-2xl border border-border bg-card p-6 space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold">🚗 品牌与车辆画像</h3>
        <span className="text-xs text-muted-foreground">{brandMatrix?.confidence as string || '⭐⭐⭐'}</span>
      </div>

      {/* 框1：品牌构成 */}
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

          {/* 专用桩品牌洞察引导 */}
          {!bpAnalysis && (
            <div className="rounded-md bg-primary/5 border border-primary/10 p-2.5 space-y-1">
              <div className="flex items-center gap-2">
                <span className="text-xs font-medium text-primary">专用桩品牌洞察</span>
              </div>
              <p className="text-xs text-muted-foreground leading-relaxed">
                周边车流涉及 {brands.length} 个品牌类型
                {top3.length > 0 && (
                  <>（{top3.map(b => b.brand).join('、')} 等）</>
                )}。
                {brands.length >= 3
                  ? '品牌集中度较高，建议配置高功率通用快充以覆盖多品牌需求。'
                  : '品牌分布较分散，通用桩为主，可针对性引入头部品牌合作桩。'}
              </p>
            </div>
          )}
        </div>
      )}

      {/* 框2：区域品牌画像与用户场站对比 */}
      {bpAnalysis && (
        <div className="rounded-lg bg-secondary/30 p-3 space-y-3">
          <div className="flex items-center gap-2">
            <MapPin size={14} className="text-teal" />
            <span className="text-sm font-medium">区域品牌画像与用户场站对比</span>
          </div>

          {/* 第 1 段：区域需求画像 */}
          {bpAnalysis.region_demand_text && (
            <p className="text-sm text-muted-foreground leading-relaxed">{bpAnalysis.region_demand_text}</p>
          )}

          {/* 第 2 段：用户场站品牌专用桩供给结构 */}
          {bpAnalysis.station_supply_text && (
            <p className="text-sm text-muted-foreground leading-relaxed">{bpAnalysis.station_supply_text}</p>
          )}

          {/* 第 3 段：用户场站诊断 */}
          {bpAnalysis.station_items && bpAnalysis.station_items.length > 0 && (
            <div className="space-y-2 pt-1">
              <div className="text-xs font-medium text-foreground">用户场站品牌专用桩诊断：</div>
              {bpAnalysis.station_items.map((item, i) => (
                <div key={i} className="rounded-md bg-navy-light/40 border border-border/50 p-2.5">
                  <div className="flex items-center justify-between gap-3">
                    <span className="font-medium text-foreground">{item.brand}</span>
                    <span className="text-xs font-semibold whitespace-nowrap shrink-0">
                      {item.count} 台 · {item.judgment}
                    </span>
                  </div>
                  <p className="text-xs text-muted-foreground mt-1">{item.reason}</p>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
