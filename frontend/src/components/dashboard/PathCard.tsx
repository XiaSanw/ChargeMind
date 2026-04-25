import { Zap, TrendingUp, Crosshair, RefreshCw, Lightbulb } from 'lucide-react';
import type { PathItem } from '@/types/dashboard';

const categoryIcons: Record<string, React.ReactNode> = {
  '成本优化': <Zap size={18} className="text-amber-400" />,
  '效率提升': <TrendingUp size={18} className="text-emerald-400" />,
  '博弈调价': <Crosshair size={18} className="text-blue-400" />,
  '资产盘活': <RefreshCw size={18} className="text-purple-400" />,
};

const effortLabel: Record<string, string> = {
  low: '投入低',
  medium: '投入中',
  high: '投入高',
};

const effortColor: Record<string, string> = {
  low: 'text-emerald-400',
  medium: 'text-amber-400',
  high: 'text-red-400',
};

interface Props {
  path: PathItem;
}

export default function PathCard({ path }: Props) {
  return (
    <div className="rounded-xl border border-border bg-card p-5 flex flex-col gap-3 min-w-[200px] flex-1">
      <div className="flex items-center gap-2">
        {categoryIcons[path.category] || <Lightbulb size={18} className="text-primary" />}
        <span className="font-semibold text-sm text-foreground">{path.title}</span>
      </div>

      {path.annual_gain !== null ? (
        <div className="flex items-baseline gap-1">
          <span className="text-2xl font-bold text-primary">+{path.annual_gain}万</span>
          <span className="text-xs text-muted-foreground">/年</span>
        </div>
      ) : (
        <div className="flex items-center gap-1">
          <Lightbulb size={16} className="text-muted-foreground" />
          <span className="text-lg font-bold text-muted-foreground">建议方向</span>
        </div>
      )}

      <div className="flex items-center gap-2 text-xs">
        <span className="text-muted-foreground">可信度</span>
        <span className="font-medium text-foreground">{path.trust}</span>
        <span className={`font-medium ${effortColor[path.effort]}`}>{effortLabel[path.effort]}</span>
      </div>

      {path.calculation && (
        <div className="text-xs text-muted-foreground bg-secondary/50 rounded-md px-2 py-1">
          公式: {path.calculation}
        </div>
      )}

      <p
        className="text-xs text-muted-foreground overflow-hidden"
        style={{
          display: '-webkit-box',
          WebkitLineClamp: 2,
          WebkitBoxOrient: 'vertical',
        }}
      >
        {path.detail}
      </p>
    </div>
  );
}
