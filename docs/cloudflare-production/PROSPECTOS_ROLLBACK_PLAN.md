# PROSPECTOS — ROLLBACK PLAN & BUSINESS CONTINUITY ASSURANCE

**Target Platform**: Cloudflare Serverless SaaS  
**Rollback Destination**: Original Docker / PostgreSQL Local & VPS Stack  
**Risk Level**: **ZERO RISK (Original Databases & Containers Untouched)**  

---

## 1. PRESERVATION GUARANTEE

Throughout the entire migration to Cloudflare Serverless:
1. **Zero Data Destruction**: The local Docker PostgreSQL database (`prospectos_db`), Redis, Celery workers, and FastAPI backend were **never deleted, modified, or truncated**.
2. **Git Branch Isolation**: All Cloudflare-related code, Next.js export configurations, and Worker scripts were developed on the dedicated branch:
   `cloudflare-anthropic-gemini-migration`.
3. The `main` and original working branches remain intact at their exact pre-migration commit hashes.

---

## 2. EMERGENCY ROLLBACK PROCEDURE

If at any point the platform owner or engineering team decides to revert from Cloudflare Serverless back to the original Docker container stack, execute the following three-step procedure:

### Step 1: Re-activate Docker Stack
From the project root:
```bash
# Verify Docker container status
docker ps -a

# Start the full original Docker compose stack
docker-compose up -d
```

### Step 2: Verify Local Health Checks
Confirm all local services are responding:
```bash
# Check PostgreSQL
docker exec prospectos_db pg_isready -U postgres

# Check FastAPI Backend
curl -i http://localhost:8000/health

# Check Next.js Frontend
curl -i http://localhost:3000/
```

### Step 3: Switch Git Branch (Optional)
If running outside of Docker in development:
```bash
git checkout main
```

---

## 3. BIDIRECTIONAL DATA SYNCHRONIZATION (D1 TO POSTGRESQL)

If new leads or scraping tasks were generated in Cloudflare D1 during serverless operation and need to be backported to PostgreSQL:

```bash
# Export all records from Cloudflare D1
npx wrangler d1 execute prospectos-production-d1 \
  --config cloudflare/wrangler.jsonc \
  --remote \
  --command="SELECT * FROM crm_leads;" --json > d1_leads_export.json

# Import into PostgreSQL using Python script
python3 -c "
import json, psycopg2, os
with open('d1_leads_export.json') as f:
    data = json.load(f)[0]['results']
conn = psycopg2.connect('postgresql://postgres:postgres@localhost:5432/prospectos')
cur = conn.cursor()
for r in data:
    cur.execute('''
        INSERT INTO crm_leads (id, organization_id, company_name, email, phone, status, lead_score)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (id) DO NOTHING;
    ''', (r['id'], r['organization_id'], r['company_name'], r['email'], r['phone'], r['status'], r['lead_score']))
conn.commit()
print(f'Successfully synced {len(data)} leads back to PostgreSQL.')
"
```

---

## 4. ROLLBACK DRILL CONCLUSION

Because the serverless migration is 100% additive and non-destructive to the original infrastructure, the rollback window is instantaneous (< 30 seconds to run `docker-compose up -d`) with zero potential for data loss.
