import { useState, useCallback, useEffect } from 'react';
import { useDiagnosis } from '@/store/DiagnosisContext';
import HeroSection from '@/components/landing/HeroSection';
import ConsultDialog from '@/components/landing/ConsultDialog';

export default function LandingPage() {
  const { autoOpenDialog, clearAutoOpenDialog } = useDiagnosis();
  const [isDialogOpen, setIsDialogOpen] = useState(false);

  useEffect(() => {
    if (autoOpenDialog) {
      setIsDialogOpen(true);
      clearAutoOpenDialog();
    }
  }, [autoOpenDialog, clearAutoOpenDialog]);

  const handleStartConsult = useCallback(() => {
    setIsDialogOpen(true);
  }, []);

  return (
    <div className="relative min-h-screen bg-navy" style={{ fontFamily: 'var(--font-body)' }}>
      <HeroSection onStartConsult={handleStartConsult} />
      <ConsultDialog isOpen={isDialogOpen} onClose={() => setIsDialogOpen(false)} />
    </div>
  );
}
