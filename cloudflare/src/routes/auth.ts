/**
 * ProspectOS Cloudflare Serverless - Authentication Routes
 */

import { Hono } from "hono";
import { Env, UserPayload } from "../types/env";
import { verifyPassword, hashPassword } from "../auth/password";
import { createAccessToken } from "../auth/jwt";
import { authMiddleware } from "../auth/middleware";

export const authRouter = new Hono<{ Bindings: Env; Variables: { user: UserPayload } }>();

authRouter.post("/register", async (c) => {
  const body = await c.req.json().catch(() => ({}));
  const email = (body.email || "").trim().toLowerCase();
  const password = body.password || "";
  const fullName = (body.full_name || body.fullName || "").trim();
  const companyName = (body.company_name || body.companyName || "").trim();

  if (!email || !password || !fullName) {
    return c.json({ detail: "Email, password, and full name are required." }, 400);
  }

  if (password.length < 8) {
    return c.json({ detail: "Password must be at least 8 characters long." }, 400);
  }

  // Check if user already exists
  const existing = await c.env.DB.prepare(
    "SELECT id FROM portal_users WHERE LOWER(email) = ? LIMIT 1"
  )
    .bind(email)
    .first<any>();

  if (existing) {
    return c.json({ detail: "A user with this email address already exists." }, 409);
  }

  // Optional: create company if specified
  let companyId: string | null = null;
  const nowStr = new Date().toISOString();
  if (companyName) {
    companyId = crypto.randomUUID();
    const domain = email.includes("@") ? email.split("@")[1] : "example.com";
    try {
      await c.env.DB.prepare(
        `INSERT INTO companies (
          id, company_name, canonical_domain, website_url, country, city, industry, 
          sales_stage, stage_updated_at, lead_priority, gdrive_sync_status,
          company_status, first_discovered_at, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`
      )
        .bind(
          companyId,
          companyName,
          domain,
          `https://${domain}`,
          "Global",
          "",
          "B2B",
          "NEW",
          nowStr,
          "MEDIUM",
          "NOT_SYNCED",
          "NEW",
          nowStr,
          nowStr,
          nowStr
        )
        .run();
    } catch {
      companyId = null;
    }
  }

  // Hash password with WebCrypto PBKDF2
  const hashedPassword = await hashPassword(password);
  const userId = crypto.randomUUID();

  await c.env.DB.prepare(
    "INSERT INTO portal_users (id, email, full_name, role, hashed_password, is_active, company_id, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)"
  )
    .bind(userId, email, fullName, "STANDARD_USER", hashedPassword, 1, companyId, nowStr, nowStr)
    .run();

  // Audit log
  await c.env.DB.prepare(
    "INSERT INTO portal_audit_logs (id, user_id, company_id, action, resource_type, resource_id, details, ip_address, timestamp) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)"
  )
    .bind(
      crypto.randomUUID(),
      userId,
      companyId,
      "USER_REGISTER_SUCCESS",
      "PORTAL_USER",
      userId,
      JSON.stringify({ email, fullName, companyName }),
      c.req.header("cf-connecting-ip") || "127.0.0.1",
      nowStr
    )
    .run()
    .catch(() => {});

  const secret = c.env.JWT_SECRET || "prospectos-cf-zero-cost-master-secret-2026";
  const token = await createAccessToken(
    {
      sub: userId,
      email: email,
      role: "STANDARD_USER",
      company_id: companyId,
    },
    secret
  );

  return c.json(
    {
      message: "User registered successfully.",
      access_token: token,
      token_type: "bearer",
      user: {
        id: userId,
        email: email,
        full_name: fullName,
        role: "STANDARD_USER",
        company_id: companyId,
      },
    },
    201
  );
});

authRouter.post("/login", async (c) => {
  const body = await c.req.json().catch(() => ({}));
  const email = (body.email || "").trim().toLowerCase();
  const password = body.password || "";

  if (!email || !password) {
    return c.json({ detail: "Email and password are required." }, 400);
  }

  // Query user from D1 database
  const user = await c.env.DB.prepare(
    "SELECT id, email, full_name, role, hashed_password, is_active, company_id FROM portal_users WHERE LOWER(email) = ? LIMIT 1"
  )
    .bind(email)
    .first<any>();

  if (!user) {
    return c.json({ detail: "Invalid email or password." }, 401);
  }

  if (!user.is_active) {
    return c.json({ detail: "Account has been suspended or deactivated. Contact Super Admin." }, 403);
  }

  const isMatch = await verifyPassword(password, user.hashed_password);
  if (!isMatch) {
    return c.json({ detail: "Invalid email or password." }, 401);
  }

  // Update last_login_at in D1
  const nowStr = new Date().toISOString();
  await c.env.DB.prepare("UPDATE portal_users SET last_login_at = ?, updated_at = ? WHERE id = ?")
    .bind(nowStr, nowStr, user.id)
    .run();

  // Create audit log entry
  const logId = crypto.randomUUID();
  await c.env.DB.prepare(
    "INSERT INTO portal_audit_logs (id, user_id, company_id, action, resource_type, resource_id, details, ip_address, timestamp) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)"
  )
    .bind(
      logId,
      user.id,
      user.company_id || null,
      "USER_LOGIN_SUCCESS",
      "PORTAL_USER",
      user.id,
      JSON.stringify({ client: "cloudflare-serverless", login_time: nowStr }),
      c.req.header("cf-connecting-ip") || "127.0.0.1",
      nowStr
    )
    .run()
    .catch(() => {}); // Gracefully log

  const secret = c.env.JWT_SECRET || "prospectos-cf-zero-cost-master-secret-2026";
  const token = await createAccessToken(
    {
      sub: user.id,
      email: user.email,
      role: user.role,
      company_id: user.company_id,
    },
    secret
  );

  return c.json({
    access_token: token,
    token_type: "bearer",
    user: {
      id: user.id,
      email: user.email,
      full_name: user.full_name,
      role: user.role,
      company_id: user.company_id,
    },
  });
});

authRouter.get("/me", authMiddleware, async (c) => {
  const payload = c.get("user");
  const user = await c.env.DB.prepare(
    "SELECT id, email, full_name, role, is_active, company_id, last_login_at, created_at FROM portal_users WHERE id = ?"
  )
    .bind(payload.sub)
    .first<any>();

  if (!user) {
    return c.json({ detail: "User not found." }, 404);
  }

  return c.json(user);
});

authRouter.post("/logout", authMiddleware, async (c) => {
  const authHeader = c.req.header("Authorization") || "";
  const token = authHeader.replace("Bearer ", "").trim();

  if (c.env.KV && token) {
    await c.env.KV.put(`revoked_token:${token.slice(-32)}`, "revoked", { expirationTtl: 86400 });
  }

  return c.json({ message: "Successfully logged out." });
});

