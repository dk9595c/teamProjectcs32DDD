import './ErrorMessage.css';

interface ErrorMessageProps {
  message: string;
  onRetry?: () => void;
  retryLabel?: string;
}

export function ErrorMessage({ message, onRetry, retryLabel = 'Try Again' }: ErrorMessageProps) {
  return (
    <div className="error-message" role="alert">
      <div className="error-icon" aria-hidden="true">⚠</div>
      <p className="error-text">{message}</p>
      {onRetry && (
        <button className="retry-button" onClick={onRetry} type="button">
          {retryLabel}
        </button>
      )}
    </div>
  );
}