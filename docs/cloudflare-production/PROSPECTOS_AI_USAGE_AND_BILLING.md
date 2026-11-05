# PROSPECTOS — AI USAGE, QUOTA TRACKING & BILLING CONTROLS (PHASE 6)

**Target Platform**: Cloudflare Serverless SaaS  
**Target Monthly Operating Cost**: **$0.00 USD / Month**  
**Budget Enforcement**: **Strict Hard Stop at $0.00**  
**Primary AI Engine**: Google Gemini 3.8 Flash (`gemini-3.8-flash`)  

---

## 1. MONTHLY COST AUDIT & SEPARATE LINE-ITEM REPORTING

To provide complete accounting clarity, hosting infrastructure costs and AI inference costs are strictly separated:

### A. Hosting Infrastructure (Cloudflare Serverless)
| Component | Free Tier Allocation | Consumed / Month | Active Cost |
| :--- | :--- | :--- | :---: |
| **Cloudflare Workers** | 100,000 requests / day | ~5,000 requests | **$0.00** |
| **Cloudflare D1 Database** | 5,000,000 reads / month | ~25,000 reads | **$0.00** |
| **Cloudflare KV Namespace** | 100,000 reads / day | ~1,000 reads | **$0.00** |
| **Cloudflare R2 Object Storage** | 10 GB storage / month | ~50 MB exports | **$0.00** |
| **Workers Static Assets CDN** | Unlimited requests & bandwidth | ~35,000 assets | **$0.00** |
| **SUBTOTAL HOSTING COST** | — | — | **$0.00 USD** |

### B. AI Inference Infrastructure
| Provider & Model | Tier / Authorization Status | Free Allowance | Incurred Cost |
| :--- | :--- | :--- | :---: |
| **Google Gemini 3 Family (3.8 Flash / 3.1 Flash Lite)** | Google AI Studio Free Tier | 15 RPM / 1,500 RPD | **$0.00** |
| **Anthropic Claude 3.5** | **BUDGET-GATED ($0.00 Mode)** | Disabled until owner budget | **$0.00** |
| **Deterministic Heuristic Engine** | In-Worker V8 Offline Engine | Unlimited execution | **$0.00** |
| **SUBTOTAL AI INFERENCE COST** | — | — | **$0.00 USD** |

**GRAND TOTAL MONTHLY OPERATING COST: $0.00 USD / MONTH**

---

## 2. STRICT BUDGET GUARDRAILS

To eliminate any risk of unexpected cloud invoices or credit card charges:
1. **Google Gemini Free Tier Enforcement**: Google AI Studio provides a perpetual free tier for `gemini-3.8-flash` (15 RPM / 1,500 RPD). When the daily allowance is exhausted, the API returns `HTTP 429`. The ProspectOS router catches `429` and falls back to the deterministic heuristic engine without upgrading or billing.
2. **Anthropic Claude Budget-Gate**: Anthropic API has no perpetual free tier. Therefore, `ANTHROPIC_ENABLED` is hardcoded to fail-closed (`false`) in production. Live Anthropic API requests are strictly prevented until the platform owner configures an approved spending budget on Anthropic console and updates the worker configuration.
3. **No Card on File Requirement**: Cloudflare Workers, D1, KV, and Static Assets function indefinitely within free limits without requiring payment details.

---

## 3. AUDIT & TELEMETRY TRACKING IN D1

AI inference telemetry is logged in Cloudflare D1:

```sql
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
- `provider`: `gemini` | `anthropic` | `heuristic_intelligence_engine`.
- `model`: `gemini-3.8-flash` | `claude-3-5-haiku-20241022` | `prospectos-deterministic-heuristic-v3`.
- `is_ai_generated`: Boolean flag (explicitly `false` for heuristics).
- `cost_usd`: Fixed at `0.0000` for Gemini free tier and heuristic engine.
