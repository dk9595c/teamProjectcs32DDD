import './MetricExplanation.css';

interface MetricExplanationProps {
  title: string;
  value: string | number;
  explanation: string;
  unit?: string;
  trend?: 'positive' | 'negative' | 'neutral';
}

export function MetricExplanation({ title, value, explanation, unit = '', trend = 'neutral' }: MetricExplanationProps) {
  const trendClass = `trend-${trend}`;
  return (
    <div className="metric-card">
      <div className="metric-header">
        <h3 className="metric-title">{title}</h3>
        <span className={`metric-trend ${trendClass}`} aria-label={`${trend} trend`}>
          {trend === 'positive' && '▲'}
          {trend === 'negative' && '▼'}
          {trend === 'neutral' && '●'}
        </span>
      </div>
      <div className="metric-value">
        <span className="metric-number">{value}</span>
        <span className="metric-unit">{unit}</span>
      </div>
      <p className="metric-explanation">{explanation}</p>
    </div>
  );
}