import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { Header } from "@/components/Header";
import { I18nProvider } from "@/lib/i18n/I18nProvider";
import { Footer } from "@/components/Footer";

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
        <I18nProvider>
          <Header />
          <main className="min-h-[calc(100vh-4rem)] pb-16">{children}</main>
          <Footer />
        </I18nProvider>
      </body>
    </html>
  );
}
