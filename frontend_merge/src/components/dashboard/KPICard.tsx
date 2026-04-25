import { TrendingUp, TrendingDown, Minus } from 'lucide-react';
import type { KPICardData } from '@/types/dashboard';

const trendIcon = {
  up: TrendingUp,
  down: TrendingDown,
  flat: Minus,
};

const trendColor = {
  up: 'text-emerald-400',
  down: 'text-red-400',
  flat: 'text-amber-400',
};

const trendBg = {
  up: 'bg-emerald-500/10',
  down: 'bg-red-500/10',
  flat: 'bg-amber-500/10',
};

interface Props {
  card: KPICardData;
}

export default function KPICard({ card }: Props) {
  const Icon = trendIcon[card.trend];

  return (
    <div className="rounded-xl border border-border bg-card p-4 flex flex-col gap-2 min-w-[140px]">
      <div className="flex items-center justify-between">
        <span className="text-xs text-muted-foreground">{card.label}</span>
        <span className="text-[10px] text-muted-foreground">{card.trust}</span>
      </div>
      <span className="text-2xl font-bold text-foreground">{card.value}</span>
      <div className={`inline-flex items-center gap-1 text-xs font-medium ${trendColor[card.trend]} ${trendBg[card.trend]} rounded-md px-2 py-1 w-fit`}>
        <Icon size={14} />
        <span>{card.detail}</span>
      </div>
      <span className="text-xs text-muted-foreground">{card.benchmark}</span>
    </div>
  );
}
