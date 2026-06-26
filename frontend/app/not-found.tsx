import Link from "next/link";

export default function NotFound() {
  return (
    <div className="container-page flex flex-col items-center justify-center py-28 text-center">
      <p className="text-6xl font-extrabold text-brand-600">404</p>
      <h1 className="mt-3 text-xl font-bold text-ink">Страница не найдена</h1>
      <p className="mt-1 text-slate-500">Возможно, услуга или клиника были удалены.</p>
      <Link href="/" className="btn-primary mt-6">
        На главную
      </Link>
    </div>
  );
}
