export function formatKzt(value: number | null | undefined): string {
  if (value === null || value === undefined) return "—";
  return new Intl.NumberFormat("ru-RU", { maximumFractionDigits: 0 }).format(value) + " ₸";
}

export function formatDate(iso: string | null | undefined): string {
  if (!iso) return "—";
  const d = new Date(iso);
  return d.toLocaleDateString("ru-RU", { day: "2-digit", month: "short", year: "numeric" });
}

export function yearsLabel(n: number, locale: string): string {
  if (locale === "kk") return "жыл";
  if (locale === "en") return n === 1 ? "year" : "years";
  return pluralRu(n, ["год", "года", "лет"]);
}

export function reviewsLabel(n: number, locale: string): string {
  if (locale === "kk") return "пікір";
  if (locale === "en") return n === 1 ? "review" : "reviews";
  return pluralRu(n, ["отзыв", "отзыва", "отзывов"]);
}

export function pluralRu(n: number, forms: [string, string, string]): string {
  const mod10 = n % 10;
  const mod100 = n % 100;
  if (mod10 === 1 && mod100 !== 11) return forms[0];
  if (mod10 >= 2 && mod10 <= 4 && (mod100 < 10 || mod100 >= 20)) return forms[1];
  return forms[2];
}

export function relativeDays(iso: string | null | undefined): string {
  if (!iso) return "—";
  const diff = Date.now() - new Date(iso).getTime();
  const days = Math.floor(diff / 86400000);
  if (days <= 0) return "сегодня";
  if (days === 1) return "вчера";
  return `${days} ${pluralRu(days, ["день", "дня", "дней"])} назад`;
}

export const CATEGORY_META: Record<string, { label: string; color: string; emoji: string }> = {
  laboratory: { label: "Лаборатория", color: "bg-violet-100 text-violet-700", emoji: "🧪" },
  doctor: { label: "Приём врача", color: "bg-emerald-100 text-emerald-700", emoji: "👨‍⚕️" },
  diagnostic: { label: "Диагностика", color: "bg-amber-100 text-amber-700", emoji: "🩻" },
  procedure: { label: "Процедура", color: "bg-sky-100 text-sky-700", emoji: "💉" },
};

export function categoryMeta(key: string) {
  return CATEGORY_META[key] || { label: key || "Прочее", color: "bg-slate-100 text-slate-600", emoji: "📋" };
}
