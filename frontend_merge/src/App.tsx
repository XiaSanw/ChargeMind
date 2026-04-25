import { DiagnosisProvider, useDiagnosis } from '@/store/DiagnosisContext';
import LandingPage from '@/pages/LandingPage';
import EnrichPage from '@/pages/EnrichPage';
import ReportPage from '@/pages/ReportPage';

function PageRouter() {
  const { currentPage } = useDiagnosis();

  if (currentPage === 'landing') {
    return <LandingPage />;
  }

  return (
    <div className="min-h-screen bg-background text-foreground">
      {currentPage === 'enrich' && <EnrichPage />}
      {currentPage === 'report' && <ReportPage />}
    </div>
  );
}

function App() {
  return (
    <DiagnosisProvider>
      <PageRouter />
    </DiagnosisProvider>
  );
}

export default App;
