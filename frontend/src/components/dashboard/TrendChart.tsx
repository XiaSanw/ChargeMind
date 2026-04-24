import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';
import type { TrendProjection } from '@/types/dashboard';

interface Props {
  data: TrendProjection;
}

const SCENARIO_COLORS: Record<string, string> = {
  '保守': '#f59e0b',
  '基准': '#3b82f6',
  '乐观': '#10b981',
};

export default function TrendChart({ data }: Props) {
  const chartData = data.months.map((month, i) => {
    const point: Record<string, number | string> = { month: `${month}月` };
    data.scenarios.forEach((s) => {
      point[s.name] = s.values[i];
    });
    return point;
  });

  return (
    <div className="rounded-2xl border border-border bg-card p-6 space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold">📈 趋势推演</h3>
      </div>
      <ResponsiveContainer width="100%" height={280}>
        <LineChart data={chartData}>
          <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
          <XAxis dataKey="month" tick={{ fill: '#94a3b8' }} />
          <YAxis tick={{ fill: '#94a3b8' }} unit="万" />
          <Tooltip
            contentStyle={{
              backgroundColor: '#1e293b',
              border: '1px solid #334155',
              borderRadius: '8px',
              color: '#f8fafc',
            }}
          />
          <Legend wrapperStyle={{ color: '#94a3b8' }} />
          {data.scenarios.map((s) => (
            <Line
              key={s.name}
              type="monotone"
              dataKey={s.name}
              stroke={SCENARIO_COLORS[s.name] || '#94a3b8'}
              strokeWidth={2}
              dot={{ r: 4 }}
              activeDot={{ r: 6 }}
            />
          ))}
        </LineChart>
      </ResponsiveContainer>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-2">
        {data.scenarios.map((s) => (
          <div key={s.name} className="rounded-lg bg-secondary/50 p-3 text-xs">
            <div className="flex items-center gap-2 mb-1">
              <span
                className="w-3 h-3 rounded-full"
                style={{ backgroundColor: SCENARIO_COLORS[s.name] }}
              />
              <span className="font-medium text-foreground">{s.name}</span>
            </div>
            <p className="text-muted-foreground">{s.description}</p>
          </div>
        ))}
      </div>
    </div>
  );
}
