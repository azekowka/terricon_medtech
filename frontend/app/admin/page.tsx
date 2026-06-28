"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import {
  Boxes, Brain, Database, Globe, Hammer, Layers, Loader2, Play, RefreshCw,
  Sparkles, Tags,
} from "lucide-react";
import { api } from "@/lib/api";

type Source = { key: string; label: string; kind: string };
type Job = {
  id: string; kind: string; sources: string[]; status: string; phase: string;
  messages: string[]; result: any; error: string | null;
  started_at: string; finished_at: string | null;
};

const CAT_LABEL: Record<string, string> = {
  laboratory: "Лаборатория", doctor: "Приём врача",
  diagnostic: "Диагностика", procedure: "Процедура",
};

export default function AdminPage() {
  const [stats, setStats] = useState<any>(null);
  const [logs, setLogs] = useState<any[]>([]);
  const [unmatched, setUnmatched] = useState<any[]>([]);
  const [services, setServices] = useState<any[]>([]);
  const [sources, setSources] = useState<Source[]>([]);
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const [job, setJob] = useState<Job | null>(null);
  const [aiMsg, setAiMsg] = useState<string>("");
  const [busy, setBusy] = useState(false);
  const poll = useRef<ReturnType<typeof setInterval> | null>(null);

  const refresh = useCallback(async () => {
    const [s, l, u, sv] = await Promise.all([
      api.stats(), api.parseLogs(), api.unmatched(),
      api.services({ sort: "popular", limit: 2000 }),
    ]);
    setStats(s); setLogs(l); setUnmatched(u); setServices(sv);
  }, []);

  useEffect(() => {
    api.adminSources().then((src) => {
      setSources(src);
      // default: all local (reliable) sources pre-selected
      setSelected(new Set(src.filter((x) => x.kind === "local").map((x) => x.key)));
    });
    refresh().catch(() => {});
    api.parseJob().then((j) => {
      if (j?.job) setJob(j.job);
      if (j?.running) startPolling();
    }).catch(() => {});
    return () => { if (poll.current) clearInterval(poll.current); };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  function startPolling() {
    if (poll.current) clearInterval(poll.current);
    poll.current = setInterval(async () => {
      try {
        const j = await api.parseJob();
        setJob(j.job);
        if (!j.running) {
          if (poll.current) clearInterval(poll.current);
          poll.current = null;
          setBusy(false);
          await refresh();
        }
      } catch {}
    }, 1000);
  }

  async function runParse(includeLive: boolean) {
    setBusy(true); setAiMsg("");
    const body = { sources: Array.from(selected), include_live: includeLive };
    const res = await api.triggerParse(body);
    setJob(res.job);
    startPolling();
  }

  async function rebuildDict() {
    setBusy(true); setAiMsg("");
    const res = await api.rebuildDict();
    setJob(res.job);
    startPolling();
  }

  async function aiAssist() {
    setBusy(true); setAiMsg("AI размечает очередь…");
    try {
      const res = await api.aiAssist();
      setAiMsg(res.message || "Готово");
      await refresh();
    } finally { setBusy(false); }
  }

  async function resolve(id: string, serviceId: string) {
    if (!serviceId) return;
    await api.resolveUnmatched(id, { service_id: serviceId, add_synonym: true });
    await refresh();
  }

  function toggle(key: string) {
    setSelected((prev) => {
      const n = new Set(prev);
      n.has(key) ? n.delete(key) : n.add(key);
      return n;
    });
  }

  const running = job?.status === "running";
  const local = sources.filter((s) => s.kind === "local");
  const live = sources.filter((s) => s.kind === "live");
  const dictPreview = services.filter((s) => (s.synonyms?.length || 0) > 0).slice(0, 12);

  return (
    <div className="container-page pt-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-extrabold text-ink">Панель администратора</h1>
          <p className="text-sm text-slate-500">
            Сбор реальных данных · справочник строится из собранных названий · нормализация
          </p>
        </div>
        <button onClick={() => refresh()} className="btn-outline"><RefreshCw size={16} /> Обновить</button>
      </div>

      {/* Stats */}
      <div className="mt-5 grid grid-cols-2 gap-3 sm:grid-cols-4 lg:grid-cols-8">
        <StatCard label="Клиники" value={stats?.clinics} />
        <StatCard label="Города" value={stats?.cities} />
        <StatCard label="Услуги (справочник)" value={stats?.services} accent="brand" />
        <StatCard label="Источники" value={stats?.sources} />
        <StatCard label="Активные цены" value={stats?.active_prices} />
        <StatCard label="Привязано" value={stats?.matched_prices} accent="emerald" />
        <StatCard label="В очереди" value={stats?.unmatched_pending} accent="amber" />
        <StatCard label="Raw-слой" value={stats?.raw_rows} />
      </div>

      {/* Parse controls */}
      <div className="card mt-6 p-5">
        <div className="mb-3 flex items-center gap-2 font-bold text-ink">
          <Database size={18} className="text-brand-600" /> Источники данных
          <span className="text-xs font-normal text-slate-400">
            (справочник пересобирается из собранных названий автоматически)
          </span>
        </div>

        <div className="grid gap-4 sm:grid-cols-2">
          <SourceGroup title="Локальные (надёжные)" icon={<Boxes size={14} />}
            items={local} selected={selected} onToggle={toggle} disabled={running} />
          <SourceGroup title="Живой веб (best-effort)" icon={<Globe size={14} />}
            items={live} selected={selected} onToggle={toggle} disabled={running} />
        </div>

        <div className="mt-4 flex flex-wrap items-center gap-2">
          <button onClick={() => runParse(false)} disabled={busy || running || selected.size === 0}
            className="btn-primary">
            {running ? <Loader2 className="animate-spin" size={16} /> : <Play size={16} />}
            Запустить парсинг ({selected.size})
          </button>
          <button onClick={() => runParse(true)} disabled={busy || running} className="btn-outline">
            <Globe size={16} /> + весь живой веб
          </button>
          <button onClick={rebuildDict} disabled={busy || running} className="btn-outline">
            <Hammer size={16} /> Перестроить справочник
          </button>
          <button onClick={aiAssist} disabled={busy || running} className="btn-outline">
            <Brain size={16} /> AI-разметка очереди
          </button>
          {aiMsg && <span className="text-sm text-slate-500">{aiMsg}</span>}
        </div>

        {/* Live progress */}
        {job && <ProgressPanel job={job} />}
      </div>

      {/* Dictionary preview (built from data) */}
      <div className="card mt-6 p-5">
        <div className="mb-1 flex items-center gap-2 font-bold text-ink">
          <Layers size={18} className="text-brand-600" /> Справочник — построен из собранных данных
        </div>
        <p className="mb-4 text-xs text-slate-400">
          Каждая позиция — кластер сырых названий из разных источников (синонимы), сведённый к одной услуге.
        </p>
        <div className="grid gap-3 md:grid-cols-2">
          {dictPreview.map((s) => (
            <div key={s.id} className="rounded-xl border border-slate-100 p-3">
              <div className="flex items-center justify-between gap-2">
                <span className="font-semibold text-ink">{s.name}</span>
                <span className="chip bg-brand-50 text-brand-700">{CAT_LABEL[s.category] || s.category}</span>
              </div>
              <div className="mt-1 text-xs text-slate-400">
                {s.raw_count ?? 0} упоминаний · {s.source_count ?? 0} источн. · {s.offers_count} клиник
              </div>
              {s.synonyms?.length > 0 && (
                <div className="mt-2 flex flex-wrap gap-1">
                  {s.synonyms.slice(0, 4).map((syn: string, i: number) => (
                    <span key={i} className="rounded-md bg-slate-50 px-1.5 py-0.5 text-[11px] text-slate-500">
                      {syn.length > 42 ? syn.slice(0, 42) + "…" : syn}
                    </span>
                  ))}
                  {s.synonyms.length > 4 && (
                    <span className="text-[11px] text-slate-400">+{s.synonyms.length - 4}</span>
                  )}
                </div>
              )}
            </div>
          ))}
        </div>
      </div>

      <div className="mt-6 grid gap-6 lg:grid-cols-2">
        {/* Unmatched queue */}
        <div className="card p-5">
          <div className="mb-3 flex items-center gap-2 font-bold text-ink">
            <Tags size={18} className="text-amber-500" /> Очередь ручной разметки
            <span className="chip bg-amber-100 text-amber-700">{unmatched.length}</span>
          </div>
          {unmatched.length === 0 ? (
            <p className="py-6 text-center text-sm text-slate-400">
              Очередь пуста 🎉 — нормализация привязала все названия
            </p>
          ) : (
            <ul className="max-h-[420px] space-y-3 overflow-y-auto">
              {unmatched.map((u) => (
                <li key={u.id} className="rounded-xl border border-slate-100 p-3">
                  <div className="font-medium text-ink">{u.service_name_raw}</div>
                  <div className="text-xs text-slate-400">
                    {u.source} · {u.occurrences}×
                    {u.suggested_service_name && ` · похоже на «${u.suggested_service_name}» (${Math.round(u.suggested_score)}%)`}
                  </div>
                  <div className="mt-2 flex items-center gap-2">
                    <select className="input py-1.5 text-sm" defaultValue={u.suggested_service_id || ""} id={`sel-${u.id}`}>
                      <option value="">— выбрать услугу —</option>
                      {services.map((s) => (
                        <option key={s.id} value={s.id}>{s.name}</option>
                      ))}
                    </select>
                    <button onClick={() => resolve(u.id, (document.getElementById(`sel-${u.id}`) as HTMLSelectElement).value)}
                      className="btn-primary py-1.5">Привязать</button>
                  </div>
                </li>
              ))}
            </ul>
          )}
        </div>

        {/* Parse logs */}
        <div className="card p-5">
          <div className="mb-3 font-bold text-ink">Журнал парсинга</div>
          <div className="max-h-[420px] space-y-2 overflow-y-auto">
            {logs.map((l) => (
              <div key={l.id} className="flex items-center justify-between rounded-lg bg-slate-50 px-3 py-2 text-sm">
                <span className="font-medium text-ink">
                  {l.source}{" "}
                  <span className={`chip ${l.status === "success" ? "bg-emerald-100 text-emerald-700"
                    : l.status === "error" ? "bg-red-100 text-red-700" : "bg-amber-100 text-amber-700"}`}>
                    {l.status}
                  </span>
                </span>
                <span className="text-xs text-slate-500">
                  {l.records_found} зап. · {l.errors_count} ош. · {new Date(l.started_at).toLocaleTimeString("ru-RU")}
                </span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Distribution */}
      {stats && (
        <div className="mt-6 grid gap-6 sm:grid-cols-2">
          <DistCard title="Цены по источникам" data={stats.prices_by_source} />
          <DistCard title="Цены по категориям" data={stats.prices_by_category} labels={CAT_LABEL} />
        </div>
      )}
    </div>
  );
}

function SourceGroup({ title, icon, items, selected, onToggle, disabled }: {
  title: string; icon: React.ReactNode; items: Source[];
  selected: Set<string>; onToggle: (k: string) => void; disabled: boolean;
}) {
  return (
    <div className="rounded-xl border border-slate-100 p-3">
      <div className="mb-2 flex items-center gap-1.5 text-xs font-semibold uppercase text-slate-400">{icon} {title}</div>
      <div className="space-y-1.5">
        {items.map((s) => (
          <label key={s.key} className="flex cursor-pointer items-center gap-2 text-sm">
            <input type="checkbox" checked={selected.has(s.key)} onChange={() => onToggle(s.key)} disabled={disabled}
              className="h-4 w-4 rounded border-slate-300 text-brand-600" />
            <span className="text-ink">{s.label}</span>
          </label>
        ))}
      </div>
    </div>
  );
}

function ProgressPanel({ job }: { job: Job }) {
  const running = job.status === "running";
  const r = job.result;
  return (
    <div className="mt-4 rounded-xl bg-slate-50 p-4">
      <div className="flex items-center gap-2 text-sm font-semibold text-ink">
        {running ? <Loader2 className="animate-spin text-brand-600" size={16} />
          : job.status === "error" ? <span className="text-red-600">✕</span>
          : <Sparkles className="text-emerald-600" size={16} />}
        {job.phase || (running ? "Запуск…" : job.status === "error" ? "Ошибка" : "Завершено")}
      </div>
      {/* live message ticker */}
      <div className="mt-2 max-h-28 overflow-y-auto rounded-lg bg-white p-2 font-mono text-[11px] leading-relaxed text-slate-500">
        {(job.messages || []).slice(-8).map((m, i) => <div key={i}>{m}</div>)}
      </div>
      {job.error && <div className="mt-2 text-sm text-red-600">{job.error}</div>}
      {/* result summary */}
      {r && (
        <div className="mt-3 grid gap-2 text-sm sm:grid-cols-3">
          {r.runs && (
            <div className="rounded-lg bg-white p-2">
              <div className="text-xs font-semibold text-slate-400">Сбор</div>
              {r.runs.map((run: any) => (
                <div key={run.id} className="flex justify-between">
                  <span>{run.source}</span>
                  <span className={run.status === "success" ? "text-emerald-600" : "text-amber-600"}>
                    {run.records_found}
                  </span>
                </div>
              ))}
            </div>
          )}
          {r.dictionary && (
            <div className="rounded-lg bg-white p-2">
              <div className="text-xs font-semibold text-slate-400">Справочник</div>
              <div className="text-lg font-bold text-brand-700">{r.dictionary.services}</div>
              <div className="text-xs text-slate-400">услуг из данных</div>
            </div>
          )}
          {r.normalization && (
            <div className="rounded-lg bg-white p-2">
              <div className="text-xs font-semibold text-slate-400">Нормализация</div>
              <div className="text-sm"><b className="text-emerald-600">{r.normalization.matched}</b> привязано</div>
              <div className="text-xs text-amber-600">{r.normalization.unmatched} в очередь</div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function StatCard({ label, value, accent }: { label: string; value: number | undefined; accent?: string }) {
  const color = accent === "emerald" ? "text-emerald-600" : accent === "amber" ? "text-amber-600"
    : accent === "brand" ? "text-brand-600" : "text-ink";
  return (
    <div className="card p-4">
      <div className={`text-2xl font-extrabold ${color}`}>{value ?? "—"}</div>
      <div className="text-xs text-slate-500">{label}</div>
    </div>
  );
}

function DistCard({ title, data, labels }: { title: string; data: Record<string, number>; labels?: Record<string, string> }) {
  const entries = Object.entries(data || {}).sort((a, b) => b[1] - a[1]);
  const max = Math.max(1, ...entries.map((e) => e[1]));
  return (
    <div className="card p-5">
      <div className="mb-3 font-bold text-ink">{title}</div>
      <div className="space-y-2">
        {entries.map(([k, v]) => (
          <div key={k}>
            <div className="mb-0.5 flex justify-between text-xs text-slate-500">
              <span>{labels?.[k] || k || "—"}</span><span className="font-medium text-ink">{v}</span>
            </div>
            <div className="h-2 rounded-full bg-slate-100">
              <div className="h-2 rounded-full bg-brand-500" style={{ width: `${(v / max) * 100}%` }} />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
