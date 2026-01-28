"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { getMe, getLatestDigest, updateBudget, getVerificationStatus, type Digest, type StockPick, type VerificationStatus } from "@/lib/api";

function StockCard({ pick, type }: { pick: StockPick; type: "buy" | "sell" }) {
  const [showDetails, setShowDetails] = useState(false);
  const isBuy = type === "buy";

  return (
    <div className="bg-white rounded-lg border border-gray-200 p-4 hover:shadow-md transition">
      <div className="flex justify-between items-start">
        <div>
          <div className="flex items-center gap-2">
            <span className="font-bold text-lg">{pick.ticker}</span>
            <span
              className={`text-xs px-2 py-0.5 rounded-full ${
                isBuy ? "bg-green-100 text-green-700" : "bg-red-100 text-red-700"
              }`}
            >
              {pick.signal}
            </span>
          </div>
          <p className="text-sm text-gray-600">{pick.name}</p>
        </div>
        <div className="text-right">
          <div className={`text-xl font-bold ${isBuy ? "text-green-600" : "text-red-600"}`}>
            {pick.score > 0 ? "+" : ""}{pick.score}
          </div>
          {pick.current_price && (
            <div className="text-sm text-gray-500">
              ${pick.current_price.toFixed(2)}
              {pick.day_change_pct !== null && (
                <span className={pick.day_change_pct >= 0 ? "text-green-600" : "text-red-600"}>
                  {" "}({pick.day_change_pct >= 0 ? "+" : ""}{pick.day_change_pct}%)
                </span>
              )}
            </div>
          )}
        </div>
      </div>

      <p className="mt-3 text-sm text-gray-700">{pick.explanation}</p>

      {pick.suggested_position > 0 && (
        <div className="mt-3 text-sm">
          <span className="text-gray-500">Voorgestelde positie: </span>
          <span className="font-medium">€{pick.suggested_position.toFixed(0)}</span>
        </div>
      )}

      <button
        onClick={() => setShowDetails(!showDetails)}
        className="mt-3 text-sm text-blue-600 hover:underline"
      >
        {showDetails ? "Minder details" : "Meer details"}
      </button>

      {showDetails && (
        <div className="mt-4 pt-4 border-t border-gray-100">
          <h4 className="text-sm font-medium text-gray-700 mb-2">Score breakdown</h4>
          <div className="space-y-2 text-sm">
            <div className="flex justify-between">
              <span className="text-gray-600">Technisch ({(pick.breakdown.technical.weight * 100).toFixed(0)}%)</span>
              <span className={pick.breakdown.technical.score >= 0 ? "text-green-600" : "text-red-600"}>
                {pick.breakdown.technical.contribution >= 0 ? "+" : ""}{(pick.breakdown.technical.contribution * 100).toFixed(1)}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">Sentiment ({(pick.breakdown.sentiment.weight * 100).toFixed(0)}%)</span>
              <span className={pick.breakdown.sentiment.score >= 0 ? "text-green-600" : "text-red-600"}>
                {pick.breakdown.sentiment.contribution >= 0 ? "+" : ""}{(pick.breakdown.sentiment.contribution * 100).toFixed(1)}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">Fundamenteel ({(pick.breakdown.fundamental.weight * 100).toFixed(0)}%)</span>
              <span className={pick.breakdown.fundamental.score >= 0 ? "text-green-600" : "text-red-600"}>
                {pick.breakdown.fundamental.contribution >= 0 ? "+" : ""}{(pick.breakdown.fundamental.contribution * 100).toFixed(1)}
              </span>
            </div>
          </div>

          {pick.news_headlines.length > 0 && (
            <div className="mt-4">
              <h4 className="text-sm font-medium text-gray-700 mb-2">Recent nieuws</h4>
              <ul className="space-y-1">
                {pick.news_headlines.map((headline, i) => (
                  <li key={i} className="text-sm text-gray-600">• {headline}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default function DashboardPage() {
  const router = useRouter();
  const [user, setUser] = useState<{ email: string; budget: number } | null>(null);
  const [digest, setDigest] = useState<Digest | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [editingBudget, setEditingBudget] = useState(false);
  const [newBudget, setNewBudget] = useState("");
  const [verificationStatus, setVerificationStatus] = useState<VerificationStatus | null>(null);

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
      setNewBudget(userResult.data!.budget.toString());

      const digestResult = await getLatestDigest();
      if (digestResult.data) {
        setDigest(digestResult.data);
      }

      const verificationResult = await getVerificationStatus();
      if (verificationResult.data) {
        setVerificationStatus(verificationResult.data);
      }

      setLoading(false);
    };

    loadData();
  }, [router]);

  const handleBudgetSave = async () => {
    const budgetNum = parseFloat(newBudget);
    if (isNaN(budgetNum) || budgetNum < 1000) {
      setError("Minimum budget is €1.000");
      return;
    }

    const result = await updateBudget(budgetNum);
    if (result.error) {
      setError(result.error);
      return;
    }

    setUser((prev) => prev ? { ...prev, budget: budgetNum } : null);
    setEditingBudget(false);
    setError("");
  };

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

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white border-b border-gray-200">
        <div className="max-w-6xl mx-auto px-4 py-4 flex justify-between items-center">
          <h1 className="text-xl font-bold text-gray-900">StockPulse AI</h1>
          <div className="flex items-center gap-4">
            <Link href="/verification" className="text-sm text-blue-600 hover:underline">
              Verificatie
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
        {error && (
          <div className="mb-6 bg-red-50 text-red-600 p-3 rounded-lg text-sm">
            {error}
          </div>
        )}

        {verificationStatus && !verificationStatus.is_unlocked && (
          <div className="mb-6 bg-yellow-50 border border-yellow-200 rounded-lg p-4">
            <div className="flex items-center gap-3">
              <span className="text-2xl">🔒</span>
              <div className="flex-1">
                <div className="font-bold text-yellow-700">Observatiemodus</div>
                <div className="text-sm text-yellow-600">
                  {verificationStatus.message}
                </div>
              </div>
              <Link
                href="/verification"
                className="text-sm bg-yellow-100 hover:bg-yellow-200 text-yellow-800 px-3 py-1.5 rounded-lg transition"
              >
                Bekijk voortgang →
              </Link>
            </div>
          </div>
        )}

        <div className="bg-white rounded-lg border border-gray-200 p-4 mb-8">
          <div className="flex justify-between items-center">
            <div>
              <span className="text-sm text-gray-600">Je budget</span>
              {editingBudget ? (
                <div className="flex items-center gap-2 mt-1">
                  <input
                    type="number"
                    value={newBudget}
                    onChange={(e) => setNewBudget(e.target.value)}
                    min={1000}
                    className="w-32 px-2 py-1 border border-gray-300 rounded"
                  />
                  <button
                    onClick={handleBudgetSave}
                    className="text-sm text-blue-600 hover:underline"
                  >
                    Opslaan
                  </button>
                  <button
                    onClick={() => setEditingBudget(false)}
                    className="text-sm text-gray-600 hover:underline"
                  >
                    Annuleren
                  </button>
                </div>
              ) : (
                <div className="flex items-center gap-2">
                  <span className="text-2xl font-bold text-gray-900">
                    €{user?.budget.toLocaleString("nl-NL")}
                  </span>
                  <button
                    onClick={() => setEditingBudget(true)}
                    className="text-sm text-blue-600 hover:underline"
                  >
                    Wijzigen
                  </button>
                </div>
              )}
            </div>
            {digest?.generated_at && (
              <div className="text-right">
                <span className="text-sm text-gray-600">Laatste update</span>
                <div className="text-sm font-medium">
                  {new Date(digest.generated_at).toLocaleString("nl-NL")}
                </div>
              </div>
            )}
          </div>
        </div>

        {digest?.message && !digest.buy.length && !digest.sell.length ? (
          <div className="bg-yellow-50 text-yellow-800 p-4 rounded-lg text-center">
            {digest.message}
          </div>
        ) : (
          <div className="grid md:grid-cols-2 gap-8">
            <div>
              <h2 className="text-lg font-bold text-green-700 mb-4 flex items-center gap-2">
                <span className="text-2xl">📈</span> Top 5 koopsignalen
              </h2>
              <div className="space-y-4">
                {digest?.buy.map((pick, i) => (
                  <StockCard key={i} pick={pick} type="buy" />
                ))}
                {!digest?.buy.length && (
                  <p className="text-gray-500 text-sm">Geen koopsignalen beschikbaar</p>
                )}
              </div>
            </div>

            <div>
              <h2 className="text-lg font-bold text-red-700 mb-4 flex items-center gap-2">
                <span className="text-2xl">📉</span> Top 5 verkoopsignalen
              </h2>
              <div className="space-y-4">
                {digest?.sell.map((pick, i) => (
                  <StockCard key={i} pick={pick} type="sell" />
                ))}
                {!digest?.sell.length && (
                  <p className="text-gray-500 text-sm">Geen verkoopsignalen beschikbaar</p>
                )}
              </div>
            </div>
          </div>
        )}

        <div className="mt-12 text-center text-sm text-gray-500">
          <p>
            ⚠️ Dit is een experimenteel systeem. Geen financieel advies.
            Doe altijd je eigen onderzoek voordat je belegt.
          </p>
        </div>
      </main>
    </div>
  );
}
