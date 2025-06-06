import { useState, useRef, useCallback, useEffect } from 'react';
import { UseWebSocketOptions, UseWebSocketReturn } from '@/types/ui';
import { WebSocketMessage } from '@/types/api';

export function useWebSocket(options: UseWebSocketOptions): UseWebSocketReturn {
  const [connected, setConnected] = useState(false);
  const [reconnecting, setReconnecting] = useState(false);
  const [lastMessage, setLastMessage] = useState<WebSocketMessage | null>(null);
  
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | undefined>(undefined);
  const reconnectAttemptsRef = useRef(0);
  const mountedRef = useRef(true);

  const {
    taskId,
    onMessage,
    onConnect,
    onDisconnect,
    onError,
    reconnectAttempts = 5,
    reconnectInterval = 3000
  } = options;

  const connect = useCallback(() => {
    if (!mountedRef.current) return;

    try {
      const wsUrl = `${process.env.NEXT_PUBLIC_WS_URL}/ws/${taskId}`.replace('http', 'ws');
      const ws = new WebSocket(wsUrl);

      ws.onopen = () => {
        if (!mountedRef.current) return;
        
        setConnected(true);
        setReconnecting(false);
        reconnectAttemptsRef.current = 0;
        onConnect?.();
      };

      ws.onmessage = (event) => {
        if (!mountedRef.current) return;

        try {
          const message: WebSocketMessage = JSON.parse(event.data);
          setLastMessage(message);
          onMessage?.(message);
        } catch (error) {
          console.error('Failed to parse WebSocket message:', error);
        }
      };

      ws.onclose = (event) => {
        if (!mountedRef.current) return;

        setConnected(false);
        onDisconnect?.();

        if (event.code !== 1000 && reconnectAttemptsRef.current < reconnectAttempts) {
          setReconnecting(true);
          reconnectTimeoutRef.current = setTimeout(() => {
            if (mountedRef.current) {
              reconnectAttemptsRef.current++;
              connect();
            }
          }, reconnectInterval);
        } else {
          setReconnecting(false);
        }
      };

      ws.onerror = (error) => {
        if (!mountedRef.current) return;
        onError?.(error);
      };

      wsRef.current = ws;
    } catch (error) {
      console.error('WebSocket connection failed:', error);
      if (mountedRef.current) {
        onError?.(error as Event);
      }
    }
  }, [taskId, onMessage, onConnect, onDisconnect, onError, reconnectAttempts, reconnectInterval]);

  const sendMessage = useCallback((message: any) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      try {
        wsRef.current.send(JSON.stringify(message));
      } catch (error) {
        console.error('Failed to send WebSocket message:', error);
      }
    } else {
      console.warn('WebSocket is not connected. Cannot send message.');
    }
  }, []);

  const disconnect = useCallback(() => {
    mountedRef.current = false;
    
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
    }
    
    if (wsRef.current) {
      wsRef.current.close(1000, 'Component unmounting');
      wsRef.current = null;
    }
    
    setConnected(false);
    setReconnecting(false);
  }, []);

  useEffect(() => {
    mountedRef.current = true;
    connect();
    
    return () => {
      disconnect();
    };
  }, [taskId]);

  useEffect(() => {
    return () => {
      mountedRef.current = false;
      disconnect();
    };
  }, []);

  return {
    connected,
    reconnecting,
    lastMessage,
    sendMessage,
    disconnect
  };
}

export function useAnalysisWebSocket(taskId: string) {
  const { connected, reconnecting, lastMessage } = useWebSocket({
    taskId,
    onMessage: (message) => {
      console.log('Analysis WebSocket message:', message);
    },
    onConnect: () => {
      console.log('Analysis WebSocket connected');
    },
    onDisconnect: () => {
      console.log('Analysis WebSocket disconnected');
    },
    onError: (error) => {
      console.error('Analysis WebSocket error:', error);
    },
    reconnectAttempts: 5,
    reconnectInterval: 3000
  });

  return {
    connected,
    reconnecting,
    lastMessage
  };
}
