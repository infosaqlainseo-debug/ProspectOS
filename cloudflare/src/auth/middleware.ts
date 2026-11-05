/**
 * ProspectOS Cloudflare Serverless - Authentication & RBAC Middleware
 */

import { Context, Next } from "hono";
import { Env, UserPayload } from "../types/env";
import { verifyAccessToken } from "./jwt";

export async function authMiddleware(c: Context<{ Bindings: Env; Variables: { user: UserPayload } }>, next: Next) {
  const authHeader = c.req.header("Authorization");
  if (!authHeader || !authHeader.startsWith("Bearer ")) {
    return c.json({ detail: "Authentication credentials were not provided." }, 401);
  }

  const token = authHeader.substring(7).trim();
  const secret = c.env.JWT_SECRET || "prospectos-cf-zero-cost-master-secret-2026";
  const payload = await verifyAccessToken(token, secret);

  if (!payload) {
    return c.json({ detail: "Invalid or expired authentication token." }, 401);
  }

  // Check KV token revocation if KV binding exists
  if (c.env.KV) {
    const isRevoked = await c.env.KV.get(`revoked_token:${token.slice(-32)}`);
    if (isRevoked) {
      return c.json({ detail: "Session has been revoked. Please log in again." }, 401);
    }
  }

  c.set("user", payload);
  await next();
}

export function requireRole(allowedRoles: string[]) {
  return async (c: Context<{ Bindings: Env; Variables: { user: UserPayload } }>, next: Next) => {
    const user = c.get("user");
    if (!user) {
      return c.json({ detail: "Authentication credentials were not provided." }, 401);
    }

    if (!allowedRoles.includes(user.role)) {
      return c.json({
        detail: `Access denied. Required role in [${allowedRoles.map((r) => `'${r}'`).join(", ")}], your role is '${user.role}'.`,
      }, 403);
    }

    await next();
  };
}

