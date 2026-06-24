const WS_BASE = import.meta.env.VITE_WS_URL ?? import.meta.env.VITE_API_URL?.replace(/^http/, "ws") ?? "ws://localhost:8000";

type MessageHandler = (data: unknown) => void;

export class TenantSocket {
  private ws: WebSocket | null = null;
  private handlers = new Set<MessageHandler>();
  private reconnectTimer: ReturnType<typeof setTimeout> | null = null;
  private shouldReconnect = true;
  private retries = 0;
  private readonly maxRetries: number;
  private token: string;
  private path: string;

  constructor(path: string, token: string, maxRetries = 5) {
    this.path = path;
    this.token = token;
    this.maxRetries = maxRetries;
  }

  connect() {
    const url = `${WS_BASE}${this.path}?token=${encodeURIComponent(this.token)}`;
    this.ws = new WebSocket(url);

    this.ws.onopen = () => {
      this.retries = 0;
    };

    this.ws.onmessage = (ev) => {
      try {
        const data = JSON.parse(ev.data);
        this.handlers.forEach((h) => h(data));
      } catch {
        // ignore malformed frames
      }
    };

    this.ws.onclose = () => {
      if (this.shouldReconnect && this.retries < this.maxRetries) {
        this.retries++;
        this.reconnectTimer = setTimeout(() => this.connect(), 3000);
      }
    };

    this.ws.onerror = () => {
      this.ws?.close();
    };
  }

  on(handler: MessageHandler) {
    this.handlers.add(handler);
    return () => this.handlers.delete(handler);
  }

  disconnect() {
    this.shouldReconnect = false;
    if (this.reconnectTimer) clearTimeout(this.reconnectTimer);
    this.ws?.close();
    this.ws = null;
  }
}

export function createKanbanSocket(token: string): TenantSocket {
  return new TenantSocket("/crm/ws/kanban", token);
}
