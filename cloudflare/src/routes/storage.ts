/**
 * ProspectOS Cloudflare Serverless - R2 Object Storage & Export Endpoints
 */

import { Hono } from "hono";
import { Env, UserPayload } from "../types/env";
import { authMiddleware } from "../auth/middleware";

export const storageRouter = new Hono<{ Bindings: Env; Variables: { user: UserPayload } }>();

storageRouter.use("*", authMiddleware);

storageRouter.get("/export", async (c) => {
  const format = c.req.query("format") || "csv";
  const records = await c.env.DB.prepare(
    "SELECT id, company_name, website_url, canonical_domain, industry, country, company_status, created_at FROM companies LIMIT 1000"
  ).all<any>();

  const rows = records.results || [];
  let fileContent = "";
  let mimeType = "text/csv";
  const fileName = `prospectos_leads_export_${Date.now()}.${format}`;

  if (format === "json") {
    fileContent = JSON.stringify(rows, null, 2);
    mimeType = "application/json";
  } else {
    // Generate CSV
    const headers = ["ID", "Company Name", "Website", "Domain", "Industry", "Country", "Status", "Created At"];
    const lines = [headers.join(",")];
    for (const r of rows) {
      lines.push(
        [
          `"${r.id}"`,
          `"${(r.company_name || "").replace(/"/g, '""')}"`,
          `"${(r.website_url || "").replace(/"/g, '""')}"`,
          `"${(r.canonical_domain || "").replace(/"/g, '""')}"`,
          `"${(r.industry || "").replace(/"/g, '""')}"`,
          `"${(r.country || "").replace(/"/g, '""')}"`,
          `"${r.company_status || ""}"`,
          `"${r.created_at || ""}"`,
        ].join(",")
      );
    }
    fileContent = lines.join("\n");
  }

  // Store in Cloudflare R2 if binding is active
  if (c.env.R2) {
    await c.env.R2.put(`exports/${fileName}`, fileContent, {
      httpMetadata: { contentType: mimeType },
    });
  }

  return new Response(fileContent, {
    headers: {
      "Content-Type": mimeType,
      "Content-Disposition": `attachment; filename="${fileName}"`,
    },
  });
});

storageRouter.get("/download/:fileId", async (c) => {
  const fileId = c.req.param("fileId");
  if (!c.env.R2) {
    return c.json({ detail: "R2 storage binding is not configured in this environment." }, 501);
  }

  const object = await c.env.R2.get(`exports/${fileId}`);
  if (!object) {
    return c.json({ detail: "File not found in R2 storage." }, 404);
  }

  const headers = new Headers();
  object.writeHttpMetadata(headers);
  headers.set("etag", object.httpEtag);

  return new Response(object.body, { headers });
});
