import type { MetadataRoute } from "next";
import { readdirSync, statSync } from "node:fs";
import { join } from "node:path";

export const dynamic = "force-static";

const BASE_URL = "https://trendrider.net";

function getBlogSlugs(): string[] {
  const blogDir = join(process.cwd(), "app", "blog");
  return readdirSync(blogDir).filter((name) => {
    const full = join(blogDir, name);
    return statSync(full).isDirectory() && !name.startsWith("_");
  });
}

export default function sitemap(): MetadataRoute.Sitemap {
  const now = new Date();
  const slugs = getBlogSlugs();

  const staticRoutes: MetadataRoute.Sitemap = [
    { url: BASE_URL, lastModified: now, changeFrequency: "weekly", priority: 1 },
    { url: `${BASE_URL}/live`, lastModified: now, changeFrequency: "hourly", priority: 0.9 },
    { url: `${BASE_URL}/blog`, lastModified: now, changeFrequency: "weekly", priority: 0.8 },
    { url: `${BASE_URL}/terms`, lastModified: now, changeFrequency: "yearly", priority: 0.3 },
    { url: `${BASE_URL}/privacy`, lastModified: now, changeFrequency: "yearly", priority: 0.3 },
  ];

  const blogRoutes: MetadataRoute.Sitemap = slugs.map((slug) => ({
    url: `${BASE_URL}/blog/${slug}`,
    lastModified: now,
    changeFrequency: "monthly",
    priority: 0.7,
  }));

  return [...staticRoutes, ...blogRoutes];
}
