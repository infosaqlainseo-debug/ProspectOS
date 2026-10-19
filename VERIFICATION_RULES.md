# ProspectOS Verification & Non-Hallucination Rules

## Core Verification Rules

**V001:** Never fabricate factual data.
**V002:** Unknown values remain unknown. (If unavailable, set `value = null`, and `status = "UNVERIFIED"` or `"NOT_AVAILABLE"`. The AI must never guess).
**V003:** Every external metric requires a source/provider.
**V004:** Every social profile requires evidence. The system must NOT generate social URLs simply from a company name.
**V005:** Historical data must not be silently overwritten. Use snapshots for changing metrics.
**V006:** Canonical domains must be normalized before deduplication.
**V007:** LLM inference must be explicitly labeled as inference.
**V008:** LLM output must be schema validated.
**V009:** A failed provider must not destroy the entire job.
**V010:** Every crawl must have a timestamp.
**V011:** Every important external fact must have provenance (`source_url`, `source_type`, `provider`, `retrieved_at`, etc.).
**V012:** Production data must never be replaced by test/mock data.
**V013:** Different SEO providers must never be presented as if their metrics are identical. (Moz DA != Ahrefs DR; they must remain separately labeled).
**V014:** A company being newly discovered does not automatically mean that the company itself is newly founded.
**V015:** The system must distinguish: newly discovered from newly created.
**V016:** A low traffic estimate or low authority metric alone must not be treated as absolute proof that a company needs SEO services. Use multi-signal confidence logic.
**V017:** Opportunity scoring must be transparent, explainable, and retain the methodology version and timestamp calculation.

## LLM Safety Architecture

**IMPORTANT:** Do not treat the LLM as a database.

### The Correct Pipeline:
`RAW SOURCE` &rarr; `EXTRACTION` &rarr; `STRUCTURED OUTPUT` &rarr; `SCHEMA VALIDATION` &rarr; `EVIDENCE VALIDATION` &rarr; `DATABASE` &rarr; `INTELLIGENCE`

### Extraction Guidelines
The LLM may extract structured information from raw HTML/text, however, LLM-generated factual fields must not automatically become trusted facts.

**Prefer Deterministic Extraction for:**
- URLs
- Links
- HTTP status
- HTML metadata (title, description)
- Canonical tags
- Social links
- robots.txt
- sitemap
- Structured data

**Use LLM Reasoning Primarily for:**
- Classification
- Categorization
- Summarization
- Semantic interpretation
- Industry classification
- Opportunity analysis
