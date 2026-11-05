# PROSPECTOS — GITHUB CONFIGURATION & CI/CD PIPELINE

**Branch**: `cloudflare-anthropic-gemini-migration`  
**Repository**: `https://github.com/infosaqlainseo-debug/ProspectOS.git`  
**CI/CD Engine**: GitHub Actions (Free Allowance - 2,000 minutes/month)  

---

## 1. BRANCH STRATEGY

1. `main`: Production deployment branch.
2. `development`: Pre-release integration branch.
3. `cloudflare-anthropic-gemini-migration`: Active Cloudflare serverless migration branch.

---

## 2. GITHUB ACTIONS AUTOMATION (`.github/workflows/ci.yml`)

The repository includes automated CI running on `ubuntu-latest`:
- **Node.js Environment**: Sets up Node 20 with `npm` caching.
- **Frontend Validation**: Runs TypeScript check (`npx tsc --noEmit`) and ESLint.
- **Backend Validation**: Runs pytest test suite across 123 tests.
- **Zero-Cost Safeguard**: Validates that no paid Cloudflare or AI dependencies are introduced.
- **Execution Time**: ~1.5 minutes per run, consuming less than 100 minutes of GitHub's free 2,000 monthly allowance.

---

## 3. SECURITY & CREDENTIAL HYGIENE

- All `.env`, `*.dump`, `*.d1`, and `.wrangler` credentials are systematically excluded via `.gitignore`.
- Secrets must be injected exclusively via Cloudflare Worker Secrets (`wrangler secret put`).
