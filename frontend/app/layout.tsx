import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { Header } from "@/components/Header";
import { I18nProvider } from "@/lib/i18n/I18nProvider";
import { Footer } from "@/components/Footer";
import { ChatWidget } from "@/components/ChatWidget";

// Inter — same typeface Aviasales uses (its Stapel falls back to Inter). Exposed
// as a CSS variable so the global font stack can mirror Aviasales' exact stack.
const inter = Inter({ subsets: ["latin", "cyrillic"], display: "swap", variable: "--font-inter" });

export const metadata: Metadata = {
  title: "MedServicePrice.kz — сравнение цен на медуслуги в Казахстане",
  description:
    "Агрегатор цен на анализы, приёмы врачей и диагностику в клиниках Казахстана. Сравните стоимость и найдите выгодное предложение.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="ru" className={inter.variable}>
      <body>
        <I18nProvider>
          <Header />
          <main className="min-h-[calc(100vh-4rem)] pb-16">{children}</main>
          <Footer />
          <ChatWidget />
        </I18nProvider>
      </body>
    </html>
  );
}
