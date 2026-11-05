# PROSPECTOS — COMPLETE SERVERLESS ARCHITECTURE SPECIFICATION

**Target Platform**: Cloudflare Serverless SaaS  
**Authenticated Account**: `smagencywire@gmail.com` (`a22069ef8b16015f16b74b9afe65f557`)  
**Public Staging URL**: `https://prospectos-serverless.smagencywire.workers.dev`  
**Target Domain**: `prospectos.grokxseo.online`  
**Recurring Hosting Cost**: **$0.00 USD / Month**  

---

## 1. SYSTEM TOPOLOGY

```
                             [ Client Web Browser ]
                                       │
                                       ▼
                     [ Cloudflare Global Edge Network (Anycast) ]
                                       │
       ┌───────────────────────────────┴───────────────────────────────┐
       ▼                                                               ▼
[ Static Asset CDN ]                                         [ Serverless Worker API ]
• /                                                          • /portal/auth/*
• /login/                                                    • /admin/*
• /admin/                                                    • /api/scraper/*
• /portal/                                                   • /crm/*
• /_next/static/*                                            • /health
       │                                                               │
       └───────────────────────────────┬───────────────────────────────┘
                                       │
                                       ▼
                       [ Cloudflare Edge Platform ]
      ┌────────────────────────────────┼────────────────────────────────┐
      ▼                                ▼                                ▼
[ Cloudflare D1 ]               [ Cloudflare KV ]              [ AI Provider Engine ]
• 77 Relational Tables          • Session Revocation           • Anthropic Claude (Primary)
• 355 Historical Logs           • Edge Rate Limiting           • Google Gemini (Secondary)
• 3 Seeded User Accounts        • TTL Expiration               • Workers AI (Serverless)
```

---

## 2. COMPONENT ROLES

1. **Frontend**: Next.js 16.4.5 static HTML/CSS/JS export compiled into `frontend/out/` and served via Cloudflare Workers Static Assets binding (`ASSETS`).
2. **Backend API**: Cloudflare Worker built with Hono TypeScript framework in `cloudflare/src/`, providing 100% endpoint parity with legacy FastAPI.
3. **Database**: Cloudflare D1 SQLite database `prospectos-production-d1` (`62d68ef1-ed9d-47bf-b90a-8a26f2cfabe0`).
4. **Cache & Tokens**: Cloudflare KV `PROSPECTOS_KV` (`bb54a9e9dfdb4c1b979a9633c9256817`) for instant token revocation.
5. **AI Routing**: Multi-provider pipeline routing to Anthropic Claude (when spending budget is approved) and Google Gemini (free tier) with fallback to local heuristic intelligence.

