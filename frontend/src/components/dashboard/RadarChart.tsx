import {
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  Radar,
  ResponsiveContainer,
} from 'recharts';
import type { RadarData } from '@/types/dashboard';

interface Props {
  data: RadarData;
  overallScore: number;
}

export default function StationRadarChart({ data, overallScore }: Props) {
  const chartData = Object.entries(data).map(([dimension, val]) => ({
    dimension,
    score: val.score,
  }));

  return (
    <div className="relative w-full">
      <ResponsiveContainer width="100%" height={320}>
        <RadarChart data={chartData} cx="50%" cy="50%" outerRadius="65%">
          <PolarGrid stroke="#334155" />
          <PolarAngleAxis
            dataKey="dimension"
            tick={{ fill: '#94a3b8', fontSize: 12 }}
          />
          <PolarRadiusAxis domain={[0, 100]} tick={false} axisLine={false} />
          <Radar
            dataKey="score"
            stroke="#3b82f6"
            fill="#3b82f6"
            fillOpacity={0.25}
            strokeWidth={2}
          />
        </RadarChart>
      </ResponsiveContainer>
      {/* 中心综合评分 */}
      <div className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none">
        <span className="text-4xl font-bold text-foreground">{overallScore}</span>
        <span className="text-xs text-muted-foreground mt-1">综合评分</span>
      </div>
    </div>
  );
}
