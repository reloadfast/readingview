import { createContext, useContext, useEffect, useState, type ReactNode } from "react";
import type { QueryClient } from "@tanstack/react-query";

interface WebSocketContextValue {
  connected: boolean;
}

const WebSocketContext = createContext<WebSocketContextValue>({ connected: false });

export function WebSocketProvider({
  queryClient,
  children,
}: {
  queryClient: QueryClient;
  children: ReactNode;
}) {
  const [connected, setConnected] = useState(false);

  useEffect(() => {
    let alive = true;
    let ws: WebSocket | null = null;
    let retryTimer: ReturnType<typeof setTimeout> | null = null;

    function connect() {
      const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
      ws = new WebSocket(`${protocol}//${window.location.host}/api/ws`);

      ws.onopen = () => {
        if (alive) setConnected(true);
      };

      ws.onclose = () => {
        if (!alive) return;
        setConnected(false);
        retryTimer = setTimeout(connect, 5_000);
      };

      ws.onerror = () => ws?.close();

      ws.onmessage = (event) => {
        if (!alive) return;
        try {
          const msg = JSON.parse(event.data as string) as { type: string };
          if (msg.type === "library_item_updated") {
            void queryClient.invalidateQueries({ queryKey: ["library"] });
          } else if (msg.type === "user_progress_updated") {
            void queryClient.invalidateQueries({ queryKey: ["library", "in-progress"] });
          }
        } catch {
          // ignore malformed messages
        }
      };
    }

    connect();

    return () => {
      alive = false;
      if (retryTimer !== null) clearTimeout(retryTimer);
      ws?.close();
    };
  }, [queryClient]);

  return (
    <WebSocketContext.Provider value={{ connected }}>
      {children}
    </WebSocketContext.Provider>
  );
}

export function useWebSocket(): WebSocketContextValue {
  return useContext(WebSocketContext);
}
