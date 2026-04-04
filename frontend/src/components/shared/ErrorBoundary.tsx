import { Component, type ReactNode } from 'react';
import { AlertTriangle, RefreshCw } from 'lucide-react';

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) return this.props.fallback;

      return (
        <div className="flex flex-col items-center justify-center py-16 px-4 text-center">
          <div className="flex items-center justify-center w-12 h-12 rounded-full bg-severity-critical/10 mb-4">
            <AlertTriangle size={24} className="text-severity-critical" />
          </div>
          <h2 className="text-sm font-semibold text-text-primary mb-1">Etwas ist schiefgelaufen</h2>
          <p className="text-xs text-text-tertiary max-w-sm mb-4">
            {this.state.error?.message || 'Ein unerwarteter Fehler ist aufgetreten.'}
          </p>
          <button
            onClick={() => { this.setState({ hasError: false, error: null }); window.location.reload(); }}
            className="inline-flex items-center gap-1.5 rounded-md bg-accent/10 border border-accent/30 px-3 py-1.5 text-xs font-medium text-accent hover:bg-accent/20"
          >
            <RefreshCw size={13} /> Seite neu laden
          </button>
        </div>
      );
    }

    return this.props.children;
  }
}
