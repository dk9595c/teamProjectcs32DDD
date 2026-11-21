import { z } from 'zod';

export const stockSchema = z.object({
  ticker: z.string(),
  name: z.string(),
  sector: z.string().optional(),
  industry: z.string().optional(),
  marketCap: z.number().optional(),
  peRatio: z.number().optional(),
});

export const pricePointSchema = z.object({
  date: z.string(),
  open: z.number(),
  high: z.number(),
  low: z.number(),
  close: z.number(),
  volume: z.number(),
});

export const portfolioSchema = z.object({
  id: z.string(),
  name: z.string(),
  holdings: z.array(z.object({
    ticker: z.string(),
    weight: z.number(),
    shares: z.number().optional(),
  })),
  initialCapital: z.number(),
  startDate: z.string(),
  endDate: z.string(),
  strategy: z.enum(['buy-hold', 'momentum']),
});

export const backtestResultSchema = z.object({
  portfolio: z.object({
    cumulativeReturn: z.number(),
    annualizedReturn: z.number(),
    volatility: z.number(),
    maxDrawdown: z.number(),
  }),
  benchmark: z.object({
    cumulativeReturn: z.number(),
    annualizedReturn: z.number(),
    volatility: z.number(),
    maxDrawdown: z.number(),
  }),
  equityCurve: z.array(z.object({
    date: z.string(),
    portfolioValue: z.number(),
    benchmarkValue: z.number(),
  })),
});

export const questionSchema = z.object({
  id: z.string(),
  type: z.enum(['percentage-return', 'pe-ratio', 'portfolio-allocation']),
  prompt: z.string(),
  data: z.record(z.unknown()),
  correctAnswer: z.unknown(),
  explanation: z.string(),
});

export const gradeRequestSchema = z.object({
  questionId: z.string(),
  userAnswer: z.unknown(),
});

export const gradeResponseSchema = z.object({
  correct: z.boolean(),
  score: z.number(),
  explanation: z.string(),
});

export type Stock = z.infer<typeof stockSchema>;
export type PricePoint = z.infer<typeof pricePointSchema>;
export type Portfolio = z.infer<typeof portfolioSchema>;
export type BacktestResult = z.infer<typeof backtestResultSchema>;
export type Question = z.infer<typeof questionSchema>;
export type GradeRequest = z.infer<typeof gradeRequestSchema>;
export type GradeResponse = z.infer<typeof gradeResponseSchema>;