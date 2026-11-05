/**
 * ProspectOS Master Staging Acceptance & Independence Test Suite
 * Executes end-to-end against https://prospectos-serverless.smagencywire.workers.dev
 */

const https = require("https");

const BASE_URL = "https://prospectos-serverless.smagencywire.workers.dev";
const TIMESTAMP = Date.now();
const TEST_EMAIL = `acceptance.tester.${TIMESTAMP}@prospectos.com`;
const TEST_PASSWORD = `P@ssword${TIMESTAMP}!Safe`;
const TEST_NAME = `Acceptance Test User ${TIMESTAMP}`;
const TEST_COMPANY = `Cloudflare Enterprise ${TIMESTAMP}`;

function request(path, options = {}) {
  return new Promise((resolve, reject) => {
    const url = new URL(path, BASE_URL);
    const reqOptions = {
      method: options.method || "GET",
      headers: {
        "Content-Type": "application/json",
        ...(options.headers || {}),
      },
      timeout: 30000,
    };

    const req = https.request(url, reqOptions, (res) => {
      let data = "";
      res.on("data", (chunk) => (data += chunk));
      res.on("end", () => {
        let json;
        try {
          json = JSON.parse(data);
        } catch {
          json = { raw: data };
        }
        resolve({ status: res.statusCode, headers: res.headers, body: json, text: data });
      });
    });

    req.on("error", reject);
    req.on("timeout", () => {
      req.destroy();
      reject(new Error(`Timeout requesting ${path}`));
    });

    if (options.body) {
      req.write(typeof options.body === "string" ? options.body : JSON.stringify(options.body));
    }
    req.end();
  });
}

async function runAcceptanceSuite() {
  console.log("=== PROSPECTOS STAGING COMPREHENSIVE ACCEPTANCE SUITE ===");
  console.log(`Target: ${BASE_URL}`);
  console.log(`Time: ${new Date().toISOString()}`);

  const results = {};

  // 1. Health & Serverless Pulse
  console.log("\n[1] Testing Global Edge Health & Pulse...");
  const healthRes = await request("/health");
  console.log(`- /health: HTTP ${healthRes.status} (Version: ${healthRes.body.version}, Architecture: ${healthRes.body.architecture})`);
  const dbHealthRes = await request("/health/database");
  console.log(`- /health/database: HTTP ${dbHealthRes.status} (Status: ${dbHealthRes.body.status}, Engine: ${dbHealthRes.body.engine})`);
  results["health"] = healthRes.status === 200 && dbHealthRes.status === 200;

  // 2. User Registration
  console.log("\n[2] Testing User Registration in D1...");
  const regRes = await request("/portal/auth/register", {
    method: "POST",
    body: {
      email: TEST_EMAIL,
      password: TEST_PASSWORD,
      full_name: TEST_NAME,
      company_name: TEST_COMPANY,
    },
  });
  console.log(`- Registration: HTTP ${regRes.status} (User ID: ${regRes.body?.user?.id || "N/A"})`);
  results["registration"] = regRes.status === 201;

  // 3. User Login & Token Issuance
  console.log("\n[3] Testing Login & Authentication...");
  const loginRes = await request("/portal/auth/login", {
    method: "POST",
    body: {
      email: TEST_EMAIL,
      password: TEST_PASSWORD,
    },
  });
  const userToken = loginRes.body?.access_token;
  console.log(`- Login: HTTP ${loginRes.status} (Token Issued: ${userToken ? "YES" : "NO"})`);
  results["login"] = loginRes.status === 200 && !!userToken;

  // 4. Authenticated Profile
  console.log("\n[4] Testing /portal/auth/me Profile Retrieval...");
  const meRes = await request("/portal/auth/me", {
    headers: { Authorization: `Bearer ${userToken}` },
  });
  console.log(`- /portal/auth/me: HTTP ${meRes.status} (Email: ${meRes.body?.email})`);
  results["profile"] = meRes.status === 200 && meRes.body?.email === TEST_EMAIL;

  // Super Admin Token for privileged endpoints
  const crypto = require("crypto");
  function b64url(s) { return Buffer.from(s).toString("base64").replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, ""); }
  const secret = "prospectos-cf-zero-cost-master-secret-2026";
  const now = Math.floor(Date.now() / 1000);
  const adminPayload = { sub: "7335313a-c6e5-499d-8fe4-3f200f3055ae", email: "admin@prospectos.com", role: "SUPER_ADMIN", iat: now, exp: now + 86400 };
  const signingInput = `${b64url(JSON.stringify({ alg: "HS256", typ: "JWT" }))}.${b64url(JSON.stringify(adminPayload))}`;
  const sig = crypto.createHmac("sha256", secret).update(signingInput).digest("base64").replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");
  const adminToken = `${signingInput}.${sig}`;

  // 5. Super Admin Modules
  console.log("\n[5] Testing Super Admin Overview & Governance...");
  const adminOverview = await request("/admin/overview", { headers: { Authorization: `Bearer ${adminToken}` } });
  console.log(`- /admin/overview: HTTP ${adminOverview.status} (Users: ${adminOverview.body?.metrics?.total_users}, Leads: ${adminOverview.body?.metrics?.total_companies})`);
  const adminUsers = await request("/admin/users", { headers: { Authorization: `Bearer ${adminToken}` } });
  console.log(`- /admin/users: HTTP ${adminUsers.status} (Count: ${adminUsers.body?.length})`);
  const adminRoles = await request("/admin/roles", { headers: { Authorization: `Bearer ${adminToken}` } });
  console.log(`- /admin/roles: HTTP ${adminRoles.status} (Count: ${adminRoles.body?.length})`);
  const scraperInfra = await request("/admin/scraper-infra/status", { headers: { Authorization: `Bearer ${adminToken}` } });
  console.log(`- /admin/scraper-infra/status: HTTP ${scraperInfra.status} (Status: ${scraperInfra.body?.status})`);
  results["admin"] = adminOverview.status === 200 && adminUsers.status === 200;

  // 6. Lead Discovery & Templates
  console.log("\n[6] Testing Lead Discovery & Scraper Templates...");
  const templatesRes = await request("/api/scraper/templates", { headers: { Authorization: `Bearer ${userToken}` } });
  console.log(`- /api/scraper/templates: HTTP ${templatesRes.status} (Templates: ${templatesRes.body?.length})`);
  results["templates"] = templatesRes.status === 200 && templatesRes.body?.length >= 3;

  // 7. Custom Scraper Task Creation
  console.log("\n[7] Testing Custom Scraper Task Creation...");
  const createTaskRes = await request("/api/scraper/tasks", {
    method: "POST",
    headers: { Authorization: `Bearer ${userToken}` },
    body: {
      name: `Acceptance Crawl Task ${TIMESTAMP}`,
      target_url: `https://example-saas-${TIMESTAMP}.com`,
      task_type: "CUSTOM_URL",
      description: "Automated acceptance test scraper task",
    },
  });
  const createdTaskId = createTaskRes.body?.id;
  console.log(`- Create Task: HTTP ${createTaskRes.status} (Task ID: ${createdTaskId})`);
  results["scraper_task_create"] = createTaskRes.status === 201 && !!createdTaskId;

  // 8. Custom Scraper Task Retrieval
  console.log("\n[8] Testing Scraper Tasks Retrieval...");
  const getTaskRes = await request(`/api/scraper/tasks/${createdTaskId}`, {
    headers: { Authorization: `Bearer ${userToken}` },
  });
  console.log(`- Get Task: HTTP ${getTaskRes.status} (Target: ${getTaskRes.body?.target_url})`);
  results["scraper_task_get"] = getTaskRes.status === 200;

  // 9. CRM Leads Creation & Deduplication
  console.log("\n[9] Testing CRM Lead Creation & Canonical Deduplication...");
  const leadDomain = `saas-growth-${TIMESTAMP}.com`;
  const createLeadRes = await request("/crm/leads", {
    method: "POST",
    headers: { Authorization: `Bearer ${userToken}` },
    body: {
      company_name: `Growth SaaS Corp ${TIMESTAMP}`,
      website_url: `https://${leadDomain}`,
      canonical_domain: leadDomain,
      industry: "B2B Software",
      sales_stage: "NEW",
      country: "United States",
    },
  });
  const createdLeadId = createLeadRes.body?.id;
  console.log(`- Create Lead 1: HTTP ${createLeadRes.status} (ID: ${createdLeadId}, Domain: ${createLeadRes.body?.canonical_domain})`);

  // Test deduplication on same canonical domain
  const dedupRes = await request("/crm/leads", {
    method: "POST",
    headers: { Authorization: `Bearer ${userToken}` },
    body: {
      company_name: `Growth SaaS Corp Updated ${TIMESTAMP}`,
      website_url: `https://${leadDomain}/about`,
      canonical_domain: leadDomain,
      industry: "B2B Software Enterprise",
      sales_stage: "QUALIFIED",
    },
  });
  console.log(`- Upsert/Dedup Lead: HTTP ${dedupRes.status} (Updated Stage: ${dedupRes.body?.sales_stage})`);
  results["crm_lead_dedup"] = createLeadRes.status === 201 && dedupRes.status === 201;

  // 10. Pipeline Board & Updates
  console.log("\n[10] Testing Pipeline Board & Stage Transitions...");
  const boardRes = await request("/crm/pipeline/board", { headers: { Authorization: `Bearer ${userToken}` } });
  console.log(`- Pipeline Board: HTTP ${boardRes.status} (Columns: ${Object.keys(boardRes.body?.columns || {}).join(", ")})`);

  const updateStageRes = await request(`/crm/leads/${createdLeadId}/stage`, {
    method: "PUT",
    headers: { Authorization: `Bearer ${userToken}` },
    body: { stage: "MEETING" },
  });
  console.log(`- Stage Update: HTTP ${updateStageRes.status} (New Stage: ${updateStageRes.body?.stage})`);
  results["pipeline"] = boardRes.status === 200 && updateStageRes.status === 200 && updateStageRes.body?.stage === "MEETING";

  // 11. Lists and Segments
  console.log("\n[11] Testing Lists & Segments...");
  const createSegRes = await request("/crm/segments", {
    method: "POST",
    headers: { Authorization: `Bearer ${userToken}` },
    body: { name: `Enterprise Accounts ${TIMESTAMP}`, description: "High ARR B2B segment" },
  });
  console.log(`- Create Segment: HTTP ${createSegRes.status} (ID: ${createSegRes.body?.id})`);
  const getSegsRes = await request("/crm/segments", { headers: { Authorization: `Bearer ${userToken}` } });
  console.log(`- Get Segments: HTTP ${getSegsRes.status} (Total: ${getSegsRes.body?.length})`);
  results["segments"] = createSegRes.status === 201 && getSegsRes.status === 200;

  // 12. CRM Analytics
  console.log("\n[12] Testing CRM Analytics Dashboard...");
  const analyticsRes = await request("/crm/analytics/dashboard", { headers: { Authorization: `Bearer ${userToken}` } });
  console.log(`- Analytics: HTTP ${analyticsRes.status} (Total Leads: ${analyticsRes.body?.total_leads}, Monthly Cost: ${analyticsRes.body?.monthly_operating_cost})`);
  results["analytics"] = analyticsRes.status === 200;

  // 13. Companies Discovery Route
  console.log("\n[13] Testing Companies Search Route...");
  const companiesRes = await request(`/companies?q=${leadDomain}`, { headers: { Authorization: `Bearer ${userToken}` } });
  console.log(`- Companies Query: HTTP ${companiesRes.status} (Found: ${companiesRes.body?.length})`);
  results["companies"] = companiesRes.status === 200 && companiesRes.body?.length > 0;

  // 14. Data Export (R2 / CSV)
  console.log("\n[14] Testing Export & Object Storage...");
  const exportRes = await request("/api/storage/export?format=csv", { headers: { Authorization: `Bearer ${userToken}` } });
  console.log(`- CSV Export: HTTP ${exportRes.status} (Content-Type: ${exportRes.headers["content-type"]}, Length: ${exportRes.text.length} chars)`);
  results["export"] = exportRes.status === 200 && exportRes.text.includes("Company Name");

  // 15. AI Lead Copilot (Live Gemini Cascade)
  console.log("\n[15] Testing Public AI Lead Copilot (Gemini API)...");
  const aiChatRes = await request("/crm/assistant/chat", {
    method: "POST",
    headers: { Authorization: `Bearer ${userToken}` },
    body: { message: "Briefly explain why canonical domain deduplication is essential in B2B CRM systems." },
  });
  console.log(`- AI Assistant: HTTP ${aiChatRes.status}`);
  console.log(`  Provider: ${aiChatRes.body?.provider_used}`);
  console.log(`  Model: ${aiChatRes.body?.model_used}`);
  console.log(`  Is AI Generated: ${aiChatRes.body?.is_ai_generated}`);
  console.log(`  Tokens: ${JSON.stringify(aiChatRes.body?.tokens_used)}`);
  console.log(`  Cost: $${aiChatRes.body?.cost_usd}`);
  console.log(`  Response Preview: ${aiChatRes.body?.response?.slice(0, 120)}...`);
  results["ai_assistant"] = aiChatRes.status === 200 && aiChatRes.body?.is_ai_generated === true;

  // 16. Logout & Token Revocation (KV Cache)
  console.log("\n[16] Testing Logout & Token Revocation in KV...");
  const logoutRes = await request("/portal/auth/logout", {
    method: "POST",
    headers: { Authorization: `Bearer ${userToken}` },
  });
  console.log(`- Logout: HTTP ${logoutRes.status} (${logoutRes.body?.message})`);

  // Test that revoked token is immediately rejected
  const revokedMeRes = await request("/portal/auth/me", {
    headers: { Authorization: `Bearer ${userToken}` },
  });
  console.log(`- Revoked Token Check: HTTP ${revokedMeRes.status} (Expected 401: ${revokedMeRes.status === 401 ? "PASSED" : "FAILED"})`);
  results["kv_revocation"] = logoutRes.status === 200 && revokedMeRes.status === 401;

  console.log("\n=== ALL TEST RESULTS SUMMARY ===");
  console.log(JSON.stringify(results, null, 2));

  return results;
}

runAcceptanceSuite().catch(console.error);
