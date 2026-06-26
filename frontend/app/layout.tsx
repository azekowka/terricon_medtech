import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import "leaflet/dist/leaflet.css";
import { Header } from "@/components/Header";

const inter = Inter({ subsets: ["latin", "cyrillic"], display: "swap" });

export const metadata: Metadata = {
  title: "MedServicePrice.kz — сравнение цен на медуслуги в Казахстане",
  description:
    "Агрегатор цен на анализы, приёмы врачей и диагностику в клиниках Казахстана. Сравните стоимость и найдите выгодное предложение.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="ru">
      <body className={inter.className}>
        <Header />
        <main className="min-h-[calc(100vh-4rem)] pb-16">{children}</main>
        <footer className="border-t border-slate-200 bg-white">
          <div className="container-page flex flex-col gap-2 py-6 text-sm text-slate-500 sm:flex-row sm:items-center sm:justify-between">
            <p>© 2025 MedServicePrice.kz — MVP, хакатон. Данные из открытых источников.</p>
            <p className="text-slate-400">Сравнение цен на медицинские услуги · Казахстан</p>
          </div>
        </footer>
      </body>
    </html>
  );
}
