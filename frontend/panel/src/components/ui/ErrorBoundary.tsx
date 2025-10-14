/**
 * Error Boundary Component
 * Catches React errors and displays fallback UI
 */
import { Component, type ErrorInfo, type ReactNode } from "react";

interface Props {
  children: ReactNode;
}

interface State {
  hasError: boolean;
}

export class ErrorBoundary extends Component<Props, State> {
  state: State = { hasError: false };

  static getDerivedStateFromError(): State {
    return { hasError: true };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo): void {
    // Log error to console for debugging
    console.error("ErrorBoundary caught error:", error, errorInfo);
  }

  render(): ReactNode {
    if (this.state.hasError) {
      return (
        <div className="p-6 text-sm text-rose-700 bg-rose-50 dark:bg-rose-900/20 dark:text-rose-400 rounded-xl border border-rose-200 dark:border-rose-800">
          <div className="font-semibold mb-2">
            ⚠️ Oops — something went wrong.
          </div>
          <div className="text-xs text-rose-600 dark:text-rose-500">
            Please refresh the page or contact support if the issue persists.
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}
