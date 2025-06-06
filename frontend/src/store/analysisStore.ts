import { create } from 'zustand';
import { devtools, persist } from 'zustand/middleware';
import { AppStore, AppState, AppActions, Notification, UserSettings } from '@/types/ui';
import { AnalysisTask, AnalysisOptions, TaskStatus, AnalysisType } from '@/types/analysis';
import { WebSocketMessage, CreateTaskRequest, ApiResponse, CreateTaskResponse } from '@/types/api';

const initialState: AppState = {
  currentTask: null,
  taskHistory: [],
  ui: {
    sidebarOpen: true,
    theme: 'light',
    language: 'zh-CN',
    notifications: []
  },
  websocket: {
    connected: false,
    reconnecting: false
  },
  settings: {
    autoSave: true,
    notifications: true,
    defaultAnalysisDepth: 'detailed',
    theme: 'light',
    language: 'zh-CN'
  }
};

export const useAnalysisStore = create<AppStore>()(
  devtools(
    persist(
      (set, get) => ({
        ...initialState,

        createTask: async (url: string, options: AnalysisOptions): Promise<string> => {
          try {
            const requestBody: CreateTaskRequest = {
              youtube_url: url,
              options
            };

            const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/v1/analyze`, {
              method: 'POST',
              headers: { 
                'Content-Type': 'application/json',
                'Accept': 'application/json'
              },
              body: JSON.stringify(requestBody)
            });

            if (!response.ok) {
              throw new Error(`HTTP error! status: ${response.status}`);
            }

            const result: ApiResponse<CreateTaskResponse> = await response.json();

            if (result.success && result.data) {
              const task: AnalysisTask = {
                id: result.data.task_id,
                type: options.analysisDepth === 'comprehensive' ? AnalysisType.COMPREHENSIVE :
                      options.analysisDepth === 'basic' ? AnalysisType.CONTENT_ONLY : 
                      AnalysisType.COMPREHENSIVE,
                url,
                options,
                status: TaskStatus.PENDING,
                progress: 0,
                createdAt: new Date().toISOString(),
                updatedAt: new Date().toISOString(),
                input: { youtube_url: url, options },
                steps: [],
                currentStep: 'initializing'
              };

              set(state => ({
                currentTask: task,
                taskHistory: [task, ...state.taskHistory.slice(0, 49)]
              }));

              get().connectWebSocket(task.id);

              get().addNotification({
                id: Date.now().toString(),
                type: 'success',
                message: '分析任务已创建，正在开始处理...',
                duration: 3000
              });

              return task.id;
            } else {
              throw new Error(result.error?.message || '创建任务失败');
            }
          } catch (error) {
            const errorMessage = error instanceof Error ? error.message : '未知错误';
            
            get().addNotification({
              id: Date.now().toString(),
              type: 'error',
              message: `任务创建失败: ${errorMessage}`,
              duration: 5000
            });
            
            throw error;
          }
        },

        updateTask: (taskId: string, updates: Partial<AnalysisTask>) => {
          set(state => ({
            currentTask: state.currentTask?.id === taskId 
              ? { ...state.currentTask, ...updates, updatedAt: new Date().toISOString() }
              : state.currentTask,
            taskHistory: state.taskHistory.map(task =>
              task.id === taskId 
                ? { ...task, ...updates, updatedAt: new Date().toISOString() } 
                : task
            )
          }));
        },

        deleteTask: (taskId: string) => {
          set(state => ({
            currentTask: state.currentTask?.id === taskId ? null : state.currentTask,
            taskHistory: state.taskHistory.filter(task => task.id !== taskId)
          }));

          get().addNotification({
            id: Date.now().toString(),
            type: 'info',
            message: '任务已删除',
            duration: 2000
          });
        },

        toggleSidebar: () => {
          set(state => ({
            ui: { ...state.ui, sidebarOpen: !state.ui.sidebarOpen }
          }));
        },

        setTheme: (theme: 'light' | 'dark') => {
          set(state => ({
            ui: { ...state.ui, theme },
            settings: { ...state.settings, theme }
          }));
        },

        addNotification: (notification: Notification) => {
          set(state => ({
            ui: {
              ...state.ui,
              notifications: [...state.ui.notifications, notification]
            }
          }));

          if (notification.duration) {
            setTimeout(() => {
              get().removeNotification(notification.id);
            }, notification.duration);
          }
        },

        removeNotification: (id: string) => {
          set(state => ({
            ui: {
              ...state.ui,
              notifications: state.ui.notifications.filter(n => n.id !== id)
            }
          }));
        },

        connectWebSocket: (taskId: string) => {
          try {
            const wsUrl = `${process.env.NEXT_PUBLIC_WS_URL}/ws/${taskId}`.replace('http', 'ws');
            const ws = new WebSocket(wsUrl);

            ws.onopen = () => {
              set(state => ({
                websocket: { 
                  ...state.websocket, 
                  connected: true, 
                  reconnecting: false 
                }
              }));

              get().addNotification({
                id: Date.now().toString(),
                type: 'success',
                message: '实时连接已建立',
                duration: 2000
              });
            };

            ws.onmessage = (event) => {
              try {
                const message: WebSocketMessage = JSON.parse(event.data);
                get().handleWebSocketMessage(message);
              } catch (error) {
                console.error('Failed to parse WebSocket message:', error);
              }
            };

            ws.onclose = () => {
              set(state => ({
                websocket: { ...state.websocket, connected: false }
              }));
            };

            ws.onerror = (error) => {
              console.error('WebSocket error:', error);
              get().addNotification({
                id: Date.now().toString(),
                type: 'error',
                message: 'WebSocket连接失败',
                duration: 3000
              });
            };

            (get() as any)._ws = ws;
          } catch (error) {
            console.error('Failed to connect WebSocket:', error);
          }
        },

        disconnectWebSocket: () => {
          const ws = (get() as any)._ws;
          if (ws) {
            ws.close();
            delete (get() as any)._ws;
          }
          
          set(state => ({
            websocket: { 
              ...state.websocket, 
              connected: false, 
              reconnecting: false 
            }
          }));
        },

        handleWebSocketMessage: (message: WebSocketMessage) => {
          const { type, data, task_id } = message;

          set(state => ({
            websocket: { ...state.websocket, lastMessage: message }
          }));

          switch (type) {
            case 'progress_update':
              get().updateTask(task_id, {
                status: TaskStatus.PROCESSING,
                progress: data.progress,
                currentStep: data.current_step,
                estimatedTimeRemaining: data.estimated_time_remaining
              });
              break;

            case 'task_completed':
              get().updateTask(task_id, {
                status: TaskStatus.COMPLETED,
                progress: 100,
                result: data.result,
                completedAt: new Date()
              });

              get().addNotification({
                id: Date.now().toString(),
                type: 'success',
                message: '分析任务已完成！',
                duration: 5000
              });
              break;

            case 'task_failed':
              get().updateTask(task_id, {
                status: TaskStatus.FAILED,
                error: data.error_message
              });

              get().addNotification({
                id: Date.now().toString(),
                type: 'error',
                message: `任务失败: ${data.error_message}`,
                duration: 5000
              });
              break;

            case 'connection_established':
              get().addNotification({
                id: Date.now().toString(),
                type: 'info',
                message: '连接已建立',
                duration: 2000
              });
              break;

            case 'error':
              get().addNotification({
                id: Date.now().toString(),
                type: 'error',
                message: data.message || '发生未知错误',
                duration: 4000
              });
              break;
          }
        },

        updateSettings: (settings: Partial<UserSettings>) => {
          set(state => ({
            settings: { ...state.settings, ...settings }
          }));
        }
      }),
      {
        name: 'youtube-analyzer-store',
        partialize: (state) => ({
          taskHistory: state.taskHistory,
          settings: state.settings,
          ui: { 
            theme: state.ui.theme, 
            language: state.ui.language,
            sidebarOpen: state.ui.sidebarOpen
          }
        })
      }
    ),
    { name: 'youtube-analyzer' }
  )
);

export const useCurrentTask = () => useAnalysisStore(state => state.currentTask);
export const useTaskHistory = () => useAnalysisStore(state => state.taskHistory);
export const useWebSocketStatus = () => useAnalysisStore(state => state.websocket);
export const useNotifications = () => useAnalysisStore(state => state.ui.notifications);
export const useSettings = () => useAnalysisStore(state => state.settings);
export const useTheme = () => useAnalysisStore(state => state.ui.theme);
