import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { AppLayout } from './components/AppLayout';
import { LearnPage } from './pages/LearnPage';
import { PracticePage } from './pages/PracticePage';
import { StockResearchPage } from './pages/StockResearchPage';
import { PortfolioPage } from './pages/PortfolioPage';
import { BacktestPage } from './pages/BacktestPage';

function App() {
  return (
    <BrowserRouter>
      <AppLayout>
        <Routes>
          <Route path="/learn" element={<LearnPage />} />
          <Route path="/practice" element={<PracticePage />} />
          <Route path="/research" element={<StockResearchPage />} />
          <Route path="/portfolio" element={<PortfolioPage />} />
          <Route path="/backtest" element={<BacktestPage />} />
          <Route path="/" element={<LearnPage />} />
          <Route path="*" element={<LearnPage />} />
        </Routes>
      </AppLayout>
    </BrowserRouter>
  );
}

export default App;