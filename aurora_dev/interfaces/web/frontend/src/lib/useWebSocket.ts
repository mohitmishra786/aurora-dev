/**
 * WebSocket hook for real-time workflow updates
 */
import { useState, useEffect, useCallback, useRef } from 'react';

const WS_URL = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000/ws';

export interface WorkflowEvent {
    type: 'state_change' | 'approval_required' | 'task_complete' | 'error';
    workflow_id: string;
    data: {
        phase?: string;
        previous_phase?: string;
        agent?: string;
        message?: string;
        approval_id?: string;
        timestamp: string;
    };
}

export interface UseWebSocketOptions {
    onMessage?: (event: WorkflowEvent) => void;
    onConnect?: () => void;
    onDisconnect?: () => void;
    onError?: (error: Event) => void;
    reconnectInterval?: number;
    maxReconnectAttempts?: number;
}

export function useWorkflowWebSocket(workflowId: string | null, options: UseWebSocketOptions = {}) {
    const [connected, setConnected] = useState(false);
    const [lastEvent, setLastEvent] = useState<WorkflowEvent | null>(null);
    const [reconnectAttempts, setReconnectAttempts] = useState(0);

    const wsRef = useRef<WebSocket | null>(null);
    const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);

    const {
        onMessage,
        onConnect,
        onDisconnect,
        onError,
        reconnectInterval = 3000,
        maxReconnectAttempts = 5,
    } = options;

    const connect = useCallback(() => {
        if (!workflowId) return;

        // Close existing connection
        if (wsRef.current) {
            wsRef.current.close();
        }

        try {
            const ws = new WebSocket(`${WS_URL}/workflows/${workflowId}`);

            ws.onopen = () => {
                setConnected(true);
                setReconnectAttempts(0);
                onConnect?.();
            };

            ws.onmessage = (event) => {
                try {
                    const data: WorkflowEvent = JSON.parse(event.data);
                    setLastEvent(data);
                    onMessage?.(data);
                } catch (e) {
                    console.error('Failed to parse WebSocket message:', e);
                }
            };

            ws.onclose = () => {
                setConnected(false);
                onDisconnect?.();

                // Auto-reconnect
                if (reconnectAttempts < maxReconnectAttempts) {
                    reconnectTimeoutRef.current = setTimeout(() => {
                        setReconnectAttempts((prev) => prev + 1);
                        connect();
                    }, reconnectInterval);
                }
            };

            ws.onerror = (error) => {
                onError?.(error);
            };

            wsRef.current = ws;
        } catch (e) {
            console.error('WebSocket connection failed:', e);
        }
    }, [workflowId, onMessage, onConnect, onDisconnect, onError, reconnectInterval, maxReconnectAttempts, reconnectAttempts]);

    const disconnect = useCallback(() => {
        if (reconnectTimeoutRef.current) {
            clearTimeout(reconnectTimeoutRef.current);
        }
        if (wsRef.current) {
            wsRef.current.close();
            wsRef.current = null;
        }
        setConnected(false);
    }, []);

    const sendMessage = useCallback((message: object) => {
        if (wsRef.current?.readyState === WebSocket.OPEN) {
            wsRef.current.send(JSON.stringify(message));
        }
    }, []);

    useEffect(() => {
        connect();
        return () => disconnect();
    }, [connect, disconnect]);

    return {
        connected,
        lastEvent,
        reconnectAttempts,
        sendMessage,
        reconnect: connect,
        disconnect,
    };
}
