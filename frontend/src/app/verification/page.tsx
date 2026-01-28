"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import {
  getMe,
  getVerificationStatus,
  getPredictions,
  type VerificationStatus,
  type Prediction,
} from "@/lib/api";

function StatCard({
  label,
  value,
  subValue,
  color = "gray",
}: {
  label: string;
  value: string | number;
  subValue?: string;
  color?: "green" | "red" | "blue" | "gray" | "yellow";
}) {
  const colorClasses = {
    green: "bg-green-50 border-green-200 text-green-700",
    red: "bg-red-50 border-red-200 text-red-700",
    blue: "bg-blue-50 border-blue-200 text-blue-700",
    gray: "bg-gray-50 border-gray-200 text-gray-700",
    yellow: "bg-yellow-50 border-yellow-200 text-yellow-700",
  };

  return (
    <div className={`rounded-lg border p-4 ${colorClasses[color]}`}>
      <div className="text-sm font-medium opacity-80">{label}</div>
      <div className="text-2xl font-bold mt-1">{value}</div>
      {subValue && <div className="text-xs mt-1 opacity-70">{subValue}</div>}
    </div>
  );
}

function AccuracyBar({ label, accuracy, count }: { label: string; accuracy: number | null; count: number }) {
  const pct = accuracy !== null ? accuracy : 0;
  const isGood = pct >= 55;

  return (
    <div className="mb-4">
      <div className="flex justify-between text-sm mb-1">
        <span className="font-medium">{label}</span>
        <span className={isGood ? "text-green-600" : "text-gray-600"}>
          {accuracy !== null ? `${accuracy.toFixed(1)}%` : "n.v.t."} ({count} geverifieerd)
        </span>
      </div>
      <div className="h-3 bg-gray-200 rounded-full overflow-hidden">
        <div
          className={`h-full transition-all duration-500 ${isGood ? "bg-green-500" : "bg-yellow-500"}`}
          style={{ width: `${Math.min(pct, 100)}%` }}
        />
      </div>
      {accuracy !== null && (
        <div className="flex justify-between text-xs text-gray-500 mt-1">
          <span>0%</span>
          <span className="text-green-600">55% (unlock)</span>
          <span>100%</span>
        </div>
      )}
    </div>
  );
}

function PredictionRow({ prediction }: { prediction: Prediction }) {
  const isBuy = prediction.direction === "buy";

  const getStatusIcon = (correct: boolean | null, verified: boolean) => {
    if (!verified) return <span className="text-gray-400">⏳</span>;
    if (correct === true) return <span className="text-green-600">✓</span>;
    if (correct === false) return <span className="text-red-600">✗</span>;
    return <span className="text-gray-400">-</span>;
  };

  const formatReturn = (ret: number | null) => {
    if (ret === null) return "-";
    const sign = ret >= 0 ? "+" : "";
    return `${sign}${ret.toFixed(2)}%`;
  };

  return (
    <tr className="border-b border-gray-100 hover:bg-gray-50">
      <td className="py-3 px-4">
        <div className="font-medium">{prediction.ticker}</div>
        <div className="text-xs text-gray-500">{prediction.company_name}</div>
      </td>
      <td className="py-3 px-4">
        <span
          className={`text-xs px-2 py-0.5 rounded-full ${
            isBuy ? "bg-green-100 text-green-700" : "bg-red-100 text-red-700"
          }`}
        >
          {isBuy ? "KOOP" : "VERKOOP"}
        </span>
      </td>
      <td className="py-3 px-4 text-sm">
        {new Date(prediction.prediction_date).toLocaleDateString("nl-NL")}
      </td>
      <td className="py-3 px-4 text-sm">€{prediction.price_at_prediction.toFixed(2)}</td>
      <td className="py-3 px-4 text-center">
        <div className="flex items-center justify-center gap-1">
          {getStatusIcon(prediction.correct_1d, prediction.verified_1d)}
          <span className={`text-xs ${prediction.return_1d !== null && prediction.return_1d >= 0 ? "text-green-600" : "text-red-600"}`}>
            {formatReturn(prediction.return_1d)}
          </span>
        </div>
      </td>
      <td className="py-3 px-4 text-center">
        <div className="flex items-center justify-center gap-1">
          {getStatusIcon(prediction.correct_7d, prediction.verified_7d)}
          <span className={`text-xs ${prediction.return_7d !== null && prediction.return_7d >= 0 ? "text-green-600" : "text-red-600"}`}>
            {formatReturn(prediction.return_7d)}
          </span>
        </div>
      </td>
      <td className="py-3 px-4 text-center">
        <div className="flex items-center justify-center gap-1">
          {getStatusIcon(prediction.correct_30d, prediction.verified_30d)}
          <span className={`text-xs ${prediction.return_30d !== null && prediction.return_30d >= 0 ? "text-green-600" : "text-red-600"}`}>
            {formatReturn(prediction.return_30d)}
          </span>
        </div>
      </td>
    </tr>
  );
}

export default function VerificationPage() {
  const router = useRouter();
  const [user, setUser] = useState<{ email: string } | null>(null);
  const [status, setStatus] = useState<VerificationStatus | null>(null);
  const [predictions, setPredictions] = useState<Prediction[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem("token");
    if (!token) {
      router.push("/login");
      return;
    }

    const loadData = async () => {
      const userResult = await getMe();
      if (userResult.error) {
        localStorage.removeItem("token");
        router.push("/login");
        return;
      }
      setUser(userResult.data!);

      const statusResult = await getVerificationStatus();
      if (statusResult.data) {
        setStatus(statusResult.data);
      }

      const predictionsResult = await getPredictions(100);
      if (predictionsResult.data) {
        setPredictions(predictionsResult.data);
      }

      setLoading(false);
    };

    loadData();
  }, [router]);

  const handleLogout = () => {
    localStorage.removeItem("token");
    router.push("/");
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-gray-600">Laden...</div>
      </div>
    );
  }

  const stats = status?.stats;
  const isUnlocked = status?.is_unlocked || false;

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white border-b border-gray-200">
        <div className="max-w-6xl mx-auto px-4 py-4 flex justify-between items-center">
          <h1 className="text-xl font-bold text-gray-900">StockPulse AI</h1>
          <div className="flex items-center gap-4">
            <Link href="/dashboard" className="text-sm text-blue-600 hover:underline">
              Dashboard
            </Link>
            <span className="text-sm text-gray-600">{user?.email}</span>
            <button
              onClick={handleLogout}
              className="text-sm text-gray-600 hover:text-gray-900"
            >
              Uitloggen
            </button>
          </div>
        </div>
      </header>

      <main className="max-w-6xl mx-auto px-4 py-8">
        {/* Status banner */}
        <div
          className={`rounded-lg p-4 mb-8 ${
            isUnlocked
              ? "bg-green-50 border border-green-200"
              : "bg-yellow-50 border border-yellow-200"
          }`}
        >
          <div className="flex items-center gap-3">
            <span className="text-2xl">{isUnlocked ? "🔓" : "🔒"}</span>
            <div>
              <div className={`font-bold ${isUnlocked ? "text-green-700" : "text-yellow-700"}`}>
                {isUnlocked ? "Systeem actief" : "Observatiemodus"}
              </div>
              <div className={`text-sm ${isUnlocked ? "text-green-600" : "text-yellow-600"}`}>
                {status?.message}
              </div>
            </div>
          </div>

          {!isUnlocked && status?.unlock_requirements && (
            <div className="mt-4 pt-4 border-t border-yellow-200">
              <div className="text-sm text-yellow-700">
                <strong>Unlock vereisten:</strong>
                <ul className="mt-2 space-y-1">
                  <li>
                    • Minimaal {status.unlock_requirements.min_predictions} voorspellingen
                    (huidig: {status.unlock_requirements.current_predictions})
                  </li>
                  <li>
                    • Minimaal {status.unlock_requirements.min_accuracy}% accuracy op 7-dagen horizon
                    (huidig: {status.unlock_requirements.current_accuracy?.toFixed(1) || "n.v.t."}%)
                  </li>
                </ul>
              </div>
            </div>
          )}
        </div>

        {/* Stats overview */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
          <StatCard
            label="Totaal voorspellingen"
            value={stats?.total_predictions || 0}
            color="blue"
          />
          <StatCard
            label="Geverifieerd (1d)"
            value={stats?.verified_1d || 0}
            subValue={stats?.accuracy_1d ? `${stats.accuracy_1d.toFixed(1)}% correct` : undefined}
            color={stats?.accuracy_1d && stats.accuracy_1d >= 55 ? "green" : "gray"}
          />
          <StatCard
            label="Geverifieerd (7d)"
            value={stats?.verified_7d || 0}
            subValue={stats?.accuracy_7d ? `${stats.accuracy_7d.toFixed(1)}% correct` : undefined}
            color={stats?.accuracy_7d && stats.accuracy_7d >= 55 ? "green" : "gray"}
          />
          <StatCard
            label="Geverifieerd (30d)"
            value={stats?.verified_30d || 0}
            subValue={stats?.accuracy_30d ? `${stats.accuracy_30d.toFixed(1)}% correct` : undefined}
            color={stats?.accuracy_30d && stats.accuracy_30d >= 55 ? "green" : "gray"}
          />
        </div>

        {/* Accuracy bars */}
        <div className="bg-white rounded-lg border border-gray-200 p-6 mb-8">
          <h2 className="text-lg font-bold text-gray-900 mb-4">Accuracy per tijdshorizon</h2>
          <AccuracyBar label="1-dag voorspellingen" accuracy={stats?.accuracy_1d || null} count={stats?.verified_1d || 0} />
          <AccuracyBar label="7-dagen voorspellingen" accuracy={stats?.accuracy_7d || null} count={stats?.verified_7d || 0} />
          <AccuracyBar label="30-dagen voorspellingen" accuracy={stats?.accuracy_30d || null} count={stats?.verified_30d || 0} />
        </div>

        {/* Average returns */}
        {(stats?.avg_return_1d !== null || stats?.avg_return_7d !== null || stats?.avg_return_30d !== null) && (
          <div className="bg-white rounded-lg border border-gray-200 p-6 mb-8">
            <h2 className="text-lg font-bold text-gray-900 mb-4">Gemiddeld rendement</h2>
            <div className="grid grid-cols-3 gap-4 text-center">
              <div>
                <div className="text-sm text-gray-600">1 dag</div>
                <div className={`text-xl font-bold ${stats?.avg_return_1d && stats.avg_return_1d >= 0 ? "text-green-600" : "text-red-600"}`}>
                  {stats?.avg_return_1d !== null ? `${stats.avg_return_1d >= 0 ? "+" : ""}${stats.avg_return_1d.toFixed(2)}%` : "-"}
                </div>
              </div>
              <div>
                <div className="text-sm text-gray-600">7 dagen</div>
                <div className={`text-xl font-bold ${stats?.avg_return_7d && stats.avg_return_7d >= 0 ? "text-green-600" : "text-red-600"}`}>
                  {stats?.avg_return_7d !== null ? `${stats.avg_return_7d >= 0 ? "+" : ""}${stats.avg_return_7d.toFixed(2)}%` : "-"}
                </div>
              </div>
              <div>
                <div className="text-sm text-gray-600">30 dagen</div>
                <div className={`text-xl font-bold ${stats?.avg_return_30d && stats.avg_return_30d >= 0 ? "text-green-600" : "text-red-600"}`}>
                  {stats?.avg_return_30d !== null ? `${stats.avg_return_30d >= 0 ? "+" : ""}${stats.avg_return_30d.toFixed(2)}%` : "-"}
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Predictions table */}
        <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
          <div className="p-4 border-b border-gray-200">
            <h2 className="text-lg font-bold text-gray-900">Voorspellingshistorie</h2>
            <p className="text-sm text-gray-600 mt-1">
              Alle voorspellingen met hun verificatiestatus
            </p>
          </div>

          {predictions.length === 0 ? (
            <div className="p-8 text-center text-gray-500">
              Nog geen voorspellingen. Genereer eerst een digest om te beginnen.
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="bg-gray-50 text-left">
                  <tr>
                    <th className="py-3 px-4 font-medium text-gray-700">Aandeel</th>
                    <th className="py-3 px-4 font-medium text-gray-700">Signaal</th>
                    <th className="py-3 px-4 font-medium text-gray-700">Datum</th>
                    <th className="py-3 px-4 font-medium text-gray-700">Prijs</th>
                    <th className="py-3 px-4 font-medium text-gray-700 text-center">1d</th>
                    <th className="py-3 px-4 font-medium text-gray-700 text-center">7d</th>
                    <th className="py-3 px-4 font-medium text-gray-700 text-center">30d</th>
                  </tr>
                </thead>
                <tbody>
                  {predictions.map((prediction) => (
                    <PredictionRow key={prediction.id} prediction={prediction} />
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

        <div className="mt-8 text-center text-sm text-gray-500">
          <p>
            ⚠️ Het systeem ontgrendelt automatisch wanneer de accuracy &gt;55% bereikt
            over minimaal 50 geverifieerde voorspellingen op de 7-dagen horizon.
          </p>
        </div>
      </main>
    </div>
  );
}
