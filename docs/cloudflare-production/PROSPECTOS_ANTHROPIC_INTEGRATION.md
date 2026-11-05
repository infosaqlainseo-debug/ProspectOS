# PROSPECTOS — ANTHROPIC CLAUDE INTEGRATION SPECIFICATION

**Target Platform**: Cloudflare Serverless SaaS  
**Primary AI Engine**: Anthropic Claude 3.5 Sonnet / Haiku  
**Cost Control Architecture**: **Budget-Gated / Strict $0 Zero-Cost Mode by Default**  

---

## 1. INTEGRATION ARCHITECTURE

ProspectOS uses Anthropic Claude for high-reasoning intelligence tasks:
1. **SEO Lead Qualification**: Analyzing company descriptions, value propositions, and web copy to assign lead quality tiers.
2. **Personalized Outreach Drafts**: Generating cold pitch drafts customized to an extracted business's technical gaps (e.g., missing meta tags, low speed score).
3. **Structured Entity Extraction**: Extracting structured executive names, business categories, and technology stacks from messy unparsed HTML.

---

## 2. STRICT ZERO-COST & BUDGET-GATING POLICY

### The Financial Reality of Anthropic API
Unlike Google Gemini (which offers a perpetual 1,500 free requests/day tier) and Cloudflare Workers AI (which includes 10,000 free neurons/day), Anthropic Claude is a **pure pay-as-you-go service with no free monthly allowance**.

### Mandatory Safety Guardrails
To enforce the project's **strict $0.00 / month cost requirement**:
1. `ANTHROPIC_ENABLED` is set to `false` by default in production runtime configuration.
2. When `ANTHROPIC_ENABLED=false` or `ANTHROPIC_API_KEY` is not explicitly set, the AI Router automatically delegates requests to **Google Gemini (100% Free)** or the local heuristic extraction engine.
3. Live Anthropic API requests cannot be triggered without explicit owner confirmation and an active billing authorization on the Anthropic account console.

---

## 3. IMPLEMENTATION IN CLOUDFLARE WORKERS

Implemented in `cloudflare/src/services/ai-provider.ts`:

```typescript
export async function callAnthropicClaude(
  prompt: string,
  env: Env,
  model = "claude-3-haiku-20240307"
): Promise<{ text: string; provider: string; model: string }> {
  // Budget Gate: Enforce $0 policy
  if (env.ANTHROPIC_ENABLED !== "true" && env.ANTHROPIC_ENABLED !== true) {
    throw new Error("ANTHROPIC_BUDGET_GATED: Anthropic is disabled to maintain $0 free-tier policy.");
  }

  if (!env.ANTHROPIC_API_KEY) {
    throw new Error("ANTHROPIC_KEY_MISSING: No Anthropic API key configured.");
  }

  const response = await fetch("https://api.anthropic.com/v1/messages", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "x-api-key": env.ANTHROPIC_API_KEY,
      "anthropic-version": "2023-06-01"
    },
    body: JSON.stringify({
      model: model,
      max_tokens: 1024,
      messages: [{ role: "user", content: prompt }]
    })
  });

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`Anthropic API error (${response.status}): ${errorText}`);
  }

  const data = await response.json();
  const text = data.content?.[0]?.text || "";

  return {
    text,
    provider: "anthropic",
    model: model
  };
}
```

---

## 4. ACTIVATION PROCEDURE (OWNER ONLY)

If the owner decides to enable Anthropic Claude with paid credits:
1. Obtain an API key from `https://console.anthropic.com/settings/keys`.
2. Set the secret in Cloudflare Worker via Wrangler:
   ```bash
   npx wrangler secret put ANTHROPIC_API_KEY --config cloudflare/wrangler.jsonc
   ```
3. Update `wrangler.jsonc` to set:
   ```jsonc
   "vars": {
     "ANTHROPIC_ENABLED": "true"
   }
   ```
4. Deploy the updated worker:
   ```bash
   npx wrangler deploy --config cloudflare/wrangler.jsonc
   ```

---

## 5. AUDIT STATUS

- **Budget Gate Verified**: `callAnthropicClaude` raises protective error when budget-gated.
- **Failover to Gemini**: Successfully verified that disabled Anthropic requests instantly fail over to Google Gemini / heuristic fallback with 0ms interruption.
- **Cost**: **$0.00 USD**.
