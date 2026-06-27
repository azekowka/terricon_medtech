import { api } from "@/lib/api";
import { HomeView } from "@/components/HomeView";
import type { Meta, ServiceItem } from "@/lib/types";

export const dynamic = "force-dynamic";

async function getData(): Promise<{ meta: Meta | null; popular: ServiceItem[] }> {
  try {
    const [meta, popular] = await Promise.all([
      api.meta(),
      api.services({ sort: "popular", limit: 12 }),
    ]);
    return { meta, popular };
  } catch {
    return { meta: null, popular: [] };
  }
}

export default async function HomePage() {
  const { meta, popular } = await getData();
  return <HomeView meta={meta} popular={popular} />;
}
