export type Category = "laboratory" | "doctor" | "diagnostic" | "procedure";

export interface Suggestion {
  id: string;
  code: string;
  name: string;
  category: Category;
  specialty?: string;
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
    specialty?: string;
    tarif_code?: string;
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
  services_by_category: Record<string, number>;
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

// ---- Doctors (idoctor clone) ----
export interface DoctorRegion {
  slug: string;
  name: string;
  count: number;
}
export interface DoctorSpecialty {
  alias: string;
  name: string;
  count: number;
}
export interface DoctorsMeta {
  regions: DoctorRegion[];
  specialties: DoctorSpecialty[];
  total: number;
}
export interface DoctorClinic {
  name?: string;
  short?: string;
  address?: string;
  price?: number | null;
  price_discount?: number | null;
  discount?: number | null;
  online_booking?: boolean;
  lat?: string;
  lng?: string;
  schedule?: { day: string; start: string | null; end: string | null; work: boolean; h24?: boolean }[];
}
export interface DoctorCard {
  id: number;
  name: string;
  avatar: string | null;
  specialties: { name: string; alias: string }[];
  primary_specialty: string | null;
  experience_years: number | null;
  category: string | null;
  accepts_children: boolean;
  age_min: string | null;
  age_max: string | null;
  rating: number | null;
  reviews: number;
  verified: boolean;
  top: boolean;
  min_price: number | null;
  online_booking: boolean;
  city: string | null;
  region: string;
  clinics_count: number;
  clinic: DoctorClinic | null;
}
export interface DoctorsResult {
  total: number;
  page: number;
  page_size: number;
  pages: number;
  region: string | null;
  region_name: string | null;
  doctors: DoctorCard[];
}
export interface DoctorRecommendation {
  type: "bestValue" | "cheapest" | "topRated" | "popular" | "experienced";
  doctor: DoctorCard;
  below_avg_pct: number;
  cheaper_than_avg: number;
  rating: number | null;
  reviews: number;
  experience: number | null;
}
export interface DoctorRecommendations {
  items: DoctorRecommendation[];
  avg_price: number | null;
}

// ---- Diseases ("Лечение заболеваний") ----
export interface DiseaseRef { alias: string; name: string; }
export interface IllnessCategory {
  alias: string;
  name: string;
  count: number;
  diseases: DiseaseRef[];
}
export interface IllnessCategories {
  total_diseases: number;
  categories: IllnessCategory[];
}
export interface IllnessDetail {
  id: number;
  alias: string;
  name: string;
  skills: DiseaseRef[];
  similar: DiseaseRef[];
  doctors: DoctorCard[];
  doctors_total: number;
  region: string | null;
  region_name: string | null;
}

export interface DoctorReview {
  author: string;
  rating: number | string | null;
  text: string;
  tags: string[];
  reply: string | null;
  created_at: string | null;
  visit_date: string | null;
}
export interface DoctorService {
  name?: string;
  price?: number | null;
  priceWithDiscount?: number | null;
  [k: string]: any;
}
export interface DoctorDetail extends DoctorCard {
  alias: string;
  partner: boolean;
  clinics: DoctorClinic[];
  diseases: string[];
  description: string | null;
  services: DoctorService[];
  reviews_list: DoctorReview[];
  has_comments: boolean;
  online_bookings: number;
  profile_fetched: boolean;
  profile_url: string | null;
}

export interface HistorySeries {
  service_id: string | null;
  clinic_id: string | null;
  series: { clinic_id: string; clinic_name: string; points: { recorded_at: string; price_kzt: number }[] }[];
}
