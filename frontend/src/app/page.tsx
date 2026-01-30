"use client";

import { useState, useEffect } from "react";
import { getStatus, executeAction, type Status } from "@/lib/api";

function SignalCard({ status }: { status: Status }) {
  const signal = status.signal;
  const [executing, setExecuting] = useState(false);
  const [message, setMessage] = useState("");

  const getSignalColor = () => {
    switch (signal.action) {
      case "BUY":
        return "bg-green-600";
      case "SELL":
        return "bg-blue-600";
      case "STOP_LOSS":
        return "bg-red-600";
      default:
        return "bg-gray-600";
    }
  };

  const getSignalEmoji = () => {
    switch (signal.action) {
      case "BUY":
        return signal.signal_type === "aggressive_buy" ? "🚀" : "📈";
      case "SELL":
        return "💰";
      case "STOP_LOSS":
        return "🚨";
      default:
        return "⏸️";
    }
  };

  const handleExecute = async () => {
    if (signal.action !== "BUY" && signal.action !== "SELL") return;

    setExecuting(true);
    const action = signal.action === "BUY" ? "buy" : "sell";
    const result = await executeAction(action, signal.amount);

    if (result.error) {
      setMessage(`Error: ${result.error}`);
    } else {
      setMessage(`✅ ${result.data?.action} executed at $${result.data?.price?.toFixed(2)}`);
      // Refresh after 2 seconds
      setTimeout(() => window.location.reload(), 2000);
    }
    setExecuting(false);
  };

  return (
    <div className={`${getSignalColor()} rounded-xl p-6 text-white`}>
      <div className="flex justify-between items-start mb-4">
        <div>
          <span className="text-4xl">{getSignalEmoji()}</span>
          <h2 className="text-2xl font-bold mt-2">{signal.action}</h2>
          {signal.signal_type && (
            <span className="text-sm opacity-80">
              {signal.signal_type.replace("_", " ").toUpperCase()}
            </span>
          )}
        </div>
        {signal.amount > 0 && (
          <div className="text-right">
            <div className="text-3xl font-bold">€{signal.amount.toFixed(0)}</div>
            <div className="text-sm opacity-80">
              @ ${signal.current_price.toFixed(2)}
            </div>
          </div>
        )}
      </div>

      <p className="text-lg mb-4">{signal.reason}</p>

      {(signal.action === "BUY" || signal.action === "SELL") && (
        <button
          onClick={handleExecute}
          disabled={executing}
          className="w-full bg-white/20 hover:bg-white/30 py-3 rounded-lg font-medium transition disabled:opacity-50"
        >
          {executing ? "Recording..." : `I executed this ${signal.action}`}
        </button>
      )}

      {message && (
        <div className="mt-3 text-sm bg-white/10 rounded p-2">{message}</div>
      )}
    </div>
  );
}

function MetricCard({
  label,
  value,
  subvalue,
  color = "text-white",
}: {
  label: string;
  value: string;
  subvalue?: string;
  color?: string;
}) {
  return (
    <div className="bg-gray-800 rounded-lg p-4">
      <div className="text-gray-400 text-sm mb-1">{label}</div>
      <div className={`text-2xl font-bold ${color}`}>{value}</div>
      {subvalue && <div className="text-gray-500 text-sm">{subvalue}</div>}
    </div>
  );
}

function GuiderailsBar({ status }: { status: Status }) {
  const { portfolio, guiderails } = status;
  const positionPct = (portfolio.total_invested / guiderails.max_position) * 100;

  return (
    <div className="bg-gray-800 rounded-lg p-4">
      <div className="flex justify-between text-sm mb-2">
        <span className="text-gray-400">Position</span>
        <span>
          €{portfolio.total_invested.toFixed(0)} / €{guiderails.max_position}
        </span>
      </div>
      <div className="w-full bg-gray-700 rounded-full h-3">
        <div
          className="bg-blue-500 h-3 rounded-full transition-all"
          style={{ width: `${Math.min(positionPct, 100)}%` }}
        />
      </div>
      <div className="flex justify-between text-xs text-gray-500 mt-1">
        <span>€{portfolio.remaining_capacity.toFixed(0)} remaining</span>
        <span>{positionPct.toFixed(0)}%</span>
      </div>
    </div>
  );
}

export default function Home() {
  const [status, setStatus] = useState<Status | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    const loadData = async () => {
      const result = await getStatus();
      if (result.error) {
        setError(result.error);
      } else if (result.data) {
        setStatus(result.data);
      }
      setLoading(false);
    };

    loadData();
    // Refresh every 5 minutes
    const interval = setInterval(loadData, 5 * 60 * 1000);
    return () => clearInterval(interval);
  }, []);

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-gray-400">Loading strategy...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center p-4">
        <div className="bg-red-900/50 border border-red-700 rounded-lg p-6 max-w-md text-center">
          <h2 className="text-xl font-bold text-red-400 mb-2">Connection Error</h2>
          <p className="text-gray-300 mb-4">{error}</p>
          <p className="text-sm text-gray-500">
            Make sure the backend is running:<br />
            <code className="bg-gray-800 px-2 py-1 rounded">cd backend && uvicorn app.main:app</code>
          </p>
        </div>
      </div>
    );
  }

  if (!status) return null;

  const { signal, portfolio, drawdown } = status;

  return (
    <div className="min-h-screen p-4 md:p-8">
      <div className="max-w-2xl mx-auto">
        {/* Header */}
        <div className="flex justify-between items-center mb-6">
          <div>
            <h1 className="text-2xl font-bold">StockPulse</h1>
            <p className="text-gray-400 text-sm">Drawdown Strategy • {status.ticker}</p>
          </div>
          <div className="text-right">
            <div className="text-2xl font-bold">${status.current_price.toFixed(2)}</div>
            <div
              className={`text-sm ${
                drawdown.drawdown_pct > 20 ? "text-red-400" : "text-gray-400"
              }`}
            >
              {drawdown.drawdown_pct.toFixed(1)}% from peak
            </div>
          </div>
        </div>

        {/* Signal Card */}
        <div className="mb-6">
          <SignalCard status={status} />
        </div>

        {/* Portfolio Metrics */}
        <div className="grid grid-cols-2 gap-4 mb-6">
          <MetricCard
            label="Total Invested"
            value={`€${portfolio.total_invested.toFixed(0)}`}
            subvalue={`${portfolio.positions_count} positions`}
          />
          <MetricCard
            label="Current Value"
            value={`€${portfolio.current_value.toFixed(0)}`}
            subvalue={`${portfolio.total_shares.toFixed(2)} shares`}
          />
          <MetricCard
            label="P&L"
            value={`€${portfolio.pnl_euro.toFixed(0)}`}
            subvalue={`${portfolio.pnl_pct >= 0 ? "+" : ""}${portfolio.pnl_pct.toFixed(1)}%`}
            color={portfolio.pnl_pct >= 0 ? "text-green-400" : "text-red-400"}
          />
          <MetricCard
            label="Days Since Buy"
            value={signal.days_since_buy?.toString() || "-"}
            subvalue={status.last_buy_date || "No buys yet"}
          />
        </div>

        {/* Guiderails */}
        <div className="mb-6">
          <h3 className="text-gray-400 text-sm mb-2">Guiderails</h3>
          <GuiderailsBar status={status} />
        </div>

        {/* Strategy Rules */}
        <div className="bg-gray-800 rounded-lg p-4 text-sm">
          <h3 className="font-medium mb-3">Strategy Rules</h3>
          <div className="space-y-2 text-gray-400">
            <div className="flex justify-between">
              <span>📈 Normal buy (DD &lt;20%)</span>
              <span>€500 / 7 days</span>
            </div>
            <div className="flex justify-between">
              <span>🚀 Aggressive buy (DD &gt;20%)</span>
              <span>€1500 / 5 days</span>
            </div>
            <div className="flex justify-between">
              <span>💰 Profit take (&gt;40%)</span>
              <span>Sell 25%</span>
            </div>
            <div className="flex justify-between">
              <span>🚨 Stop loss</span>
              <span>-25% alert</span>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="mt-8 text-center text-xs text-gray-600">
          <p>Last updated: {new Date(signal.timestamp).toLocaleString("nl-NL")}</p>
          <p className="mt-1">⚠️ Not financial advice. Execute trades manually.</p>
        </div>
      </div>
    </div>
  );
}
