import { useState } from 'react';
import HeroSection from './components/HeroSection';
import ConsultDialog from './components/ConsultDialog';

export default function App() {
  const [isDialogOpen, setIsDialogOpen] = useState(false);

  return (
    <div className="relative min-h-screen bg-navy">
      <HeroSection onStartConsult={() => setIsDialogOpen(true)} />
      <ConsultDialog isOpen={isDialogOpen} onClose={() => setIsDialogOpen(false)} />
    </div>
  );
}
