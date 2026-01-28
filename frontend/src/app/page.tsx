import Link from "next/link";

export default function Home() {
  return (
    <div className="min-h-screen flex flex-col items-center justify-center p-8">
      <div className="max-w-md w-full text-center">
        <h1 className="text-4xl font-bold text-gray-900 mb-4">
          StockPulse AI
        </h1>
        <p className="text-gray-600 mb-8">
          Dagelijkse AI-gestuurde buy/sell adviezen voor slimmer beleggen.
        </p>

        <div className="space-y-4">
          <Link
            href="/login"
            className="block w-full bg-blue-600 text-white py-3 px-6 rounded-lg font-medium hover:bg-blue-700 transition"
          >
            Inloggen
          </Link>
          <Link
            href="/register"
            className="block w-full bg-white text-blue-600 py-3 px-6 rounded-lg font-medium border border-blue-600 hover:bg-blue-50 transition"
          >
            Account aanmaken
          </Link>
        </div>

        <div className="mt-12 grid grid-cols-3 gap-4 text-center">
          <div>
            <div className="text-2xl font-bold text-blue-600">100+</div>
            <div className="text-sm text-gray-500">Aandelen</div>
          </div>
          <div>
            <div className="text-2xl font-bold text-green-600">Top 5</div>
            <div className="text-sm text-gray-500">Buy signalen</div>
          </div>
          <div>
            <div className="text-2xl font-bold text-red-600">Top 5</div>
            <div className="text-sm text-gray-500">Sell signalen</div>
          </div>
        </div>

        <p className="mt-8 text-xs text-gray-400">
          Experimenteel. Geen financieel advies. Gebruik op eigen risico.
        </p>
      </div>
    </div>
  );
}
