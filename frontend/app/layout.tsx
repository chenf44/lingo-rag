import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "LingoRAG",
  description: "Find natural English and Thai expressions, backed by real example sentences.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="zh">
      <body>{children}</body>
    </html>
  );
}
