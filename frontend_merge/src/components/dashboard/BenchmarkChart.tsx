import { useState } from 'react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Cell,
  ResponsiveContainer,
} from 'recharts';
import type { Benchmark } from '@/types/dashboard';

interface Props {
  benchmark: Benchmark;
}

export default function BenchmarkChart({ benchmark }: Props) {
  const [selectedKey, setSelectedKey] = useState(benchmark.selected_metric);
  const metric = benchmark.metrics.find((m) => m.key === selectedKey)!;

  const chartData = benchmark.labels.map((label, i) => ({
    name: label,
    value: metric.values[i],
    isUser: i === 0,
  }));

  return (
    <div className="rounded-2xl border border-border bg-card p-6 space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold">📊 运营标杆对比</h3>
        <div className="flex gap-2">
          {benchmark.metrics.map((m) => (
            <button
              key={m.key}
              onClick={() => setSelectedKey(m.key)}
              className={`px-3 py-1 rounded-lg text-xs font-medium transition-all ${
                m.key === selectedKey
                  ? 'bg-primary text-primary-foreground'
                  : 'bg-secondary text-muted-foreground hover:text-foreground'
              }`}
            >
              {m.name}
            </button>
          ))}
        </div>
      </div>
      <ResponsiveContainer width="100%" height={280}>
        <BarChart data={chartData} barCategoryGap="20%">
          <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
          <XAxis
            dataKey="name"
            tick={{ fill: '#94a3b8', fontSize: 11 }}
            interval={0}
            angle={-15}
            textAnchor="end"
            height={60}
          />
          <YAxis
            tick={{ fill: '#94a3b8', fontSize: 12 }}
            unit={metric.unit}
          />
          <Tooltip
            contentStyle={{
              backgroundColor: '#1e293b',
              border: '1px solid #334155',
              borderRadius: '8px',
              color: '#f8fafc',
            }}
          />
          <Bar dataKey="value" radius={[4, 4, 0, 0]}>
            {chartData.map((entry, i) => (
              <Cell
                key={i}
                fill={entry.isUser ? '#3b82f6' : '#64748b'}
              />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
      <p className="text-xs text-muted-foreground text-center">
        蓝色柱为你的场站，灰色柱为对标场站
      </p>
    </div>
  );
}
