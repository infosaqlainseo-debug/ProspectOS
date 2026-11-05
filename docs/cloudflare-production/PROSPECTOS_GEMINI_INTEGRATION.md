# PROSPECTOS — GOOGLE GEMINI 3.8 FLASH INTEGRATION SPECIFICATION

**Target Platform**: Cloudflare Serverless SaaS  
**Primary AI Inference Engine**: **Google Gemini 3.8 Flash** (`gemini-3.8-flash`)  
**Operating Allowance**: **Google AI Studio Free Tier (15 RPM / 1,500 RPD at $0.00)**  
**Version**: 3.0 (Gemini 3 Architecture Upgrade)  

---

## 1. MODEL UPGRADE & ARCHITECTURAL OVERVIEW

Following Google's deprecation and shutdown of legacy Gemini 1.5 endpoints, ProspectOS has upgraded its primary AI inference provider to the current flagship model: **Gemini 3.8 Flash** (`gemini-3.8-flash`).

### Core Responsibilities in ProspectOS:
1. **Automated SEO Audit Summaries**: Analyzing raw crawler metrics (HTTP status codes, title tags, schema.org markup, responsive meta tags, backlink indicators) into client-facing executive summaries.
2. **ICP Lead Qualification & Scoring**: Evaluating prospective business domains against target ideal customer profiles (1-100 numerical score with rationale).
3. **Conversational Intelligence Assistant**: Answering prospect analysis queries in the `/crm/pipeline` and `/portal` interfaces.

---

## 2. GOOGLE AI STUDIO FREE-TIER SPECIFICATIONS

ProspectOS operates strictly within Google AI Studio's perpetual free allowances:

| Metric | Free Tier Allocation | System Enforcement |
| :--- | :--- | :--- |
| **Model Target** | `gemini-3.8-flash` | Hardcoded in `UnifiedAIProvider` |
| **Requests Per Minute (RPM)** | 15 RPM | Edge rate-limiter prevents burst overages |
| **Requests Per Day (RPD)** | 1,500 Requests / Day | Daily counter in Cloudflare D1 |
| **Tokens Per Minute (TPM)** | 1,000,000 TPM | Request truncation guardrails |
| **Monthly Cost** | **$0.00 USD** | No automatic card billing in AI Studio free tier |
| **Over-Quota Behavior** | HTTP 429 Rate Limit | Immediate failover to deterministic rule engine |

> [!IMPORTANT]
> The Gemini API Free tier does NOT automatically convert to paid billing. When the 1,500 RPD cap is reached, the API returns HTTP 429. ProspectOS catches HTTP 429 and cascades to the deterministic offline rule engine without downtime or unexpected cloud bills.

---

## 3. GEMINI 3 REST API SPECIFICATION

Implemented in `cloudflare/src/services/ai-provider.ts`:

### Endpoint
```http
POST https://generativelanguage.googleapis.com/v1beta/models/gemini-3.8-flash:generateContent
```

### Request Headers
```http
Content-Type: application/json
x-goog-api-key: [CLOUDFLARE_WORKER_SECRET]
```

### Request Body Schema (Gemini 3 Specification)
```json
{
  "contents": [
    {
      "role": "user",
      "parts": [{ "text": "Analyze the SEO visibility of Acme Corp..." }]
    }
  ],
  "systemInstruction": {
    "parts": [{ "text": "You are ProspectOS AI, an expert agentic SEO analyst..." }]
  },
  "generationConfig": {
    "temperature": 0.4,
    "maxOutputTokens": 2048,
    "responseMimeType": "application/json"
  }
}
```

---

## 4. SECURE SECRET PROVISIONING PROTOCOL

To maintain zero-leakage security, the Google Gemini API key must **never** be committed to GitHub, embedded in source code, or shared in conversation transcripts.

### Provisioning Instructions for Platform Owner:
1. Generate a free API key at **Google AI Studio**: [https://aistudio.google.com/app/apikey](https://aistudio.google.com/app/apikey).
2. In your local terminal, run the Cloudflare secret configuration command:
   ```bash
   npx wrangler secret put GEMINI_API_KEY --config cloudflare/wrangler.jsonc
   ```
3. When prompted: `Enter a secret value:`, paste the API key securely.
4. Cloudflare encrypts the secret and injects `env.GEMINI_API_KEY` directly into the V8 edge worker runtime.

### Secret Verification (Non-Leaking):
```bash
# Verify that GEMINI_API_KEY exists in Cloudflare secret store without printing its value
npx wrangler secret list --config cloudflare/wrangler.jsonc
```

---

## 5. TRANSPARENT AI ROUTER HIERARCHY

To ensure complete regulatory and client transparency, ProspectOS enforces strict attribution:

```
                      [ Incoming User Query ]
                                 │
                                 ▼
                 [ 1. Google Gemini 3.8 Flash ]
                 ├── GEMINI_API_KEY present?
                 │     ├── Yes ──► Call API (Free Tier)
                 │     │             ├── HTTP 200: Return with is_ai_generated: true
                 │     │             └── HTTP 429: Fallback (Quota Exceeded)
                 │     └── No ──► Fallback (Key Pending)
                 │
                 ▼
                 [ 2. Anthropic Claude 3.5 ]
                 ├── ANTHROPIC_ENABLED == "true"?
                 │     ├── Yes (Owner Approved Budget) ──► Call Claude API
                 │     └── No (Default Zero-Cost Mode) ──► Fallback (Budget-Gated)
                 │
                 ▼
                 [ 3. Deterministic Heuristic Engine ]
                 └── Return Rule-Based JSON
                     • is_ai_generated: false
                     • provider: "heuristic_intelligence_engine"
                     • model: "prospectos-deterministic-heuristic-v3"
                     • cost: $0.00
```

> [!CAUTION]
> The platform strictly prohibits representing heuristic engine output as Gemini or Claude. Every response payload explicitly specifies `is_ai_generated` and `status_note`.
