const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export interface Signal {
  action: "HOLD" | "BUY" | "SELL" | "STOP_LOSS";
  signal_type: string | null;
  amount: number;
  reason: string;
  drawdown_pct: number;
  current_price: number;
  days_since_buy: number | null;
  total_invested: number;
  current_value: number;
  pnl_pct: number;
  timestamp: string;
}

export interface Drawdown {
  current_price: number;
  peak_price: number;
  drawdown_pct: number;
  peak_date: string;
}

export interface Portfolio {
  total_invested: number;
  current_value: number;
  total_shares: number;
  pnl_euro: number;
  pnl_pct: number;
  positions_count: number;
  remaining_capacity: number;
}

export interface Guiderails {
  max_position: number;
  stop_loss_pct: number;
  profit_take_pct: number;
  drawdown_threshold: number;
}

export interface Status {
  ticker: string;
  current_price: number;
  drawdown: Drawdown;
  signal: Signal;
  portfolio: Portfolio;
  guiderails: Guiderails;
  last_buy_date: string | null;
}

export interface HistoryPoint {
  date: string;
  price: number;
  peak: number;
  drawdown: number;
}

export interface History {
  ticker: string;
  data: HistoryPoint[];
  current: HistoryPoint | null;
}

async function fetchApi<T>(endpoint: string, options: RequestInit = {}): Promise<{ data?: T; error?: string }> {
  try {
    const response = await fetch(`${API_BASE}${endpoint}`, {
      ...options,
      headers: {
        "Content-Type": "application/json",
        ...options.headers,
      },
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      return { error: errorData.error || errorData.detail || `HTTP ${response.status}` };
    }

    const data = await response.json();
    return { data };
  } catch {
    return { error: "Network error. Is the backend running?" };
  }
}

export async function getSignal() {
  return fetchApi<Signal>("/api/signal");
}

export async function getStatus() {
  return fetchApi<Status>("/api/status");
}

export async function executeAction(action: "buy" | "sell", amount?: number) {
  const url = amount ? `/api/execute/${action}?amount=${amount}` : `/api/execute/${action}`;
  return fetchApi<{ status: string; action: string; amount?: number; price?: number }>(
    url,
    { method: "POST" }
  );
}

export async function resetState() {
  return fetchApi<{ status: string }>("/api/reset", { method: "POST" });
}

export async function getHistory() {
  return fetchApi<History>("/api/history");
}
