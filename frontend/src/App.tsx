import { DiagnosisProvider, useDiagnosis } from '@/store/DiagnosisContext';
import StationInputPage from '@/pages/StationInputPage';
import EnrichPage from '@/pages/EnrichPage';
import ReportPage from '@/pages/ReportPage';

function PageRouter() {
  const { currentPage } = useDiagnosis();

  return (
    <div className="min-h-screen bg-background text-foreground">
      {currentPage === 'input' && <StationInputPage />}
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
