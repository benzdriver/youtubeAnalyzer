'use client';

import React, { Component, ErrorInfo, ReactNode } from 'react';
import { Button, Card } from './ui';

interface Props {
  children: ReactNode;
  fallback?: React.ComponentType<ErrorFallbackProps>;
  onError?: (error: Error, errorInfo: ErrorInfo) => void;
}

interface State {
  hasError: boolean;
  error: Error | null;
  errorInfo: ErrorInfo | null;
}

interface ErrorFallbackProps {
  error: Error;
  resetError: () => void;
}

const DefaultErrorFallback: React.FC<ErrorFallbackProps> = ({ error, resetError }) => (
  <Card className="p-8 text-center max-w-lg mx-auto mt-8">
    <div className="text-red-500 text-6xl mb-4">⚠️</div>
    <h2 className="text-2xl font-bold text-gray-900 mb-4">出现了错误</h2>
    <p className="text-gray-600 mb-6">
      抱歉，应用程序遇到了意外错误。请尝试刷新页面或联系技术支持。
    </p>
    <details className="text-left mb-6 p-4 bg-gray-50 rounded-lg">
      <summary className="cursor-pointer font-medium text-gray-700 mb-2">
        错误详情
      </summary>
      <pre className="text-sm text-red-600 whitespace-pre-wrap overflow-auto">
        {error.message}
        {error.stack && (
          <>
            {'\n\n'}
            {error.stack}
          </>
        )}
      </pre>
    </details>
    <div className="flex justify-center space-x-4">
      <Button onClick={resetError}>
        重试
      </Button>
      <Button variant="outline" onClick={() => window.location.reload()}>
        刷新页面
      </Button>
    </div>
  </Card>
);

export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = {
      hasError: false,
      error: null,
      errorInfo: null
    };
  }

  static getDerivedStateFromError(error: Error): Partial<State> {
    return {
      hasError: true,
      error
    };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    this.setState({
      error,
      errorInfo
    });

    if (this.props.onError) {
      this.props.onError(error, errorInfo);
    }

    console.error('ErrorBoundary caught an error:', error, errorInfo);
  }

  resetError = () => {
    this.setState({
      hasError: false,
      error: null,
      errorInfo: null
    });
  };

  render() {
    if (this.state.hasError && this.state.error) {
      const FallbackComponent = this.props.fallback || DefaultErrorFallback;
      
      return (
        <FallbackComponent
          error={this.state.error}
          resetError={this.resetError}
        />
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;
