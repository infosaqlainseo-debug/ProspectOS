# PROSPECTOS — CLOUDFLARE & AI FREE TIER RESOURCE LIMITS & MONITORING

**Target Platform**: Cloudflare Serverless SaaS  
**Target Monthly Operating Cost**: **$0.00 USD / Month**  
**Account**: `smagencywire@gmail.com` (`a22069ef8b16015f16b74b9afe65f557`)  

---

## 1. CLOUDFLARE FREE TIER SPECIFICATIONS (OFFICIAL & VERIFIED)

| Service | Cloudflare Free Tier Allocation | Reset Frequency | Over-Quota Behavior |
| :--- | :--- | :--- | :--- |
| **Cloudflare Workers** | **100,000 requests / day** | Daily (Midnight UTC) | Returns HTTP 1015 / 1027 Rate Limit (No billing charge) |
| **Worker CPU Time** | 10ms CPU time / request | Per Request | Cancels execution if exceeded (No billing charge) |
| **Cloudflare D1 (Database)** | **5,000,000 rows read / day**<br>**100,000 rows written / day**<br>**5 GB total free storage** | Daily (Reads & Writes)<br>Perpetual (Storage) | Read-only mode / rejection (No billing charge) |
| **Cloudflare KV (Cache & Session)** | **100,000 reads / day**<br>**1,000 writes / day**<br>**1 GB storage** | Daily (Operations)<br>Perpetual (Storage) | Throttles KV operations (No billing charge) |
| **Cloudflare R2 (Object Storage)** | **10 GB-month storage**<br>**1,000,000 Class A ops / month**<br>**10,000,000 Class B ops / month** | Monthly | Storage & operation caps (No billing charge) |
| **Workers Static Assets** | Unlimited requests & bandwidth<br>Up to 20,000 files / deployment | Per Deploy | Build-time validation (No billing charge) |
| **Cloudflare DNS & SSL** | Unlimited queries & free Edge SSL | Perpetual | Included free (No billing charge) |

> [!IMPORTANT]
> **Strict Resource Separation**: Cloudflare KV (key-value edge cache) and Cloudflare R2 (S3-compatible object storage) are distinct services with separate usage meters and billing boundaries. ProspectOS maintains independent meters for KV read/writes vs. R2 Class A/B operations.

---

## 2. GOOGLE GEMINI FREE TIER SPECIFICATIONS

| Metric | Free Tier Allocation | System Enforcement & Guardrail |
| :--- | :--- | :--- |
| **Primary Model** | `gemini-3.8-flash` | Flagship speed tier; `thinkingLevel: "low"` prevents timeout |
| **Secondary Model** | `gemini-3.5-flash-lite` | Actively maintained fallback; no scheduled retirement |
| **Requests Per Minute (RPM)** | 15 RPM | Automatic backoff at edge router |
| **Requests Per Day (RPD)** | 1,500 RPD | Daily D1 quota counter; failover to offline heuristic engine |
| **Tokens Per Minute (TPM)** | 1,000,000 TPM | Request truncation guardrails |
| **Monthly Cost** | **$0.00 USD** | Google AI Studio free tier has no automatic card billing |

---

## 3. CAPACITY & HEADROOM FOR PROSPECTOS

### Scraper & Workers Throughput
- Scraper execution on Cloudflare Workers requires ~0.10s wall-clock time and ~2.5ms edge CPU time (well within the 10ms limit).
- 100,000 requests/day allows **up to 50,000 scrape page fetches + 50,000 dashboard/API interactions every single day**.

### Database Operations (Cloudflare D1)
- Standard ProspectOS usage generates ~10 D1 rows read and ~2 D1 rows written per user interaction.
- **5,000,000 rows read / day** supports **500,000 daily user page views or automated audit queries**.
- **100,000 rows written / day** supports **up to 50,000 new prospect records created, enriched, or updated daily**.

### Database Storage Capacity (5 GB)
- The D1 schema uses SQLite with compact binary types.
- 5 GB storage holds approximately **2,500,000 fully enriched prospect records and CRM leads** before approaching capacity.

### Edge Caching (Cloudflare KV)
- 100,000 reads/day and 1,000 writes/day with 1 GB storage.
- Used strictly for high-speed JWT revocation tokens and scraper rate limit counters.
- Automatic TTL (`expirationTtl: 86400`) cleanses expired records after 24 hours.

### Export & Document Storage (Cloudflare R2)
- 10 GB storage, 1M Class A ops (writes/lists), 10M Class B ops (reads).
- Dedicated to CSV prospect exports, audit PDF attachments, and raw scraper dumps with zero egress fees.

---

## 4. MONITORING & EARLY WARNING STRATEGY

1. **Cloudflare Dashboard Telemetry**:
   - `Workers & Pages > Overview`: Real-time request volume graphs and CPU percentile metrics.
   - `D1 > prospectos-production-d1 > Metrics`: Daily row reads, row writes, and database size.
   - `KV > Namespaces > prospectos-kv`: Daily read/write operations and active keys.
   - `R2 > Overview`: Total stored bytes, Class A operations, and Class B operations.
2. **Built-in Platform Health Checks**:
   - `GET /health`: Checks edge CPU health and active architecture.
   - `GET /health/database`: Verifies D1 query latency and connection status.
3. **KV Revocation Cleanup**:
   - Every revoked token in KV has an explicit TTL equal to JWT expiration (`expirationTtl: 86400`), automatically reclaiming KV key space after 24 hours.

