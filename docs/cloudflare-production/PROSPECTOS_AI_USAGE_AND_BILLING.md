# PROSPECTOS — AI USAGE, QUOTA TRACKING & BILLING CONTROLS

**Target Platform**: Cloudflare Serverless SaaS  
**Target Monthly Operating Cost**: **$0.00 USD / Month**  
**Budget Enforcement**: **Strict Hard Stop at $0.00**  

---

## 1. MONTHLY COST COMPARISON: LEGACY VS SERVERLESS

| Component | Legacy Docker / VPS Architecture | Cloudflare Serverless Architecture |
| :--- | :--- | :--- |
| **Compute & API Runtime** | DigitalOcean / AWS VPS ($24 - $48/mo) | Cloudflare Workers Free Tier ($0.00/mo) |
| **Frontend Static Hosting** | Dedicated Nginx / Node VPS ($12/mo) | Cloudflare Workers Assets / Pages ($0.00/mo) |
| **Relational Database** | Managed PostgreSQL ($15 - $35/mo) | Cloudflare D1 Serverless SQLite ($0.00/mo) |
| **Cache & Task Queue** | Redis Cloud / ElastiCache ($10 - $25/mo) | Cloudflare KV Free Tier ($0.00/mo) |
| **Object & Export Storage** | AWS S3 + Egress fees ($5 - $15/mo) | Cloudflare R2 Free Tier + $0 Egress ($0.00/mo) |
| **AI Inference** | Uncapped OpenAI / Anthropic ($20 - $100/mo) | Google Gemini Free + Heuristics ($0.00/mo) |
| **TOTAL ESTIMATED COST** | **$86.00 – $235.00 / month** | **$0.00 / month (100% Free)** |

---

## 2. STRICT BUDGET GUARDRAILS

To eliminate any chance of surprise cloud bills or accidental credit card charges:
1. **No Payment Method Required**: Cloudflare Workers, D1, KV, and Workers Static Assets operate perpetually on the free plan without requiring a credit card on file.
2. **Anthropic Hard Stop**: The Anthropic provider is disabled (`ANTHROPIC_ENABLED=false`) until the platform owner explicitly overrides it in writing.
3. **Gemini Hard Limit**: Google Gemini free-tier requests return `HTTP 429 Too Many Requests` when the 1,500 requests/day limit is reached; the API does NOT automatically bill or upgrade. The ProspectOS AI router catches `429` errors and falls back to offline heuristic processing.
4. **Cloudflare Worker Daily Cap**: The free tier provides 100,000 requests/day. If exceeded, Cloudflare returns standard rate-limit error pages without billing overage fees.

---

## 3. USAGE & TELEMETRY TRACKING IN D1

AI inference requests and scraper runs are metered per organization in Cloudflare D1:

```sql
-- Query to audit AI usage by organization
SELECT 
  organization_id,
  provider,
  model,
  COUNT(*) as total_requests,
  SUM(estimated_tokens) as total_tokens,
  ROUND(SUM(estimated_cost_usd), 4) as total_cost_usd
FROM ai_usage_audit_logs
GROUP BY organization_id, provider, model;
```

### Telemetry Fields Recorded:
- `timestamp`: UTC ISO 8601 timestamp.
- `organization_id`: Multi-tenant organization UUID.
- `user_id`: Requesting user UUID.
- `provider`: `gemini` | `anthropic` | `heuristic`.
- `model`: Model identifier (e.g., `gemini-1.5-flash`, `claude-3-haiku-20240307`).
- `prompt_tokens` & `completion_tokens`: Approximate token count.
- `cost_usd`: Fixed at `0.0000` for Gemini free tier and heuristic engine.

---

## 4. RECOMMENDATIONS FOR ENTERPRISE SCALING

If the platform experiences hypergrowth beyond free-tier capacity:
1. **Cloudflare Workers Paid Plan**: $5/month for 10 million requests (if exceeding 100k requests/day).
2. **Gemini Pay-As-You-Go**: $0.075 per 1 million input tokens on Gemini 1.5 Flash (extremely economical).
3. **Anthropic Pay-As-You-Go**: Activate Claude 3.5 Haiku ($0.25 / 1M tokens) for premium agency clients who pay subscription fees.

