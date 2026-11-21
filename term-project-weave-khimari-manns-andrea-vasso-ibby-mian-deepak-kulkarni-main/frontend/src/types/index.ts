export interface Stock {
  ticker: string;
  name: string;
  sector?: string;
  industry?: string;
  marketCap?: number;
  peRatio?: number;
}

export interface PricePoint {
  date: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

export interface PortfolioHolding {
  ticker: string;
  weight: number;
  shares?: number;
}

export interface Portfolio {
  id: string;
  name: string;
  holdings: PortfolioHolding[];
  initialCapital: number;
  startDate: string;
  endDate: string;
  strategy: 'buy-hold' | 'momentum';
}

export interface BacktestMetrics {
  cumulativeReturn: number;
  annualizedReturn: number;
  volatility: number;
  maxDrawdown: number;
}

export interface BacktestResult {
  portfolio: BacktestMetrics;
  benchmark: BacktestMetrics;
  equityCurve: Array<{
    date: string;
    portfolioValue: number;
    benchmarkValue: number;
  }>;
}

export interface Question {
  id: string;
  type: 'percentage-return' | 'pe-ratio' | 'portfolio-allocation';
  prompt: string;
  data: Record<string, unknown>;
  correctAnswer: unknown;
  explanation: string;
}

export interface GradeRequest {
  questionId: string;
  userAnswer: unknown;
}

export interface GradeResponse {
  correct: boolean;
  score: number;
  explanation: string;
}

export interface HealthResponse {
  status: 'ok';
  timestamp: string;
  version: string;
}