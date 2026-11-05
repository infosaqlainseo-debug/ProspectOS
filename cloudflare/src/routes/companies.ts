/**
 * ProspectOS Cloudflare Serverless - Companies & Discovery Endpoints
 */

import { Hono } from "hono";
import { Env, UserPayload } from "../types/env";
import { authMiddleware } from "../auth/middleware";

export const companiesRouter = new Hono<{ Bindings: Env; Variables: { user: UserPayload } }>();

companiesRouter.use("*", authMiddleware);

companiesRouter.get("/", async (c) => {
  const query = c.req.query("q") || "";
  let sql = "SELECT id, company_name, website_url, canonical_domain, industry, country, company_status, created_at FROM companies";
  const params: any[] = [];

  if (query) {
    sql += " WHERE company_name LIKE ? OR canonical_domain LIKE ?";
    params.push(`%${query}%`, `%${query}%`);
  }

  sql += " ORDER BY created_at DESC LIMIT 50";
  const stmt = c.env.DB.prepare(sql);
  const res = params.length > 0 ? await stmt.bind(...params).all<any>() : await stmt.all<any>();

  return c.json(res.results || []);
});

companiesRouter.get("/:id", async (c) => {
  const id = c.req.param("id");
  const company = await c.env.DB.prepare("SELECT * FROM companies WHERE id = ?").bind(id).first<any>();
  if (!company) return c.json({ detail: "Company not found." }, 404);
  return c.json(company);
});

