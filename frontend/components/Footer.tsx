"use client";

export function Footer() {
  return (
    <footer className="border-t border-slate-200 bg-white">
      <div className="container-page flex flex-col gap-2 py-6 text-sm text-slate-500 sm:flex-row sm:items-center sm:justify-between">
        <p>© 2025 MedServicePrice.kz — MVP. Данные из открытых источников.</p>
        <p className="text-slate-400">Агрегатор медицинских цен и врачей · Казахстан</p>
      </div>
    </footer>
  );
}
