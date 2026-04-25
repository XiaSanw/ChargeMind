import KPICard from './KPICard';
import type { KPICardData } from '@/types/dashboard';

interface Props {
  cards: KPICardData[];
}

export default function KPICards({ cards }: Props) {
  return (
    <div className="grid grid-cols-2 gap-3">
      {cards.map((card) => (
        <KPICard key={card.label} card={card} />
      ))}
    </div>
  );
}
