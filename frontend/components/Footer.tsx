"use client";

export function Footer() {
  return (
    <footer className="border-t border-slate-200 bg-white">
      <div className="container-page flex flex-col gap-2 py-8 text-sm text-slate-500 sm:flex-row sm:items-center sm:justify-between">
        <p>© 2026 MedServicePrice.kz — Агрегатор медицинских цен и врачей.</p>
        <p className="text-slate-400">Данные из открытых источников.</p>
      </div>
    </footer>
  );
}
