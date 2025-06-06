import React from 'react';
import { AnalysisTask, AnalysisResult, AnalysisStep, AnalysisOptions, AnalysisError, TaskStatus, ValidationRule, ExportFormat, SharePlatform } from './analysis';
import { WebSocketMessage } from './api';

export interface BaseComponentProps {
  className?: string;
  children?: React.ReactNode;
  testId?: string;
}

export interface AnalysisTaskProps extends BaseComponentProps {
  taskId: string;
  onStatusChange?: (status: TaskStatus) => void;
  onComplete?: (result: AnalysisResult) => void;
  onError?: (error: AnalysisError) => void;
}

export interface YouTubeInputProps extends BaseComponentProps {
  onSubmit: (url: string, options: AnalysisOptions) => void;
  isLoading?: boolean;
  disabled?: boolean;
  placeholder?: string;
  validationRules?: ValidationRule[];
}

export interface ProgressTrackerProps extends BaseComponentProps {
  taskId: string;
  steps: AnalysisStep[];
  currentStep?: string;
  progress: number;
  showDetails?: boolean;
  onStepClick?: (step: AnalysisStep) => void;
}

export interface ResultDisplayProps extends BaseComponentProps {
  result: AnalysisResult;
  viewMode?: 'summary' | 'detailed' | 'export';
  onExport?: (format: ExportFormat) => void;
  onShare?: (platform: SharePlatform) => void;
}

export interface AnalysisTypeSelectorProps extends BaseComponentProps {
  selectedType: string;
  onTypeChange: (type: string) => void;
}

export interface ButtonProps extends BaseComponentProps {
  variant?: 'primary' | 'secondary' | 'outline' | 'ghost' | 'danger';
  size?: 'sm' | 'md' | 'lg';
  disabled?: boolean;
  loading?: boolean;
  onClick?: (e?: React.MouseEvent) => void;
  type?: 'button' | 'submit' | 'reset';
}

export interface InputProps extends BaseComponentProps {
  type?: 'text' | 'email' | 'password' | 'url' | 'number';
  placeholder?: string;
  value?: string;
  defaultValue?: string;
  disabled?: boolean;
  required?: boolean;
  error?: string;
  min?: string | number;
  max?: string | number;
  onChange?: (value: string) => void;
  onBlur?: () => void;
  onFocus?: () => void;
}

export interface CardProps extends BaseComponentProps {
  title?: string;
  subtitle?: string;
  padding?: 'none' | 'sm' | 'md' | 'lg';
  shadow?: 'none' | 'sm' | 'md' | 'lg';
  border?: boolean;
}

export interface ProgressProps extends BaseComponentProps {
  value: number;
  max?: number;
  size?: 'sm' | 'md' | 'lg';
  variant?: 'default' | 'success' | 'warning' | 'error';
  showLabel?: boolean;
  label?: string;
}

export interface Notification {
  id: string;
  type: 'success' | 'error' | 'warning' | 'info';
  message: string;
  duration?: number;
  action?: {
    label: string;
    onClick: () => void;
  };
}

export interface UserSettings {
  autoSave: boolean;
  notifications: boolean;
  defaultAnalysisDepth: 'basic' | 'detailed' | 'comprehensive';
  theme: 'light' | 'dark';
  language: string;
}

export interface AppState {
  currentTask: AnalysisTask | null;
  taskHistory: AnalysisTask[];
  ui: {
    sidebarOpen: boolean;
    theme: 'light' | 'dark';
    language: string;
    notifications: Notification[];
  };
  websocket: {
    connected: boolean;
    reconnecting: boolean;
    lastMessage?: WebSocketMessage;
  };
  settings: UserSettings;
}

export interface AppActions {
  createTask: (url: string, options: AnalysisOptions) => Promise<string>;
  updateTask: (taskId: string, updates: Partial<AnalysisTask>) => void;
  deleteTask: (taskId: string) => void;
  toggleSidebar: () => void;
  setTheme: (theme: 'light' | 'dark') => void;
  addNotification: (notification: Notification) => void;
  removeNotification: (id: string) => void;
  connectWebSocket: (taskId: string) => void;
  disconnectWebSocket: () => void;
  handleWebSocketMessage: (message: WebSocketMessage) => void;
  updateSettings: (settings: Partial<UserSettings>) => void;
}

export interface AppStore extends AppState, AppActions {}

export interface UseWebSocketOptions {
  taskId: string;
  onMessage?: (message: WebSocketMessage) => void;
  onConnect?: () => void;
  onDisconnect?: () => void;
  onError?: (error: Event) => void;
  reconnectAttempts?: number;
  reconnectInterval?: number;
}

export interface UseWebSocketReturn {
  connected: boolean;
  reconnecting: boolean;
  lastMessage: WebSocketMessage | null;
  sendMessage: (message: any) => void;
  disconnect: () => void;
}

export interface RouteParams {
  taskId?: string;
}

export interface PageProps {
  params: RouteParams;
  searchParams: Record<string, string>;
}

export interface LayoutProps {
  children: React.ReactNode;
  params: RouteParams;
}

export interface ThemeConfig {
  colors: {
    primary: string;
    secondary: string;
    success: string;
    warning: string;
    error: string;
    background: string;
    surface: string;
    text: {
      primary: string;
      secondary: string;
      disabled: string;
    };
  };
  spacing: {
    xs: string;
    sm: string;
    md: string;
    lg: string;
    xl: string;
  };
  typography: {
    fontFamily: string;
    fontSize: {
      xs: string;
      sm: string;
      base: string;
      lg: string;
      xl: string;
    };
    fontWeight: {
      normal: number;
      medium: number;
      bold: number;
    };
  };
  borderRadius: {
    sm: string;
    md: string;
    lg: string;
    full: string;
  };
  shadows: {
    sm: string;
    md: string;
    lg: string;
  };
}

export interface ThemeProviderProps {
  children: React.ReactNode;
  theme?: 'light' | 'dark';
  customTheme?: Partial<ThemeConfig>;
}

export interface ErrorBoundaryProps {
  children: React.ReactNode;
  fallback?: React.ComponentType<ErrorFallbackProps>;
  onError?: (error: Error, errorInfo: React.ErrorInfo) => void;
}

export interface ErrorFallbackProps {
  error: Error;
  resetError: () => void;
}

export interface UseErrorHandlerReturn {
  error: AnalysisError | null;
  setError: (error: AnalysisError) => void;
  clearError: () => void;
  retry: () => void;
}

export interface VirtualizedListProps<T> {
  items: T[];
  itemHeight: number;
  renderItem: (item: T, index: number) => React.ReactNode;
  containerHeight: number;
  overscan?: number;
  onScroll?: (scrollTop: number) => void;
}

export interface LazyComponentProps {
  children: React.ReactNode;
  placeholder?: React.ReactNode;
  threshold?: number;
  rootMargin?: string;
}

export interface RenderOptions {
  initialState?: Partial<AppState>;
  theme?: 'light' | 'dark';
  locale?: string;
}

export interface MockWebSocketOptions {
  autoConnect?: boolean;
  messages?: WebSocketMessage[];
  delay?: number;
}

export interface TestDataFactory {
  createTask: (overrides?: Partial<AnalysisTask>) => AnalysisTask;
  createVideoInfo: (overrides?: Partial<any>) => any;
  createAnalysisResult: (overrides?: Partial<AnalysisResult>) => AnalysisResult;
  createWebSocketMessage: (type: string, data?: any) => WebSocketMessage;
}
