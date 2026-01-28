const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface ApiResponse<T> {
  data?: T;
  error?: string;
}

async function fetchApi<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<ApiResponse<T>> {
  const token = typeof window !== "undefined" ? localStorage.getItem("token") : null;

  const headers: HeadersInit = {
    "Content-Type": "application/json",
    ...(token && { Authorization: `Bearer ${token}` }),
    ...options.headers,
  };

  try {
    const response = await fetch(`${API_BASE}${endpoint}`, {
      ...options,
      headers,
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      return { error: errorData.detail || `HTTP ${response.status}` };
    }

    const data = await response.json();
    return { data };
  } catch {
    return { error: "Network error. Please try again." };
  }
}

// Auth
export async function register(email: string, password: string, budget: number) {
  return fetchApi<{ access_token: string }>("/api/user/register", {
    method: "POST",
    body: JSON.stringify({ email, password, budget }),
  });
}

export async function login(email: string, password: string) {
  return fetchApi<{ access_token: string }>("/api/user/login", {
    method: "POST",
    body: JSON.stringify({ email, password }),
  });
}

export async function getMe() {
  return fetchApi<{
    id: number;
    email: string;
    budget: number;
    created_at: string;
  }>("/api/user/me");
}

export async function updateBudget(budget: number) {
  return fetchApi<{ budget: number }>("/api/user/budget", {
    method: "PATCH",
    body: JSON.stringify({ budget }),
  });
}

// Digest
export interface StockPick {
  ticker: string;
  name: string;
  score: number;
  signal: string;
  current_price: number | null;
  day_change_pct: number | null;
  explanation: string;
  suggested_position: number;
  news_headlines: string[];
  breakdown: {
    technical: { score: number; weight: number; contribution: number };
    sentiment: { score: number; weight: number; contribution: number };
    fundamental: { score: number; weight: number; contribution: number };
  };
}

export interface Digest {
  date: string;
  generated_at: string | null;
  buy: StockPick[];
  sell: StockPick[];
  message?: string;
}

export async function getLatestDigest() {
  return fetchApi<Digest>("/api/digest/latest");
}

export async function getDigestByDate(date: string) {
  return fetchApi<Digest>(`/api/digest/${date}`);
}

export async function generateDigest() {
  return fetchApi<{ status: string; date: string; buy_count: number; sell_count: number }>(
    "/api/digest/generate",
    { method: "POST" }
  );
}

// Verification
export interface VerificationStats {
  total_predictions: number;
  verified_1d: number;
  verified_7d: number;
  verified_30d: number;
  accuracy_1d: number | null;
  accuracy_7d: number | null;
  accuracy_30d: number | null;
  avg_return_1d: number | null;
  avg_return_7d: number | null;
  avg_return_30d: number | null;
  is_unlocked: boolean;
  unlock_reason: string | null;
  last_updated: string | null;
}

// Alias for frontend convenience
export type SimplifiedStats = VerificationStats;

export interface VerificationStatus {
  is_unlocked: boolean;
  mode: "observation" | "active";
  message: string;
  stats: VerificationStats | null;
  unlock_requirements: {
    min_predictions: number;
    min_accuracy: number;
    current_predictions: number;
    current_accuracy: number | null;
  };
}

export interface Prediction {
  id: number;
  ticker: string;
  company_name: string;
  direction: "buy" | "sell";
  score: number;
  prediction_date: string;
  price_at_prediction: number;
  price_after_1d: number | null;
  verified_1d: boolean;
  correct_1d: boolean | null;
  return_1d: number | null;
  price_after_7d: number | null;
  verified_7d: boolean;
  correct_7d: boolean | null;
  return_7d: number | null;
  price_after_30d: number | null;
  verified_30d: boolean;
  correct_30d: boolean | null;
  return_30d: number | null;
}

export async function getVerificationStats() {
  return fetchApi<VerificationStats>("/api/verification/stats");
}

export async function getVerificationStatus() {
  return fetchApi<VerificationStatus>("/api/verification/status");
}

export async function getPredictions(limit: number = 50, offset: number = 0) {
  return fetchApi<Prediction[]>(`/api/verification/predictions?limit=${limit}&offset=${offset}`);
}

export async function runVerification() {
  return fetchApi<{ verified_1d: number; verified_7d: number; verified_30d: number; errors: number }>(
    "/api/verification/run",
    { method: "POST" }
  );
}
