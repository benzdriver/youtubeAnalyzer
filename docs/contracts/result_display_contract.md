# 结果展示接口契约

**提供方**: TASK_09 (结果展示界面)  
**使用方**: TASK_10 (部署配置)  
**版本**: v1.0.0

## 概述

定义结果展示界面的接口规范，包括分析结果的可视化展示、导出功能和用户交互接口。

## 展示组件接口

### 主要展示组件

```typescript
// 分析结果主页面
interface AnalysisResultPageProps {
  taskId: string;
  result: AnalysisResult;
  onExport?: (format: ExportFormat, data: any) => void;
  onShare?: (platform: SharePlatform, data: any) => void;
  onSave?: (data: any) => void;
}

// 视频信息卡片
interface VideoInfoCardProps {
  videoInfo: VideoInfo;
  className?: string;
  showThumbnail?: boolean;
  showStats?: boolean;
  onThumbnailClick?: () => void;
}

// 内容洞察展示
interface ContentInsightsDisplayProps {
  insights: ContentInsights;
  viewMode?: 'summary' | 'detailed' | 'timeline';
  onKeyPointClick?: (keyPoint: KeyPoint) => void;
  onTopicClick?: (topic: string) => void;
}

// 评论分析展示
interface CommentInsightsDisplayProps {
  insights: CommentInsights;
  viewMode?: 'overview' | 'sentiment' | 'themes' | 'engagement';
  onThemeClick?: (theme: ThemeCluster) => void;
  onSentimentFilter?: (sentiment: SentimentType) => void;
}

// 综合洞察展示
interface ComprehensiveInsightsProps {
  insights: string[];
  recommendations: string[];
  maxItems?: number;
  showPriority?: boolean;
  onInsightExpand?: (insight: string) => void;
}
```

### 数据可视化组件

```typescript
// 情感分布图表
interface SentimentChartProps {
  sentimentData: SentimentDistribution;
  chartType?: 'pie' | 'bar' | 'donut';
  showLabels?: boolean;
  showPercentages?: boolean;
  onSegmentClick?: (sentiment: SentimentType) => void;
}

// 主题词云
interface TopicWordCloudProps {
  topics: TopicData[];
  maxWords?: number;
  colorScheme?: string[];
  onWordClick?: (word: string) => void;
}

// 时间轴图表
interface TimelineChartProps {
  timelineData: TimelinePoint[];
  height?: number;
  showMarkers?: boolean;
  onPointClick?: (point: TimelinePoint) => void;
}

// 质量指标雷达图
interface QualityRadarChartProps {
  qualityMetrics: QualityMetrics;
  maxValue?: number;
  showGrid?: boolean;
  onMetricClick?: (metric: string) => void;
}

// 参与度趋势图
interface EngagementTrendProps {
  engagementData: EngagementPoint[];
  timeRange?: 'hour' | 'day' | 'week';
  showAverage?: boolean;
  onDataPointHover?: (point: EngagementPoint) => void;
}
```

### 交互式组件

```typescript
// 可展开的洞察卡片
interface InsightCardProps {
  title: string;
  content: string;
  priority?: 'high' | 'medium' | 'low';
  category?: string;
  expandable?: boolean;
  actions?: CardAction[];
  onExpand?: () => void;
  onAction?: (action: CardAction) => void;
}

// 过滤器组件
interface ResultFilterProps {
  filters: FilterOption[];
  activeFilters: string[];
  onFilterChange: (filters: string[]) => void;
  onReset: () => void;
}

// 搜索组件
interface ResultSearchProps {
  placeholder?: string;
  onSearch: (query: string) => void;
  onClear: () => void;
  suggestions?: string[];
}

// 排序组件
interface ResultSortProps {
  sortOptions: SortOption[];
  currentSort: string;
  onSortChange: (sort: string) => void;
}
```

## 数据类型定义

### 展示数据结构

```typescript
// 完整分析结果
interface AnalysisResult {
  taskId: string;
  videoInfo: VideoInfo;
  contentInsights: ContentInsights;
  commentInsights: CommentInsights;
  comprehensiveInsights: string[];
  recommendations: string[];
  metadata: AnalysisMetadata;
  createdAt: Date;
  processingTime: number;
}

// 分析元数据
interface AnalysisMetadata {
  version: string;
  models: {
    transcription: string;
    contentAnalysis: string;
    commentAnalysis: string;
  };
  qualityScores: {
    overall: number;
    transcription: number;
    contentAnalysis: number;
    commentAnalysis: number;
  };
  processingStats: {
    totalTime: number;
    stepTimes: Record<string, number>;
    resourceUsage: ResourceUsage;
  };
}

// 可视化数据类型
interface SentimentDistribution {
  positive: number;
  negative: number;
  neutral: number;
  mixed?: number;
}

interface TopicData {
  word: string;
  weight: number;
  category?: string;
  color?: string;
}

interface TimelinePoint {
  timestamp: number;
  value: number;
  label?: string;
  type?: 'content' | 'comment' | 'engagement';
  metadata?: any;
}

interface EngagementPoint {
  time: Date;
  value: number;
  type: 'likes' | 'comments' | 'replies';
  details?: any;
}

// 交互数据类型
interface FilterOption {
  id: string;
  label: string;
  type: 'checkbox' | 'radio' | 'range' | 'select';
  options?: string[];
  defaultValue?: any;
}

interface SortOption {
  id: string;
  label: string;
  direction: 'asc' | 'desc';
}

interface CardAction {
  id: string;
  label: string;
  icon?: string;
  type: 'primary' | 'secondary' | 'danger';
  onClick: () => void;
}
```

### 导出格式定义

```typescript
// 导出格式
enum ExportFormat {
  PDF = 'pdf',
  DOCX = 'docx',
  JSON = 'json',
  CSV = 'csv',
  XLSX = 'xlsx',
  HTML = 'html'
}

// 导出选项
interface ExportOptions {
  format: ExportFormat;
  sections: ExportSection[];
  includeCharts: boolean;
  includeRawData: boolean;
  template?: string;
  customization?: ExportCustomization;
}

interface ExportSection {
  id: string;
  name: string;
  included: boolean;
  options?: any;
}

interface ExportCustomization {
  title?: string;
  subtitle?: string;
  logo?: string;
  colors?: string[];
  fonts?: string[];
}

// 分享平台
enum SharePlatform {
  EMAIL = 'email',
  LINK = 'link',
  TWITTER = 'twitter',
  LINKEDIN = 'linkedin',
  SLACK = 'slack'
}

interface ShareOptions {
  platform: SharePlatform;
  message?: string;
  includePreview: boolean;
  expirationTime?: Date;
}
```

## 布局接口

### 响应式布局

```typescript
// 布局配置
interface LayoutConfig {
  breakpoints: {
    mobile: number;
    tablet: number;
    desktop: number;
    wide: number;
  };
  
  grid: {
    columns: number;
    gap: string;
    maxWidth: string;
  };
  
  sidebar: {
    width: string;
    collapsible: boolean;
    defaultCollapsed: boolean;
  };
}

// 布局组件
interface ResultLayoutProps {
  children: React.ReactNode;
  sidebar?: React.ReactNode;
  header?: React.ReactNode;
  footer?: React.ReactNode;
  config?: Partial<LayoutConfig>;
}

// 网格系统
interface GridProps {
  columns?: number | { [key: string]: number };
  gap?: string;
  children: React.ReactNode;
  className?: string;
}

interface GridItemProps {
  span?: number | { [key: string]: number };
  offset?: number | { [key: string]: number };
  children: React.ReactNode;
  className?: string;
}
```

### 导航接口

```typescript
// 结果导航
interface ResultNavigationProps {
  sections: NavigationSection[];
  currentSection: string;
  onSectionChange: (section: string) => void;
  sticky?: boolean;
}

interface NavigationSection {
  id: string;
  label: string;
  icon?: string;
  badge?: string | number;
  disabled?: boolean;
  subsections?: NavigationSection[];
}

// 面包屑导航
interface BreadcrumbProps {
  items: BreadcrumbItem[];
  separator?: string;
  maxItems?: number;
  onItemClick?: (item: BreadcrumbItem) => void;
}

interface BreadcrumbItem {
  label: string;
  href?: string;
  active?: boolean;
}
```

## 状态管理接口

### 结果展示状态

```typescript
interface ResultDisplayState {
  // 当前展示的结果
  currentResult: AnalysisResult | null;
  
  // 视图状态
  viewMode: 'overview' | 'detailed' | 'comparison';
  activeSection: string;
  expandedCards: string[];
  
  // 过滤和搜索
  filters: Record<string, any>;
  searchQuery: string;
  sortBy: string;
  
  // 可视化设置
  chartSettings: {
    theme: 'light' | 'dark';
    animations: boolean;
    colorScheme: string;
  };
  
  // 导出状态
  exportInProgress: boolean;
  exportHistory: ExportRecord[];
  
  // UI状态
  sidebarCollapsed: boolean;
  fullscreenMode: boolean;
  loading: boolean;
  error: string | null;
}

interface ResultDisplayActions {
  // 结果操作
  setResult: (result: AnalysisResult) => void;
  clearResult: () => void;
  
  // 视图操作
  setViewMode: (mode: string) => void;
  setActiveSection: (section: string) => void;
  toggleCardExpansion: (cardId: string) => void;
  
  // 过滤和搜索
  updateFilters: (filters: Record<string, any>) => void;
  setSearchQuery: (query: string) => void;
  setSortBy: (sort: string) => void;
  
  // 导出操作
  exportResult: (options: ExportOptions) => Promise<void>;
  
  // UI操作
  toggleSidebar: () => void;
  toggleFullscreen: () => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
}
```

## 性能优化接口

### 虚拟化和懒加载

```typescript
// 虚拟化列表
interface VirtualizedResultListProps {
  items: any[];
  itemHeight: number;
  renderItem: (item: any, index: number) => React.ReactNode;
  containerHeight: number;
  overscan?: number;
}

// 懒加载图表
interface LazyChartProps {
  chartType: string;
  data: any;
  placeholder?: React.ReactNode;
  threshold?: number;
  onLoad?: () => void;
}

// 图片懒加载
interface LazyImageProps {
  src: string;
  alt: string;
  placeholder?: string;
  className?: string;
  onLoad?: () => void;
  onError?: () => void;
}
```

### 缓存接口

```typescript
// 结果缓存
interface ResultCache {
  get: (key: string) => AnalysisResult | null;
  set: (key: string, result: AnalysisResult, ttl?: number) => void;
  delete: (key: string) => void;
  clear: () => void;
  size: () => number;
}

// 图表缓存
interface ChartCache {
  getChart: (key: string) => ChartData | null;
  setChart: (key: string, data: ChartData) => void;
  invalidate: (pattern: string) => void;
}
```

## 错误处理接口

### 错误展示组件

```typescript
// 错误边界
interface ResultErrorBoundaryProps {
  children: React.ReactNode;
  fallback?: React.ComponentType<ErrorFallbackProps>;
  onError?: (error: Error, errorInfo: ErrorInfo) => void;
}

// 错误展示
interface ErrorDisplayProps {
  error: AnalysisError;
  onRetry?: () => void;
  onReport?: (error: AnalysisError) => void;
  showDetails?: boolean;
}

// 加载失败组件
interface LoadFailureProps {
  message: string;
  onRetry: () => void;
  retryCount?: number;
  maxRetries?: number;
}
```

## 可访问性接口

### 无障碍支持

```typescript
// 可访问性配置
interface AccessibilityConfig {
  screenReader: boolean;
  highContrast: boolean;
  largeText: boolean;
  reducedMotion: boolean;
  keyboardNavigation: boolean;
}

// ARIA标签
interface AriaLabels {
  chartDescription: string;
  tableDescription: string;
  buttonLabels: Record<string, string>;
  sectionLabels: Record<string, string>;
}

// 键盘导航
interface KeyboardNavigationProps {
  onKeyDown: (event: KeyboardEvent) => void;
  focusableElements: string[];
  trapFocus?: boolean;
}
```

## 测试接口

### 测试工具

```typescript
// 组件测试
interface ResultTestUtils {
  renderWithResult: (component: React.ReactNode, result: AnalysisResult) => RenderResult;
  mockChartData: (type: string) => any;
  simulateUserInteraction: (element: HTMLElement, action: string) => void;
}

// 可视化测试
interface ChartTestUtils {
  captureChart: (chartId: string) => Promise<string>;
  compareCharts: (chart1: string, chart2: string) => boolean;
  validateChartData: (data: any, schema: any) => boolean;
}

// 性能测试
interface PerformanceTestUtils {
  measureRenderTime: (component: React.ReactNode) => number;
  measureMemoryUsage: () => number;
  simulateSlowNetwork: (delay: number) => void;
}
```

## 使用示例

### 基本结果展示

```typescript
function ResultPage({ taskId }: { taskId: string }) {
  const [result, setResult] = useState<AnalysisResult | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  useEffect(() => {
    fetchResult(taskId)
      .then(setResult)
      .catch(err => setError(err.message))
      .finally(() => setLoading(false));
  }, [taskId]);
  
  const handleExport = async (format: ExportFormat) => {
    try {
      const exportData = await exportResult(result!, format);
      downloadFile(exportData, `analysis-${taskId}.${format}`);
    } catch (error) {
      console.error('导出失败:', error);
    }
  };
  
  if (loading) return <LoadingSpinner />;
  if (error) return <ErrorDisplay error={{ message: error }} />;
  if (!result) return <div>结果不存在</div>;
  
  return (
    <ResultLayout
      header={<ResultHeader result={result} onExport={handleExport} />}
      sidebar={<ResultNavigation sections={navigationSections} />}
    >
      <div className="space-y-6">
        <VideoInfoCard videoInfo={result.videoInfo} />
        
        <ContentInsightsDisplay 
          insights={result.contentInsights}
          viewMode="detailed"
        />
        
        <CommentInsightsDisplay 
          insights={result.commentInsights}
          viewMode="overview"
        />
        
        <ComprehensiveInsights
          insights={result.comprehensiveInsights}
          recommendations={result.recommendations}
        />
      </div>
    </ResultLayout>
  );
}
```

### 自定义图表组件

```typescript
function CustomSentimentChart({ data }: { data: SentimentDistribution }) {
  const chartRef = useRef<HTMLCanvasElement>(null);
  
  useEffect(() => {
    if (chartRef.current) {
      const chart = new Chart(chartRef.current, {
        type: 'doughnut',
        data: {
          labels: ['积极', '消极', '中性'],
          datasets: [{
            data: [data.positive, data.negative, data.neutral],
            backgroundColor: ['#10B981', '#EF4444', '#6B7280']
          }]
        },
        options: {
          responsive: true,
          plugins: {
            legend: {
              position: 'bottom'
            }
          }
        }
      });
      
      return () => chart.destroy();
    }
  }, [data]);
  
  return (
    <div className="chart-container">
      <canvas ref={chartRef} />
    </div>
  );
}
```
