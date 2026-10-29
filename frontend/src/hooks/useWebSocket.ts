import { useEffect, useRef, useState, useCallback } from 'react';

export interface WebSocketOptions {
  autoReconnect?: boolean;
  maxReconnectAttempts?: number;
  heartbeatIntervalMs?: number;
  onMessage?: (data: any) => void;
  onOpen?: () => void;
  onClose?: () => void;
  onError?: (err: Event) => void;
}

export function useWebSocket(url: string | null, options: WebSocketOptions = {}) {
  const {
    autoReconnect = true,
    maxReconnectAttempts = 5,
    heartbeatIntervalMs = 25000,
    onMessage,
    onOpen,
    onClose,
    onError,
  } = options;

  const [isConnected, setIsConnected] = useState(false);
  const [reconnectCount, setReconnectCount] = useState(0);
  const wsRef = useRef<WebSocket | null>(null);
  const heartbeatTimerRef = useRef<any>(null);
  const reconnectTimerRef = useRef<any>(null);

  const startHeartbeat = useCallback(() => {
    if (heartbeatTimerRef.current) clearInterval(heartbeatTimerRef.current);
    heartbeatTimerRef.current = setInterval(() => {
      if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
        wsRef.current.send(JSON.stringify({ type: 'ping', timestamp: Date.now() }));
      }
    }, heartbeatIntervalMs);
  }, [heartbeatIntervalMs]);

  const stopHeartbeat = useCallback(() => {
    if (heartbeatTimerRef.current) {
      clearInterval(heartbeatTimerRef.current);
      heartbeatTimerRef.current = null;
    }
  }, []);

  const connect = useCallback(() => {
    if (!url) return;

    try {
      const ws = new WebSocket(url);
      wsRef.current = ws;

      ws.onopen = () => {
        setIsConnected(true);
        setReconnectCount(0);
        startHeartbeat();
        onOpen?.();
      };

      ws.onmessage = (event) => {
        try {
          const parsed = JSON.parse(event.data);
          // Auto reply pong if server pings
          if (parsed.type === 'ping') {
            ws.send(JSON.stringify({ type: 'pong', timestamp: Date.now() }));
            return;
          }
          if (parsed.type === 'pong') return;

          onMessage?.(parsed);
        } catch (e) {
          onMessage?.(event.data);
        }
      };

      ws.onclose = () => {
        setIsConnected(false);
        stopHeartbeat();
        onClose?.();

        if (autoReconnect && reconnectCount < maxReconnectAttempts) {
          const delay = Math.min(1000 * Math.pow(2, reconnectCount), 10000);
          reconnectTimerRef.current = setTimeout(() => {
            setReconnectCount((prev) => prev + 1);
            connect();
          }, delay);
        }
      };

      ws.onerror = (err) => {
        onError?.(err);
      };
    } catch (e) {
      console.error('[WebSocket] Connection instantiation failed', e);
    }
  }, [url, autoReconnect, maxReconnectAttempts, reconnectCount, startHeartbeat, stopHeartbeat, onOpen, onMessage, onClose, onError]);

  const sendMessage = useCallback((data: any) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      const payload = typeof data === 'string' ? data : JSON.stringify(data);
      wsRef.current.send(payload);
      return true;
    }
    return false;
  }, []);

  useEffect(() => {
    connect();
    return () => {
      stopHeartbeat();
      if (reconnectTimerRef.current) clearTimeout(reconnectTimerRef.current);
      if (wsRef.current) {
        wsRef.current.close();
        wsRef.current = null;
      }
    };
  }, [url]);

  return { isConnected, sendMessage, reconnectCount };
}
