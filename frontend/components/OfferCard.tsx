"use client";

import Link from "next/link";
import { ArrowRight, Bell, Clock, ExternalLink, MapPin, Star, Navigation, CalendarCheck } from "lucide-react";
import type { Offer } from "@/lib/types";
import { formatKzt, relativeDays } from "@/lib/format";

export function OfferCard({
  offer,
  isCheapest,
  subscribable = true,
  selected,
  onToggleCompare,
  onSubscribe,
}: {
  offer: Offer;
  isCheapest: boolean;
  subscribable?: boolean;
  selected: boolean;
  onToggleCompare: () => void;
  onSubscribe: () => void;
}) {
  const cheapest = isCheapest;
  // A real external clinic site, if we have one; otherwise we keep the user on
  // our own clinic page (idoctor-derived clinics have no public website).
  const extSite = [offer.source_url, offer.website].find(
    (u) => u && /^https?:\/\//i.test(u) && !/idoctor\.kz/i.test(u),
  );
  return (
    <div
      className={`card relative flex flex-col gap-4 p-5 transition duration-200 hover:-translate-y-0.5 hover:shadow-hover sm:flex-row sm:items-center sm:justify-between ${
        cheapest ? "ring-2 ring-teal-400/70" : ""
      }`}
    >
      <div className="min-w-0 flex-1">
        <div className="flex min-w-0 items-center gap-2">
          {cheapest && (
            <span className="chip shrink-0 bg-teal-500 font-semibold text-white">Лучшая цена</span>
          )}
          {/* min-w-0 lets `truncate` actually clip long clinic names instead of
              forcing the flex/grid track wider than the viewport */}
          <Link
            href={`/clinics/${offer.clinic_id}`}
            className="min-w-0 truncate text-lg font-bold text-ink hover:text-brand-700"
          >
            {offer.clinic_name}
          </Link>
          {offer.rating != null && (
            <span className="chip shrink-0 bg-amber-50 text-amber-700">
              <Star size={12} className="fill-amber-400 text-amber-400" /> {offer.rating.toFixed(1)}
            </span>
          )}
          {offer.has_online_booking && (
            <span className="chip shrink-0 bg-emerald-50 text-emerald-700">
              <CalendarCheck size={12} /> Онлайн-запись
            </span>
          )}
        </div>

        <div className="mt-2 flex flex-wrap gap-x-4 gap-y-1 text-sm text-slate-500">
          <span className="inline-flex items-center gap-1">
            <MapPin size={14} /> {offer.city}
            {offer.address ? `, ${offer.address}` : ""}
          </span>
          {offer.working_hours && (
            <span className="inline-flex items-center gap-1">
              <Clock size={14} /> {offer.working_hours}
            </span>
          )}
          {offer.distance_km != null && (
            <span className="inline-flex items-center gap-1 text-brand-600">
              <Navigation size={14} /> {offer.distance_km} км
            </span>
          )}
        </div>

        <div className="mt-2.5 flex flex-wrap items-center gap-1.5 text-xs">
          <span className="rounded-md bg-slate-100 px-2 py-0.5 font-medium text-slate-500">
            {offer.source}
          </span>
          <span
            className={`inline-flex items-center gap-1 rounded-md px-2 py-0.5 font-medium ${
              offer.is_stale ? "bg-red-50 text-red-600" : "bg-emerald-50 text-emerald-700"
            }`}
            title={`Спарсено: ${offer.parsed_at}`}
          >
            <span className={`h-1.5 w-1.5 rounded-full ${offer.is_stale ? "bg-red-500" : "bg-emerald-500"}`} />
            {offer.is_stale ? "устарело" : "обновлено"} {relativeDays(offer.parsed_at)}
          </span>
          {offer.duration_days != null && (
            <span className="rounded-md bg-slate-100 px-2 py-0.5 font-medium text-slate-500">
              срок: {offer.duration_days} дн.
            </span>
          )}
          <span className="min-w-0 max-w-full truncate text-slate-400" title={offer.service_name_raw}>
            «{offer.service_name_raw}»
          </span>
        </div>
      </div>

      <div className="flex flex-wrap items-center gap-3 sm:shrink-0 sm:flex-col sm:flex-nowrap sm:items-end sm:gap-4">
        <div className="text-right">
          <div className="text-2xl font-bold tracking-tight text-ink">{formatKzt(offer.price_kzt)}</div>
        </div>
        <div className="flex items-center gap-2">
          {subscribable && (
            <button
              onClick={onSubscribe}
              title="Подписаться на изменение цены"
              className="btn-outline px-2.5 py-2"
            >
              <Bell size={16} />
            </button>
          )}
          {extSite ? (
            <a href={extSite} target="_blank" rel="noopener noreferrer" className="btn-primary">
              На сайт <ExternalLink size={14} />
            </a>
          ) : (
            <Link href={`/clinics/${offer.clinic_id}`} className="btn-primary">
              Подробнее <ArrowRight size={14} />
            </Link>
          )}
        </div>
        <label className="flex cursor-pointer items-center gap-1.5 text-xs font-medium text-slate-500">
          <input type="checkbox" checked={selected} onChange={onToggleCompare} className="h-4 w-4 rounded" />
          В сравнение
        </label>
      </div>
    </div>
  );
}
