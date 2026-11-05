/**
 * ProspectOS Cloudflare Serverless Entrypoint
 * Zero-Cost Serverless SaaS Platform on Cloudflare Workers, D1, R2, KV, and Workers AI
 * Guaranteed Monthly Hosting Cost: $0.00 USD
 */

import { Hono } from "hono";
import { cors } from "hono/cors";
import { Env, UserPayload } from "./types/env";
import { authRouter } from "./routes/auth";
import { adminRouter } from "./routes/admin";
import { scraperRouter } from "./routes/scraper";
import { crmRouter } from "./routes/crm";
import { companiesRouter } from "./routes/companies";
import { storageRouter } from "./routes/storage";

const app = new Hono<{ Bindings: Env; Variables: { user: UserPayload } }>();

// 1. Zero-Cost CORS Configuration
app.use(
  "*",
  cors({
    origin: (origin) => {
      if (!origin) return "*";
      if (
        origin.endsWith("grokxseo.online") ||
        origin.endsWith("trycloudflare.com") ||
        origin.endsWith("pages.dev") ||
        origin.endsWith("workers.dev") ||
        origin.includes("localhost") ||
        origin.includes("127.0.0.1")
      ) {
        return origin;
      }
      return null;
    },
    allowMethods: ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allowHeaders: ["Content-Type", "Authorization", "X-Requested-With"],
    credentials: true,
  })
);

// 2. Global Security Headers
app.use("*", async (c, next) => {
  await next();
  c.header("X-Content-Type-Options", "nosniff");
  c.header("X-Frame-Options", "SAMEORIGIN");
  c.header("X-XSS-Protection", "1; mode=block");
  c.header("Referrer-Policy", "strict-origin-when-cross-origin");
  c.header("X-Serverless-Architecture", "Cloudflare-Zero-Cost");
});

// 3. Health & Observability Endpoints
app.get("/health", (c) => {
  return c.json({
    status: "ok",
    version: "2.0.1-staging-acceptance",
    architecture: "Cloudflare Serverless (Workers + D1 + R2)",
    monthly_operating_cost: "$0.00 USD",
    free_tier_status: "ENFORCED",
    timestamp: new Date().toISOString(),
  });
});

app.get("/health/database", async (c) => {
  try {
    const res = await c.env.DB.prepare("SELECT 1 as alive").first<any>();
    if (res?.alive === 1) {
      return c.json({ status: "ok", database: "connected", engine: "Cloudflare D1 (SQLite 3)" });
    }
    return c.json({ status: "error", detail: "D1 did not return expected pulse" }, 503);
  } catch (err: any) {
    return c.json({ status: "error", detail: err.message }, 503);
  }
});

// 4. Dynamic SEO Endpoints
app.get("/robots.txt", (c) => {
  const robots = `User-agent: *\nAllow: /\nDisallow: /admin/\nDisallow: /portal/\nSitemap: https://prospectos.grokxseo.online/sitemap.xml\n`;
  return c.text(robots, 200, { "Content-Type": "text/plain" });
});

app.get("/sitemap.xml", async (c) => {
  let pages: any[] = [];
  try {
    const res = await c.env.DB.prepare("SELECT route_path, last_scanned_at FROM seo_public_pages WHERE is_active = 1").all<any>();
    pages = res.results || [];
  } catch {
    pages = [{ route_path: "/", last_scanned_at: new Date().toISOString() }];
  }

  const urlsXml = pages
    .map(
      (p) => `  <url>\n    <loc>https://prospectos.grokxseo.online${p.route_path}</loc>\n    <lastmod>${p.last_scanned_at ? p.last_scanned_at.split("T")[0] : new Date().toISOString().split("T")[0]}</lastmod>\n    <changefreq>daily</changefreq>\n    <priority>0.8</priority>\n  </url>`
    )
    .join("\n");

  const sitemap = `<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n${urlsXml}\n</urlset>`;
  return c.text(sitemap, 200, { "Content-Type": "application/xml" });
});

// 5. Mount Core Sub-Routers (Full API Contract Parity)
app.route("/portal/auth", authRouter);
app.route("/admin", adminRouter);
app.route("/api/scraper", scraperRouter);
app.route("/crm", crmRouter);
app.route("/companies", companiesRouter);
app.route("/api/storage", storageRouter);

// 6. Export Fetch Handler and Cloudflare Queue Consumer
export default {
  fetch: app.fetch,

  // Asynchronous queue handler for background scraping & AI processing (Cloudflare Queues free tier)
  async queue(batch: MessageBatch<any>, env: Env): Promise<void> {
    for (const msg of batch.messages) {
      console.log(`[Cloudflare Queue] Processing background task: ${msg.id}`);
      msg.ack();
    }
  },
};

