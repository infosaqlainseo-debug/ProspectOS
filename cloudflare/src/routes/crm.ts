/**
 * ProspectOS Cloudflare Serverless - CRM Endpoints
 */

import { Hono } from "hono";
import { Env, UserPayload } from "../types/env";
import { authMiddleware } from "../auth/middleware";
import { UnifiedAIProvider } from "../services/ai-provider";

export const crmRouter = new Hono<{ Bindings: Env; Variables: { user: UserPayload } }>();

crmRouter.use("*", authMiddleware);

crmRouter.get("/leads", async (c) => {
  const stage = c.req.query("stage");
  let query = "SELECT id, company_name, website_url, canonical_domain, industry, country, company_status, created_at FROM companies";
  const params: any[] = [];

  if (stage) {
    query += " WHERE company_status = ?";
    params.push(stage);
  }

  query += " ORDER BY created_at DESC LIMIT 100";
  const stmt = c.env.DB.prepare(query);
  const leads = params.length > 0 ? await stmt.bind(...params).all<any>() : await stmt.all<any>();

  return c.json({
    leads: leads.results || [],
    total: (leads.results || []).length,
  });
});

crmRouter.post("/leads", async (c) => {
  try {
    const body = await c.req.json().catch(() => ({}));
    const id = crypto.randomUUID();
    const now = new Date().toISOString();
    const name = body.company_name || body.name || "Untitled Prospect";
    const website = body.website_url || body.website || "https://example.com";
    const domain = body.canonical_domain || (typeof website === "string" ? website.replace(/^https?:\/\//, "").split("/")[0] : "example.com");

    await c.env.DB.prepare(
      `INSERT INTO companies (
        id, company_name, website_url, canonical_domain, country, city, industry, 
        sales_stage, stage_updated_at, lead_priority, gdrive_sync_status,
        company_status, first_discovered_at, created_at, updated_at
      ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
      ON CONFLICT(canonical_domain) DO UPDATE SET
        company_name = excluded.company_name,
        website_url = excluded.website_url,
        sales_stage = excluded.sales_stage,
        stage_updated_at = excluded.stage_updated_at,
        lead_priority = excluded.lead_priority,
        company_status = excluded.company_status,
        updated_at = excluded.updated_at`
    )
      .bind(
        id,
        name,
        website,
        domain,
        body.country || "Global",
        body.city || "",
        body.industry || "General B2B",
        body.sales_stage || body.company_status || "NEW",
        now,
        body.lead_priority || "MEDIUM",
        "NOT_SYNCED",
        body.company_status || body.sales_stage || "NEW",
        now,
        now,
        now
      )
      .run();

    const created = await c.env.DB.prepare("SELECT * FROM companies WHERE canonical_domain = ?").bind(domain).first<any>();
    return c.json(created, 201);
  } catch (err: any) {
    return c.json({ detail: err.message, stack: err.stack }, 500);
  }
});

crmRouter.get("/leads/:id", async (c) => {
  const id = c.req.param("id");
  const lead = await c.env.DB.prepare("SELECT * FROM companies WHERE id = ?").bind(id).first<any>();
  if (!lead) return c.json({ detail: "Lead not found." }, 404);
  return c.json(lead);
});

crmRouter.put("/leads/:id", async (c) => {
  const id = c.req.param("id");
  const body = await c.req.json().catch(() => ({}));
  const now = new Date().toISOString();

  await c.env.DB.prepare(
    `UPDATE companies SET 
      company_name = COALESCE(?, company_name),
      website_url = COALESCE(?, website_url),
      company_status = COALESCE(?, company_status),
      industry = COALESCE(?, industry),
      updated_at = ?
    WHERE id = ?`
  )
    .bind(body.company_name, body.website_url, body.company_status, body.industry, now, id)
    .run();

  const updated = await c.env.DB.prepare("SELECT * FROM companies WHERE id = ?").bind(id).first<any>();
  return c.json(updated);
});

crmRouter.delete("/leads/:id", async (c) => {
  const id = c.req.param("id");
  await c.env.DB.prepare("DELETE FROM companies WHERE id = ?").bind(id).run();
  return c.json({ success: true, message: "Lead deleted successfully." });
});

crmRouter.get("/pipeline/board", async (c) => {
  const stages = ["NEW", "QUALIFIED", "CONTACTED", "MEETING", "PROPOSAL", "WON", "LOST"];
  const allLeads = await c.env.DB.prepare(
    "SELECT id, company_name, website_url, canonical_domain, company_status, created_at FROM companies"
  ).all<any>();

  const columns: Record<string, any[]> = {};
  for (const s of stages) {
    columns[s] = [];
  }

  for (const lead of allLeads.results || []) {
    const s = lead.company_status || "NEW";
    if (columns[s]) {
      columns[s].push(lead);
    } else {
      columns["NEW"].push(lead);
    }
  }

  return c.json({ columns });
});

crmRouter.put("/leads/:id/stage", async (c) => {
  const id = c.req.param("id");
  const body = await c.req.json().catch(() => ({}));
  const stage = body.stage || body.status || "NEW";
  const now = new Date().toISOString();

  await c.env.DB.prepare("UPDATE companies SET company_status = ?, updated_at = ? WHERE id = ?")
    .bind(stage, now, id)
    .run();

  return c.json({ success: true, id, stage });
});

crmRouter.get("/segments", async (c) => {
  const segs = await c.env.DB.prepare("SELECT * FROM crm_lead_segments ORDER BY name").all<any>();
  return c.json(segs.results || []);
});

crmRouter.post("/segments", async (c) => {
  const body = await c.req.json().catch(() => ({}));
  const id = crypto.randomUUID();
  const now = new Date().toISOString();

  await c.env.DB.prepare(
    "INSERT INTO crm_lead_segments (id, name, description, created_at, updated_at) VALUES (?, ?, ?, ?, ?)"
  )
    .bind(id, body.name || "Custom Segment", body.description || "", now, now)
    .run();

  const created = await c.env.DB.prepare("SELECT * FROM crm_lead_segments WHERE id = ?").bind(id).first<any>();
  return c.json(created, 201);
});

crmRouter.get("/analytics/dashboard", async (c) => {
  const total = await c.env.DB.prepare("SELECT count(*) as count FROM companies").first<any>();
  const won = await c.env.DB.prepare("SELECT count(*) as count FROM companies WHERE company_status = 'WON'").first<any>();
  const qualified = await c.env.DB.prepare("SELECT count(*) as count FROM companies WHERE company_status = 'QUALIFIED'").first<any>();

  return c.json({
    total_leads: total?.count || 0,
    qualified_leads: qualified?.count || 0,
    won_leads: won?.count || 0,
    conversion_rate: total?.count ? (((won?.count || 0) / total.count) * 100).toFixed(1) + "%" : "0.0%",
    monthly_operating_cost: "$0.00 USD",
  });
});

crmRouter.post("/assistant/chat", async (c) => {
  const body = await c.req.json().catch(() => ({}));
  const message = body.message || body.prompt || "";

  if (!message) {
    return c.json({ detail: "Message is required." }, 400);
  }

  const ai = new UnifiedAIProvider(c.env);
  const result = await ai.complete({
    prompt: message,
    systemPrompt: "You are the ProspectOS AI Lead Copilot. Assist with sales intelligence, ICP qualification, cold outreach strategy, and company analysis. Respond concisely in Markdown.",
  });

  return c.json({
    response: result.content,
    provider_used: result.provider,
    model_used: result.model,
    is_ai_generated: result.isAiGenerated,
    cost_usd: result.costUsd,
    tokens_used: result.tokensUsed,
    quota_status: result.quotaStatus,
    status_note: result.statusNote,
    fallback_occurred: result.fallbackOccurred,
  });
});

crmRouter.post("/import-from-scraper", async (c) => {
  const body = await c.req.json().catch(() => ({}));
  const recordIds: string[] = body.record_ids || [];

  let importedCount = 0;
  const now = new Date().toISOString();

  if (recordIds.length > 0) {
    for (const recId of recordIds) {
      const rec = await c.env.DB.prepare("SELECT * FROM extracted_records WHERE id = ?").bind(recId).first<any>();
      if (rec) {
        const leadId = crypto.randomUUID();
        await c.env.DB.prepare(
          `INSERT INTO companies (
            id, company_name, website_url, canonical_domain, description, 
            sales_stage, stage_updated_at, lead_priority, gdrive_sync_status,
            company_status, first_discovered_at, created_at, updated_at
          ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`
        )
          .bind(
            leadId,
            rec.company_name || "Scraped Lead",
            rec.source_url || rec.website,
            new URL(rec.source_url || rec.website || "https://example.com").hostname,
            rec.description || "",
            "NEW",
            now,
            "MEDIUM",
            "NOT_SYNCED",
            "NEW",
            now,
            now,
            now
          )
          .run();
        importedCount++;
      }
    }
  }

  return c.json({
    success: true,
    imported_count: importedCount,
    status: "COMPLETED",
  });
});
