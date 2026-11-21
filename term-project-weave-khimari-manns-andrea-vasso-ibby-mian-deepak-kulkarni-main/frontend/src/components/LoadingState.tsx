import './LoadingState.css';

interface LoadingStateProps {
  message?: string;
  size?: 'small' | 'medium' | 'large';
}

export function LoadingState({ message = 'Loading...', size = 'medium' }: LoadingStateProps) {
  const sizeClass = `spinner-${size}`;
  return (
    <div className={`loading-state ${sizeClass}`} role="status" aria-live="polite">
      <div className="spinner" aria-hidden="true"></div>
      <p className="loading-message">{message}</p>
    </div>
  );
}