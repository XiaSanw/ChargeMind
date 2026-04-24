import { Zap, TrendingUp, Crosshair, RefreshCw } from 'lucide-react';
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

const sourceColor: Record<string, string> = {
  '[算法预测]': 'bg-blue-500/10 text-blue-400',
  '[知识库类比]': 'bg-emerald-500/10 text-emerald-400',
  '[行业规律推断]': 'bg-slate-500/10 text-slate-400',
};

interface Props {
  path: PathItem;
}

export default function PathCard({ path }: Props) {
  return (
    <div className="rounded-xl border border-border bg-card p-5 flex flex-col gap-3 min-w-[200px] flex-1">
      <div className="flex items-center gap-2">
        {categoryIcons[path.category] || <Zap size={18} className="text-primary" />}
        <span className="font-semibold text-sm text-foreground">{path.title}</span>
      </div>
      <div className="flex items-baseline gap-1">
        <span className="text-2xl font-bold text-primary">+{path.annual_gain}万</span>
        <span className="text-xs text-muted-foreground">/年</span>
      </div>
      <div className="flex items-center gap-2">
        <span
          className={`inline-flex items-center px-2 py-0.5 rounded-md text-xs font-medium ${
            sourceColor[path.source] || 'bg-slate-500/10 text-slate-400'
          }`}
        >
          {path.source.replace(/[\[\]]/g, '')}
        </span>
      </div>
      <div className="flex justify-between text-xs text-muted-foreground">
        <span>概率 {Math.round(path.probability * 100)}%</span>
        <span>{effortLabel[path.effort]}</span>
      </div>
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
