"use client";

import { useState } from "react";
import { SlidersHorizontal } from "lucide-react";
import type { DoctorSpecialty } from "@/lib/types";
import { useI18n } from "@/lib/i18n/I18nProvider";

export interface DocFilterState {
  specialty: string;
  price_max: string;
  rating_min: string;
  experience_min: string;
  accepts_children: boolean;
  online_booking: boolean;
  verified: boolean;
  sort: string;
}

const SORT_KEYS = [
  { key: "rating", tk: "doctors.sort.rating" },
  { key: "price_asc", tk: "doctors.sort.priceAsc" },
  { key: "price_desc", tk: "doctors.sort.priceDesc" },
  { key: "experience", tk: "doctors.sort.experience" },
  { key: "reviews", tk: "doctors.sort.reviews" },
];

export function DoctorFilters({
  specialties,
  state,
  onChange,
}: {
  specialties: DoctorSpecialty[];
  state: DocFilterState;
  onChange: (patch: Partial<DocFilterState>) => void;
}) {
  const { t } = useI18n();
  const [specQuery, setSpecQuery] = useState("");
  const visibleSpecs = specialties
    .filter((s) => s.name.toLowerCase().includes(specQuery.trim().toLowerCase()))
    .slice(0, specQuery ? 40 : 30);

  return (
    <div className="card sticky top-20 max-h-[calc(100vh-6rem)] space-y-4 overflow-y-auto p-5">
      <div className="flex items-center gap-2 font-bold text-ink">
        <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-slate-100 text-slate-600">
          <SlidersHorizontal size={16} strokeWidth={1.75} />
        </span>
        {t("search.filters")}
      </div>

      <div>
        <label className="label">{t("search.sort")}</label>
        <select className="input" value={state.sort} onChange={(e) => onChange({ sort: e.target.value })}>
          {SORT_KEYS.map((s) => (
            <option key={s.key} value={s.key}>{t(s.tk)}</option>
          ))}
        </select>
      </div>

      <div>
        <label className="label">{t("doctors.specialty")}</label>
        <input
          className="input mb-2"
          placeholder={t("doctors.searchSpecialty")}
          value={specQuery}
          onChange={(e) => setSpecQuery(e.target.value)}
        />
        <div className="max-h-64 space-y-0.5 overflow-y-auto pr-1">
          <button
            onClick={() => onChange({ specialty: "" })}
            className={`block w-full rounded-lg px-2.5 py-1.5 text-left text-sm ${
              !state.specialty ? "bg-brand-50 font-semibold text-brand-700" : "text-slate-600 hover:bg-slate-100"
            }`}
          >
            {t("doctors.allSpecialties")}
          </button>
          {visibleSpecs.map((s) => (
            <button
              key={s.alias}
              onClick={() => onChange({ specialty: s.alias })}
              className={`flex w-full items-center justify-between rounded-lg px-2.5 py-1.5 text-left text-sm ${
                state.specialty === s.alias ? "bg-brand-50 font-semibold text-brand-700" : "text-slate-600 hover:bg-slate-100"
              }`}
            >
              <span className="truncate">{s.name}</span>
              <span className="ml-2 shrink-0 text-xs text-slate-400">{s.count}</span>
            </button>
          ))}
        </div>
      </div>

      <div>
        <label className="label">{t("doctors.priceUpTo")}</label>
        <input
          type="number"
          className="input"
          placeholder="10000"
          value={state.price_max}
          onChange={(e) => onChange({ price_max: e.target.value })}
        />
      </div>

      <div>
        <label className="label">{t("search.minRating")}</label>
        <select className="input" value={state.rating_min} onChange={(e) => onChange({ rating_min: e.target.value })}>
          <option value="">{t("search.anyRating")}</option>
          <option value="4">{t("common.from")} 4.0 ★</option>
          <option value="4.5">{t("common.from")} 4.5 ★</option>
          <option value="4.8">{t("common.from")} 4.8 ★</option>
        </select>
      </div>

      <div>
        <label className="label">{t("doctors.expFrom")}</label>
        <select className="input" value={state.experience_min} onChange={(e) => onChange({ experience_min: e.target.value })}>
          <option value="">{t("search.anyRating")}</option>
          <option value="5">{t("common.from")} 5</option>
          <option value="10">{t("common.from")} 10</option>
          <option value="20">{t("common.from")} 20</option>
        </select>
      </div>

      <Toggle label={t("doctors.acceptsChildren")} checked={state.accepts_children} onChange={(v) => onChange({ accepts_children: v })} />
      <Toggle label={t("search.online")} checked={state.online_booking} onChange={(v) => onChange({ online_booking: v })} />
      <Toggle label={t("doctors.verifiedOnly")} checked={state.verified} onChange={(v) => onChange({ verified: v })} />
    </div>
  );
}

function Toggle({ label, checked, onChange }: { label: string; checked: boolean; onChange: (v: boolean) => void }) {
  return (
    <label className="flex cursor-pointer items-center justify-between rounded-xl bg-slate-50 px-3 py-2.5 text-sm font-medium text-slate-700 transition hover:bg-slate-100">
      {label}
      <input type="checkbox" checked={checked} onChange={(e) => onChange(e.target.checked)} className="h-4 w-4 rounded accent-brand-600" />
    </label>
  );
}
