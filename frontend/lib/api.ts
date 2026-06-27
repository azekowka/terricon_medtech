import type {
  ClinicCard,
  ClinicListItem,
  DoctorDetail,
  DoctorRecommendations as DoctorRecs,
  DoctorsMeta,
  DoctorsResult,
  HistorySeries,
  Meta,
  SearchResult,
  ServiceItem,
  Suggestion,
} from "./types";

export const API_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

async function get<T>(path: string, params?: Record<string, any>): Promise<T> {
  const url = new URL(API_URL + path);
  if (params) {
    for (const [k, v] of Object.entries(params)) {
      if (v !== undefined && v !== null && v !== "") url.searchParams.set(k, String(v));
    }
  }
  const res = await fetch(url.toString(), { cache: "no-store" });
  if (!res.ok) throw new Error(`API ${res.status}: ${path}`);
  return res.json();
}

async function post<T>(path: string, body: any): Promise<T> {
  const res = await fetch(API_URL + path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error(`API ${res.status}: ${path}`);
  return res.json();
}

export const api = {
  meta: () => get<Meta>("/api/meta"),
  autocomplete: (q: string) =>
    get<{ suggestions: Suggestion[] }>("/api/search/autocomplete", { q, limit: 8 }),
  search: (params: Record<string, any>) => get<SearchResult>("/api/search", params),
  services: (params?: Record<string, any>) => get<ServiceItem[]>("/api/services", params),
  service: (id: string) => get<any>(`/api/services/${id}`),
  clinics: (params?: Record<string, any>) => get<ClinicListItem[]>("/api/clinics", params),
  clinic: (id: string) => get<ClinicCard>(`/api/clinics/${id}`),
  compare: (params: Record<string, any>) => get<SearchResult>("/api/compare", params),
  history: (params: Record<string, any>) => get<HistorySeries>("/api/history", params),
  // admin
  stats: () => get<any>("/api/admin/stats"),
  parseLogs: () => get<any[]>("/api/admin/parse-logs"),
  unmatched: (status = "pending") => get<any[]>("/api/admin/unmatched", { status }),
  triggerParse: (body: { sources?: string[]; include_live?: boolean }) =>
    post<any>("/api/admin/parse", body),
  resolveUnmatched: (id: string, body: { service_id: string; add_synonym: boolean }) =>
    post<any>(`/api/admin/unmatched/${id}/resolve`, body),
  subscribe: (body: { email: string; service_id: string; clinic_id?: string; target_price_kzt?: number }) =>
    post<any>("/api/subscriptions", body),
  // doctors (idoctor clone)
  doctorsMeta: () => get<DoctorsMeta>("/api/doctors/meta"),
  doctors: (params: Record<string, any>) => get<DoctorsResult>("/api/doctors", params),
  doctor: (id: number) => get<DoctorDetail>(`/api/doctors/${id}`),
  doctorProfile: (id: number) => get<DoctorDetail>(`/api/doctors/${id}/profile`),
  doctorRecommendations: (params: Record<string, any>) =>
    get<DoctorRecs>("/api/doctors/recommendations", params),
  mapCities: () => get<{ cities: any[] }>("/api/map/cities"),
  assistantChat: (message: string, locale: string, history: { role: string; text: string }[] = []) =>
    post<{ reply: string; actions: { label: string; href: string }[] }>("/api/assistant/chat", {
      message,
      locale,
      history,
    }),
};
