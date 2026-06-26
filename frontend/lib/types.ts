export type Category = "laboratory" | "doctor" | "diagnostic" | "procedure";

export interface Suggestion {
  id: string;
  code: string;
  name: string;
  category: Category;
  offers_count: number;
}

export interface ServiceItem {
  id: string;
  code: string;
  name: string;
  category: Category;
  category_label: string;
  synonyms: string[];
  duration_days: number | null;
  offers_count: number;
}

export interface Offer {
  price_id: string;
  clinic_id: string;
  clinic_name: string;
  city: string;
  address: string;
  phone: string;
  working_hours: string;
  website: string;
  rating: number | null;
  has_online_booking: boolean;
  lat: number | null;
  lng: number | null;
  service_name_raw: string;
  service_name_norm: string;
  category: string;
  price_kzt: number;
  currency: string;
  duration_days: number | null;
  source: string;
  source_url: string;
  parsed_at: string;
  is_stale: boolean;
  distance_km: number | null;
  is_cheapest?: boolean;
}

export interface SearchResult {
  service: {
    id: string;
    code: string;
    name: string;
    category: Category;
    duration_days: number | null;
  } | null;
  query: string | null;
  stats: { count: number; min_price: number | null; max_price: number | null; avg_price: number | null };
  offers: Offer[];
}

export interface Meta {
  cities: string[];
  sources: string[];
  categories: { key: Category; label: string }[];
  category_labels: Record<string, string>;
  counts: { clinics: number; services: number; active_prices: number; cities: number; sources: number };
  price_range: { min: number | null; max: number | null };
  last_updated: string | null;
}

export interface ClinicListItem {
  id: string;
  name: string;
  city: string;
  address: string;
  phone: string;
  working_hours: string;
  website: string;
  source: string;
  lat: number | null;
  lng: number | null;
  rating: number | null;
  has_online_booking: boolean;
  services_count: number;
}

export interface ClinicCard extends ClinicListItem {
  services: {
    price_id: string;
    service_id: string | null;
    service_name: string;
    service_name_raw: string;
    category: string;
    category_label: string;
    price_kzt: number;
    currency: string;
    duration_days: number | null;
    source_url: string;
    parsed_at: string;
    matched: boolean;
  }[];
}

export interface HistorySeries {
  service_id: string | null;
  clinic_id: string | null;
  series: { clinic_id: string; clinic_name: string; points: { recorded_at: string; price_kzt: number }[] }[];
}
