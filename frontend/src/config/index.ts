/**
 * Application configuration interface and settings.
 * 
 * This module provides type-safe configuration management for the frontend
 * application, including API endpoints, feature flags, and environment-specific
 * settings.
 */

export interface AppConfig {
  /** Base URL for the backend API */
  apiUrl: string;
  
  /** WebSocket URL for real-time updates */
  wsUrl: string;
  
  /** Current environment */
  environment: 'development' | 'production' | 'test';
  
  /** Feature flags */
  features: {
    /** Enable analytics tracking */
    enableAnalytics: boolean;
    
    /** Enable export functionality */
    enableExport: boolean;
    
    /** Enable real-time updates via WebSocket */
    enableRealTimeUpdates: boolean;
    
    /** Enable debug mode */
    enableDebug: boolean;
  };
  
  /** UI configuration */
  ui: {
    /** Default theme */
    defaultTheme: 'light' | 'dark' | 'system';
    
    /** Maximum number of items per page in lists */
    itemsPerPage: number;
    
    /** Auto-refresh interval for task status (in milliseconds) */
    autoRefreshInterval: number;
  };
  
  /** Analysis configuration */
  analysis: {
    /** Maximum allowed video duration in seconds */
    maxVideoDuration: number;
    
    /** Default analysis depth */
    defaultAnalysisDepth: 'basic' | 'detailed' | 'comprehensive';
    
    /** Maximum number of comments to analyze */
    maxComments: number;
    
    /** Supported export formats */
    supportedExportFormats: string[];
  };
  
  /** API configuration */
  api: {
    /** Request timeout in milliseconds */
    timeout: number;
    
    /** Number of retry attempts for failed requests */
    retryAttempts: number;
    
    /** Base delay between retries in milliseconds */
    retryDelay: number;
  };
}

/**
 * Get environment variable with optional default value.
 * 
 * @param key - Environment variable key
 * @param defaultValue - Default value if environment variable is not set
 * @returns Environment variable value or default
 */
function getEnvVar(key: string, defaultValue?: string): string {
  if (typeof window !== 'undefined') {
    return defaultValue || '';
  }
  
  const env = (globalThis as any).process?.env || {};
  return env[key] || defaultValue || '';
}

/**
 * Get boolean environment variable.
 * 
 * @param key - Environment variable key
 * @param defaultValue - Default value if environment variable is not set
 * @returns Boolean value
 */
function getBooleanEnvVar(key: string, defaultValue: boolean = false): boolean {
  const value = getEnvVar(key);
  if (!value) return defaultValue;
  
  return value.toLowerCase() === 'true' || value === '1';
}

/**
 * Get numeric environment variable.
 * 
 * @param key - Environment variable key
 * @param defaultValue - Default value if environment variable is not set
 * @returns Numeric value
 */
function getNumericEnvVar(key: string, defaultValue: number): number {
  const value = getEnvVar(key);
  if (!value) return defaultValue;
  
  const parsed = parseInt(value, 10);
  return isNaN(parsed) ? defaultValue : parsed;
}

/**
 * Application configuration instance.
 * 
 * This configuration is loaded from environment variables with sensible
 * defaults for development.
 */
export const config: AppConfig = {
  apiUrl: getEnvVar('NEXT_PUBLIC_API_URL', 'http://localhost:8000'),
  wsUrl: getEnvVar('NEXT_PUBLIC_WS_URL', 'ws://localhost:8000'),
  environment: (getEnvVar('NODE_ENV', 'development') as AppConfig['environment']),
  
  features: {
    enableAnalytics: getBooleanEnvVar('NEXT_PUBLIC_ENABLE_ANALYTICS', false),
    enableExport: getBooleanEnvVar('NEXT_PUBLIC_ENABLE_EXPORT', true),
    enableRealTimeUpdates: getBooleanEnvVar('NEXT_PUBLIC_ENABLE_REAL_TIME_UPDATES', true),
    enableDebug: getBooleanEnvVar('NEXT_PUBLIC_ENABLE_DEBUG', false),
  },
  
  ui: {
    defaultTheme: (getEnvVar('NEXT_PUBLIC_DEFAULT_THEME', 'system') as AppConfig['ui']['defaultTheme']),
    itemsPerPage: getNumericEnvVar('NEXT_PUBLIC_ITEMS_PER_PAGE', 10),
    autoRefreshInterval: getNumericEnvVar('NEXT_PUBLIC_AUTO_REFRESH_INTERVAL', 5000),
  },
  
  analysis: {
    maxVideoDuration: getNumericEnvVar('NEXT_PUBLIC_MAX_VIDEO_DURATION', 3600),
    defaultAnalysisDepth: (getEnvVar('NEXT_PUBLIC_DEFAULT_ANALYSIS_DEPTH', 'detailed') as AppConfig['analysis']['defaultAnalysisDepth']),
    maxComments: getNumericEnvVar('NEXT_PUBLIC_MAX_COMMENTS', 1000),
    supportedExportFormats: getEnvVar('NEXT_PUBLIC_SUPPORTED_EXPORT_FORMATS', 'json,markdown,pdf,html').split(','),
  },
  
  api: {
    timeout: getNumericEnvVar('NEXT_PUBLIC_API_TIMEOUT', 30000),
    retryAttempts: getNumericEnvVar('NEXT_PUBLIC_API_RETRY_ATTEMPTS', 3),
    retryDelay: getNumericEnvVar('NEXT_PUBLIC_API_RETRY_DELAY', 1000),
  },
};

/**
 * Validate configuration values.
 * 
 * @throws Error if configuration is invalid
 */
export function validateConfig(): void {
  const errors: string[] = [];
  
  if (!config.apiUrl) {
    errors.push('API URL is required');
  }
  
  if (!config.wsUrl) {
    errors.push('WebSocket URL is required');
  }
  
  if (!['development', 'production', 'test'].includes(config.environment)) {
    errors.push(`Invalid environment: ${config.environment}`);
  }
  
  if (config.analysis.maxVideoDuration <= 0) {
    errors.push('Max video duration must be positive');
  }
  
  if (config.analysis.maxComments <= 0) {
    errors.push('Max comments must be positive');
  }
  
  if (config.ui.itemsPerPage <= 0) {
    errors.push('Items per page must be positive');
  }
  
  if (config.ui.autoRefreshInterval < 1000) {
    errors.push('Auto refresh interval must be at least 1000ms');
  }
  
  if (errors.length > 0) {
    throw new Error(`Configuration validation failed: ${errors.join(', ')}`);
  }
}

/**
 * Check if running in development mode.
 */
export const isDevelopment = config.environment === 'development';

/**
 * Check if running in production mode.
 */
export const isProduction = config.environment === 'production';

/**
 * Check if running in test mode.
 */
export const isTesting = config.environment === 'test';

/**
 * Get API endpoint URL.
 * 
 * @param path - API path (should start with /)
 * @returns Full API URL
 */
export function getApiUrl(path: string): string {
  return `${config.apiUrl}${path}`;
}

/**
 * Get WebSocket URL.
 * 
 * @param path - WebSocket path (should start with /)
 * @returns Full WebSocket URL
 */
export function getWsUrl(path: string): string {
  return `${config.wsUrl}${path}`;
}

if (typeof window !== 'undefined') {
  try {
    validateConfig();
  } catch (error) {
    console.error('Configuration validation failed:', error);
  }
}
