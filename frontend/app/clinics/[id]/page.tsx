import Link from "next/link";
import { notFound } from "next/navigation";
import dynamic from "next/dynamic";
import { ArrowLeft, CalendarCheck, Clock, ExternalLink, MapPin, Phone, Star } from "lucide-react";
import { api } from "@/lib/api";
import { categoryMeta, formatDate, formatKzt } from "@/lib/format";
import type { ClinicCard } from "@/lib/types";

const ClinicMiniMap = dynamic(() => import("@/components/ClinicMiniMap").then((m) => m.ClinicMiniMap), {
  ssr: false,
  loading: () => <div className="h-56 w-full animate-pulse rounded-2xl bg-slate-100" />,
});

export const dynamicParams = true;
export const revalidate = 0;

export default async function ClinicPage({ params }: { params: { id: string } }) {
  let clinic: ClinicCard;
  try {
    clinic = await api.clinic(params.id);
  } catch {
    notFound();
  }

  const grouped: Record<string, ClinicCard["services"]> = {};
  for (const s of clinic!.services) (grouped[s.category || "other"] ||= []).push(s);

  return (
    <div className="container-page pt-6">
      <Link href="/" className="mb-4 inline-flex items-center gap-1 text-sm text-slate-500 hover:text-brand-700">
        <ArrowLeft size={16} /> Назад к поиску
      </Link>

      <div className="grid gap-6 lg:grid-cols-[1fr_320px]">
        {/* main */}
        <div>
          <div className="card p-6">
            <div className="flex flex-wrap items-center gap-2">
              <h1 className="text-2xl font-extrabold text-ink">{clinic!.name}</h1>
              {clinic!.rating != null && (
                <span className="chip bg-amber-50 text-amber-700">
                  <Star size={12} className="fill-amber-400 text-amber-400" /> {clinic!.rating.toFixed(1)}
                </span>
              )}
              {clinic!.has_online_booking && (
                <span className="chip bg-emerald-50 text-emerald-700">
                  <CalendarCheck size={12} /> Онлайн-запись
                </span>
              )}
              <span className="chip bg-slate-100 text-slate-500">источник: {clinic!.source}</span>
            </div>
            <div className="mt-3 grid gap-2 text-sm text-slate-600 sm:grid-cols-2">
              <span className="inline-flex items-center gap-2">
                <MapPin size={16} className="text-brand-500" /> {clinic!.city}
                {clinic!.address ? `, ${clinic!.address}` : ""}
              </span>
              {clinic!.working_hours && (
                <span className="inline-flex items-center gap-2">
                  <Clock size={16} className="text-brand-500" /> {clinic!.working_hours}
                </span>
              )}
              {clinic!.phone && (
                <span className="inline-flex items-center gap-2">
                  <Phone size={16} className="text-brand-500" /> {clinic!.phone}
                </span>
              )}
              {clinic!.website && (
                <a
                  href={clinic!.website}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-2 text-brand-600 hover:underline"
                >
                  <ExternalLink size={16} /> Сайт клиники
                </a>
              )}
            </div>
          </div>

          {/* services */}
          <div className="mt-6 space-y-6">
            <h2 className="text-lg font-bold text-ink">
              Услуги и цены <span className="text-slate-400">({clinic!.services_count})</span>
            </h2>
            {Object.entries(grouped).map(([cat, items]) => {
              const cm = categoryMeta(cat);
              const Icon = cm.icon;
              return (
                <div key={cat} className="card overflow-hidden">
                  <div className={`flex items-center gap-2 px-5 py-3 text-sm font-semibold ${cm.color}`}>
                    <Icon size={16} strokeWidth={1.9} /> {cm.label}
                    <span className="ml-auto font-medium opacity-70">{items.length}</span>
                  </div>
                  <ul className="divide-y divide-slate-100">
                    {items.map((s) => (
                      <li key={s.price_id} className="flex items-center justify-between gap-3 px-5 py-3">
                        <div className="min-w-0">
                          {s.service_id ? (
                            <Link
                              href={`/search?service_id=${s.service_id}&name=${encodeURIComponent(s.service_name)}`}
                              className="font-medium text-ink hover:text-brand-700"
                            >
                              {s.service_name}
                            </Link>
                          ) : (
                            <span className="font-medium text-ink">{s.service_name}</span>
                          )}
                          <div className="text-xs text-slate-400">
                            {s.duration_days != null && `срок ${s.duration_days} дн. · `}
                            обновлено {formatDate(s.parsed_at)}
                            {!s.matched && " · не привязано к справочнику"}
                          </div>
                        </div>
                        <div className="shrink-0 text-lg font-bold text-ink">{formatKzt(s.price_kzt)}</div>
                      </li>
                    ))}
                  </ul>
                </div>
              );
            })}
          </div>
        </div>

        {/* sidebar */}
        <aside className="space-y-4">
          {clinic!.lat != null && clinic!.lng != null && (
            <div className="card overflow-hidden p-2">
              <ClinicMiniMap lat={clinic!.lat} lng={clinic!.lng} name={clinic!.name} />
              <a
                href={`https://2gis.kz/search/${encodeURIComponent(clinic!.name + " " + clinic!.address)}`}
                target="_blank"
                rel="noopener noreferrer"
                className="btn-outline m-2 w-[calc(100%-1rem)]"
              >
                <MapPin size={16} /> Маршрут в 2GIS
              </a>
            </div>
          )}
          <div className="card p-5 text-sm text-slate-500">
            <p className="font-semibold text-ink">О данных</p>
            <p className="mt-1">
              Цены собраны из открытых источников и нормализованы по единому справочнику услуг.
              Перед визитом уточняйте стоимость на сайте клиники.
            </p>
          </div>
        </aside>
      </div>
    </div>
  );
}
