import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "StockPulse - Drawdown Strategy",
  description: "QQQ Drawdown-Based Accumulation Strategy",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="nl">
      <body className={`${inter.className} antialiased bg-gray-900 text-white`}>
        {children}
      </body>
    </html>
  );
}
