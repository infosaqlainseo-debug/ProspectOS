# PROSPECTOS — CLOUDFLARE FREE TIER RESOURCE LIMITS & MONITORING

**Target Platform**: Cloudflare Serverless SaaS  
**Target Monthly Operating Cost**: **$0.00 USD / Month**  
**Account**: `smagencywire@gmail.com` (`a22069ef8b16015f16b74b9afe65f557`)  

---

## 1. CLOUDFLARE FREE TIER SPECIFICATIONS

| Service | Cloudflare Free Tier Allocation | Reset Frequency | Over-Quota Behavior |
| :--- | :--- | :--- | :--- |
| **Cloudflare Workers** | 100,000 requests / day | Daily (Midnight UTC) | Returns HTTP 1015 / 1027 Rate Limit (No billing charge) |
| **Worker CPU Time** | 10ms CPU time / request | Per Request | Cancels execution if exceeded (No billing charge) |
| **Cloudflare D1 (Database)** | 5,000,000 reads / month<br>100,000 writes / day<br>500 MB total storage | Monthly (Reads)<br>Daily (Writes) | Read-only mode / rejection (No billing charge) |
| **Cloudflare KV (Cache)** | 100,000 reads / day<br>1,000 writes / day<br>1 GB storage | Daily | Throttles KV operations (No billing charge) |
| **Cloudflare R2 (Objects)** | 10 GB storage / month<br>1M Class A ops / month<br>10M Class B ops / month | Monthly | Storage caps (No billing charge) |
| **Workers Static Assets** | Unlimited requests & bandwidth<br>Up to 20,000 files / deployment | Per Deploy | Build-time validation (No billing charge) |
| **Cloudflare DNS & SSL** | Unlimited queries & free Edge SSL | Perpetual | Included free (No billing charge) |

---

## 2. GOOGLE GEMINI FREE TIER ALLOCATION

| Metric | Free Tier Allocation | Safety Mechanism |
| :--- | :--- | :--- |
| **Requests Per Minute (RPM)** | 15 RPM | Automatic retry with backoff |
| **Requests Per Day (RPD)** | 1,500 RPD | Catch HTTP 429 and fallback to offline heuristic engine |
| **Tokens Per Minute (TPM)** | 1,000,000 TPM | In-flight payload truncation |
| **Cost** | **$0.00 USD** | No automatic card billing in AI Studio free tier |

---

## 3. CAPACITY & HEADROOM FOR PROSPECTOS

### Scraper Throughput
- Scraper execution on Cloudflare Workers requires ~0.10s wall-clock time and ~2.5ms edge CPU time (well within the 10ms limit).
- 100,000 requests/day allows **up to 50,000 scrape page fetches + 50,000 dashboard/API interactions every single day**.

### Database Operations (D1)
- Standard ProspectOS usage generates ~10 D1 reads and ~2 D1 writes per user interaction.
- 5,000,000 reads/month supports **500,000 user page views or automated actions per month**.
- 100,000 writes/day supports **up to 50,000 new leads discovered, updated, or status-changed daily**.

### Database Storage Capacity
- The D1 schema uses SQLite with compact types.
- 500 MB storage holds approximately **250,000 fully enriched prospect records and CRM leads** before approaching storage limits.

---

## 4. MONITORING & EARLY WARNING STRATEGY

1. **Cloudflare Dashboard Telemetry**:
   - `Workers & Pages > Overview`: Real-time request volume graphs and CPU percentile metrics.
   - `D1 > prospectos-production-d1 > Metrics`: Daily read/write operations and storage size.
2. **Built-in Health Check**:
   - `GET /health`: Checks edge CPU health and active architecture.
   - `GET /health/database`: Verifies D1 query latency and connection status.
3. **KV Revocation Cleanup**:
   - Every revoked token in KV has an explicit TTL equal to JWT expiration (`expirationTtl: 86400`), automatically reclaiming KV key space after 24 hours.
