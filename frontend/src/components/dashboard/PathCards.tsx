import PathCard from './PathCard';
import type { PathItem } from '@/types/dashboard';

interface Props {
  paths: PathItem[];
}

export default function PathCards({ paths }: Props) {
  return (
    <div className="rounded-2xl border border-border bg-card p-6 space-y-4">
      <h3 className="text-lg font-semibold">💡 提升路径</h3>
      <div className="flex flex-col md:flex-row gap-4">
        {paths.map((path, i) => (
          <PathCard key={i} path={path} />
        ))}
      </div>
    </div>
  );
}
