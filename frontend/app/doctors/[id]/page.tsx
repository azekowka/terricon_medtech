"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import {
  ArrowLeft, BadgeCheck, CalendarCheck, Check, Clock, MapPin, Star, Stethoscope, ThumbsUp,
} from "lucide-react";
import { api } from "@/lib/api";
import type { DoctorDetail } from "@/lib/types";
import { formatKzt, yearsLabel } from "@/lib/format";
import { useI18n } from "@/lib/i18n/I18nProvider";

const DAYS = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"];

function sanitize(html: string): string {
  return html.replace(/<script[\s\S]*?<\/script>/gi, "").replace(/ on\w+="[^"]*"/gi, "");
}

function ratingNum(r: number | string | null): number | null {
  if (r === null || r === undefined) return null;
  const n = typeof r === "string" ? parseFloat(r) : r;
  return isNaN(n) ? null : n;
}

export default function DoctorProfilePage({ params }: { params: { id: string } }) {
  const { t, locale } = useI18n();
  const { id } = params;
  const [d, setD] = useState<DoctorDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [booked, setBooked] = useState(false);

  useEffect(() => {
    setLoading(true);
    api.doctorProfile(Number(id)).then(setD).catch(() => setD(null)).finally(() => setLoading(false));
  }, [id]);

  if (loading) {
    return (
      <div className="container-page flex flex-col items-center gap-3 py-32 text-slate-400">
        <Stethoscope className="animate-pulse" size={36} />
        <p>{t("profile.loading")}</p>
      </div>
    );
  }
  if (!d) {
    return (
      <div className="container-page py-28 text-center">
        <p className="text-xl font-bold text-ink">{t("profile.notFound")}</p>
        <Link href="/doctors" className="btn-primary mt-6">{t("profile.toList")}</Link>
      </div>
    );
  }

  const specs = d.specialties?.map((s) => s.name) || [];
  const reviews = d.reviews_list || [];

  return (
    <div className="container-page pt-6">
      <Link href="/doctors" className="mb-4 inline-flex items-center gap-1 text-sm text-slate-500 hover:text-brand-700">
        <ArrowLeft size={16} /> {t("profile.toList")}
      </Link>

      <div className="grid gap-6 lg:grid-cols-[1fr_340px]">
        {/* main column */}
        <div className="space-y-6">
          {/* header */}
          <div className="card p-6">
            <div className="flex flex-col gap-4 sm:flex-row">
              <div className="relative shrink-0">
                <div className="h-32 w-32 overflow-hidden rounded-2xl bg-slate-100">
                  {d.avatar ? (
                    // eslint-disable-next-line @next/next/no-img-element
                    <img src={d.avatar} alt={d.name} className="h-full w-full object-cover" />
                  ) : (
                    <div className="flex h-full w-full items-center justify-center text-slate-300"><Stethoscope size={44} /></div>
                  )}
                </div>
                {d.verified && (
                  <span className="absolute -bottom-1 -right-1 flex h-8 w-8 items-center justify-center rounded-full bg-white text-brand-600 shadow">
                    <BadgeCheck size={26} className="fill-brand-100" />
                  </span>
                )}
              </div>
              <div className="min-w-0 flex-1">
                <div className="flex flex-wrap items-center gap-2">
                  {d.top && <span className="chip bg-amber-100 text-amber-700">ТОП</span>}
                  {d.verified && <span className="chip bg-brand-50 text-brand-700"><BadgeCheck size={12} /> {t("profile.verified")}</span>}
                  <h1 className="text-2xl font-extrabold text-ink">{d.name}</h1>
                </div>
                <p className="mt-1 font-semibold text-brand-700">{specs.join(" · ") || "Врач"}</p>
                <div className="mt-2 flex flex-wrap items-center gap-x-4 gap-y-1 text-sm text-slate-500">
                  {d.experience_years != null && (
                    <span>{t("doc.experience")} {d.experience_years} {yearsLabel(d.experience_years, locale)}</span>
                  )}
                  {d.category && <span>• {d.category}</span>}
                  <span className="chip bg-emerald-50 text-emerald-700">
                    {d.accepts_children ? t("doc.acceptsKids") : t("doc.acceptsAdults")}
                  </span>
                </div>
                <div className="mt-2 flex flex-wrap items-center gap-3 text-sm">
                  {ratingNum(d.rating) != null && (
                    <span className="inline-flex items-center gap-1 font-semibold text-amber-600">
                      <Star size={15} className="fill-amber-400 text-amber-400" /> {ratingNum(d.rating)!.toFixed(2)}
                    </span>
                  )}
                  {reviews.length > 0 && (
                    <span className="text-slate-500">{reviews.length} {t("doc.reviews")}</span>
                  )}
                  {d.online_bookings > 0 && (
                    <span className="text-slate-400">· {d.online_bookings} {t("doc.online").toLowerCase()}</span>
                  )}
                </div>
              </div>
            </div>
          </div>

          {/* about */}
          {d.description && (
            <Section title={t("profile.about")}>
              <div
                className="prose prose-sm max-w-none text-slate-700 [&_p]:my-1.5 [&_strong]:text-ink [&_ul]:list-disc [&_ul]:pl-5"
                dangerouslySetInnerHTML={{ __html: sanitize(d.description) }}
              />
            </Section>
          )}

          {/* diseases */}
          {d.diseases?.length > 0 && (
            <Section title={t("profile.diseases")}>
              <div className="flex flex-wrap gap-1.5">
                {d.diseases.map((x) => <span key={x} className="chip bg-slate-100 text-slate-600">{x}</span>)}
              </div>
            </Section>
          )}

          {/* services */}
          {d.services?.length > 0 && (
            <Section title={`${t("profile.services")} (${d.services.length})`}>
              <ul className="divide-y divide-slate-100">
                {d.services.slice(0, 40).map((s, i) => (
                  <li key={i} className="flex items-center justify-between gap-3 py-2.5 text-sm">
                    <span className="text-ink">{s.name || s.title}</span>
                    <span className="shrink-0 font-semibold text-ink">
                      {s.priceWithDiscount || s.price ? formatKzt(s.priceWithDiscount || s.price) : "—"}
                    </span>
                  </li>
                ))}
              </ul>
            </Section>
          )}

          {/* clinics */}
          <Section title={`${t("profile.whereReceives")} (${d.clinics?.length || 0})`}>
            <div className="space-y-3">
              {(d.clinics || []).map((c, i) => (
                <div key={i} className="rounded-xl border border-slate-100 p-3">
                  <div className="flex items-start justify-between gap-3">
                    <div>
                      <div className="font-semibold text-ink">{c.name}</div>
                      {c.address && (
                        <div className="flex items-center gap-1 text-sm text-slate-500"><MapPin size={13} /> {c.address}</div>
                      )}
                    </div>
                    <div className="shrink-0 text-right">
                      {c.discount ? (
                        <>
                          <div className="text-xs text-slate-400 line-through">{formatKzt(c.price)}</div>
                          <div className="font-bold text-ink">{formatKzt(c.price_discount)}</div>
                        </>
                      ) : (
                        <div className="font-bold text-ink">{c.price ? formatKzt(c.price) : "—"}</div>
                      )}
                    </div>
                  </div>
                  <div className="mt-1.5 flex flex-wrap items-center gap-2">
                    {c.online_booking && <span className="chip bg-emerald-50 text-emerald-700"><CalendarCheck size={12} /> Онлайн-запись</span>}
                    {c.lat && c.lng && (
                      <a href={`https://2gis.kz/geo/${c.lng},${c.lat}`} target="_blank" rel="noopener noreferrer" className="chip bg-slate-100 text-slate-600">
                        <MapPin size={12} /> {t("profile.onMap")}
                      </a>
                    )}
                  </div>
                  {c.schedule && c.schedule.some((s) => s.work) && (
                    <div className="mt-2 flex items-start gap-1.5 text-xs text-slate-500">
                      <Clock size={13} className="mt-0.5 shrink-0 text-slate-400" />
                      <div className="flex flex-wrap gap-1.5">
                        {c.schedule.map((s, j) => (
                          <span key={j} className={`rounded px-1.5 py-0.5 ${s.work ? "bg-emerald-50 text-emerald-700" : "bg-slate-50 text-slate-300"}`}>
                            {DAYS[j] || s.day}{s.work ? ` ${s.h24 ? "24ч" : `${s.start}–${s.end}`}` : " —"}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              ))}
            </div>
          </Section>

          {/* reviews */}
          {reviews.length > 0 && (
            <Section title={`${t("profile.reviews")} (${reviews.length})`}>
              <div className="space-y-3">
                {reviews.map((r, i) => {
                  const rn = ratingNum(r.rating);
                  return (
                    <div key={i} className="rounded-xl border border-slate-100 p-4">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          <span className="flex h-9 w-9 items-center justify-center rounded-full bg-brand-50 font-bold text-brand-700">
                            {(r.author || "?").charAt(0)}
                          </span>
                          <div>
                            <div className="text-sm font-semibold text-ink">{r.author}</div>
                            {r.visit_date && <div className="text-xs text-slate-400">{t("profile.visit")}: {r.visit_date}</div>}
                          </div>
                        </div>
                        {rn != null && (
                          <span className="inline-flex items-center gap-0.5">
                            {Array.from({ length: 5 }).map((_, k) => (
                              <Star key={k} size={14} className={k < Math.round(rn) ? "fill-amber-400 text-amber-400" : "text-slate-200"} />
                            ))}
                          </span>
                        )}
                      </div>
                      {r.text && <p className="mt-2 text-sm text-slate-700">{r.text}</p>}
                      {r.tags?.length > 0 && (
                        <div className="mt-2 flex flex-wrap gap-1">
                          {r.tags.slice(0, 8).map((t) => (
                            <span key={t} className="chip bg-emerald-50 text-emerald-700"><ThumbsUp size={10} /> {t}</span>
                          ))}
                        </div>
                      )}
                      {r.reply && (
                        <div className="mt-2 rounded-lg bg-slate-50 p-2.5 text-sm text-slate-600">
                          <span className="font-semibold text-slate-700">{t("profile.clinicReply")}:</span> {r.reply}
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            </Section>
          )}
        </div>

        {/* sticky booking sidebar */}
        <aside>
          <div className="card sticky top-20 p-5">
            <div className="text-sm text-slate-500">{t("profile.price")}</div>
            <div className="mt-1 text-3xl font-extrabold text-ink">
              {d.clinic?.price_discount || d.clinic?.price || d.min_price
                ? formatKzt(d.clinic?.price_discount || d.clinic?.price || d.min_price)
                : t("profile.byRequest")}
            </div>
            {d.clinic?.discount ? (
              <span className="chip mt-1 bg-teal-100 text-teal-700">-{d.clinic.discount}% от MedService</span>
            ) : null}
            {booked ? (
              <div className="mt-4 flex items-center gap-2 rounded-xl bg-emerald-50 p-3 font-semibold text-emerald-700">
                <Check size={18} /> {t("profile.sent")}
              </div>
            ) : (
              <button onClick={() => setBooked(true)} className="btn-primary mt-4 w-full">
                {t("common.bookAppt")}
              </button>
            )}
            <p className="mt-3 text-center text-xs text-slate-400">
              {d.online_bookings > 0 ? t("profile.bookedCount", { n: d.online_bookings }) : t("profile.freeBooking")}
            </p>
          </div>
        </aside>
      </div>
    </div>
  );
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="card p-6">
      <h2 className="mb-3 text-lg font-bold text-ink">{title}</h2>
      {children}
    </div>
  );
}
