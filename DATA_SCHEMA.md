# ProspectOS Data Schema Dictionary

## Source of Truth Hierarchy
1. Authorized API/provider data
2. Official company website
3. Reliable public source
4. Secondary public source
5. LLM inference (Explicitly labeled as inference, never overrides stronger evidence)

## Evidence-First Data Model
Every important externally sourced fact must be traceable. Expected evidence fields: `value`, `source_url`, `source_type`, `provider`, `retrieved_at`, `extraction_method`, `confidence`, `verification_status`.

---

## Entities

### Company
- `id` (UUID, non-nullable)
- `company_name` (String, nullable)
- `legal_name` (String, nullable)
- `website_url` (String, nullable)
- `canonical_domain` (String, nullable, normalized)
- `country` (String, nullable)
- `state` (String, nullable)
- `city` (String, nullable)
- `industry` (String, nullable)
- `sub_industry` (String, nullable)
- `description` (Text, nullable)
- `company_status` (String, nullable)
- `first_discovered_at` (Timestamp, non-nullable)
- `last_seen_at` (Timestamp, nullable)
- `last_verified_at` (Timestamp, nullable)
- `created_at` (Timestamp, non-nullable)
- `updated_at` (Timestamp, non-nullable)

### Domain
- `id` (UUID, non-nullable)
- `company_id` (UUID, non-nullable)
- `domain` (String, non-nullable)
- `canonical_domain` (String, non-nullable)
- `registrar` (String, nullable)
- `domain_created_at` (Timestamp, nullable)
- `domain_expiry_at` (Timestamp, nullable)
- `first_seen_at` (Timestamp, nullable)
- `last_checked_at` (Timestamp, nullable)
- `status` (String, non-nullable) (UNVERIFIED if unknown)

### Discovery
- `id` (UUID, non-nullable)
- `company_id` (UUID, non-nullable)
- `source_id` (UUID, nullable)
- `source_url` (String, nullable)
- `discovery_method` (String, non-nullable)
- `discovered_at` (Timestamp, non-nullable)
- `query` (String, nullable)
- `job_id` (UUID, nullable)
- `confidence` (Float, nullable)

### SEOMetric
- `metric_id` (UUID, non-nullable)
- `company_id` (UUID, non-nullable)
- `metric_name` (String, non-nullable) (e.g., DA, DR, organic_traffic)
- `metric_value` (Float/Integer, nullable)
- `unit` (String, nullable)
- `provider` (String, non-nullable) (e.g., Moz, Ahrefs)
- `source_url` (String, nullable)
- `retrieved_at` (Timestamp, non-nullable)
- `confidence` (Float, nullable)
- `verification_status` (String, non-nullable)
- `raw_reference` (JSON, nullable)

### SocialProfile
- `id` (UUID, non-nullable)
- `company_id` (UUID, non-nullable)
- `platform` (String, non-nullable) (LinkedIn, Facebook, Instagram, X, YouTube, TikTok)
- `profile_url` (String, non-nullable)
- `source_url` (String, nullable)
- `verification_method` (String, non-nullable)
- `confidence` (Float, nullable)
- `verification_status` (String, non-nullable)
- `discovered_at` (Timestamp, non-nullable)
- `last_verified_at` (Timestamp, nullable)

### WebsiteScan
- `id` (UUID, non-nullable)
- `company_id` (UUID, non-nullable)
- `url` (String, non-nullable)
- `http_status` (Integer, nullable)
- `https_enabled` (Boolean, nullable)
- `final_url` (String, nullable)
- `redirect_chain` (JSON, nullable)
- `title` (String, nullable)
- `meta_description` (Text, nullable)
- `canonical_url` (String, nullable)
- `robots_txt_status` (String, nullable)
- `sitemap_status` (String, nullable)
- `schema_detected` (JSON, nullable)
- `cms_detected` (String, nullable)
- `technology_signals` (JSON, nullable)
- `scanned_at` (Timestamp, non-nullable)
- `scan_status` (String, non-nullable)

### RiskAssessment
- `id` (UUID, non-nullable)
- `company_id` (UUID, non-nullable)
- `risk_score` (Float, nullable)
- `risk_level` (String, non-nullable) (LOW, MEDIUM, HIGH, UNKNOWN)
- `risk_signals` (JSON, nullable)
- `confidence` (Float, nullable)
- `methodology_version` (String, non-nullable)
- `assessed_at` (Timestamp, non-nullable)

### HealthAssessment
- `id` (UUID, non-nullable)
- `company_id` (UUID, non-nullable)
- `health_score` (Float, nullable)
- `health_status` (String, non-nullable) (EXCELLENT, GOOD, NEEDS_ATTENTION, POOR, UNKNOWN)
- `health_signals` (JSON, nullable)
- `methodology_version` (String, non-nullable)
- `assessed_at` (Timestamp, non-nullable)

### HistoricalSnapshot
- Records point-in-time snapshots of critical metrics to ensure historical observations are never silently destroyed.

### OpportunityProfile
- `id` (UUID, non-nullable)
- `company_id` (UUID, non-nullable)
- `recommended_service` (String, non-nullable)
- `opportunity_score` (Float, non-nullable)
- `supporting_evidence` (JSON, nullable)
- `identified_problems` (JSON, nullable)
- `confidence_level` (Float, non-nullable)
- `data_freshness` (String, non-nullable)
- `missing_information` (JSON, nullable)
- `recommended_next_action` (String, nullable)
- `methodology_version` (String, non-nullable)
- `calculation_timestamp` (Timestamp, non-nullable)
- `created_at` (Timestamp, non-nullable)

### System & Audit Entities
- `Source`
- `Evidence`
- `Job`
- `JobResult`
- `AgentRun`
- `Error`

### Phase 2.0 & 2.1 Media Planning Entities

#### PublisherRecord
- `id` (UUID, non-nullable)
- `company_id` (UUID, non-nullable) - Links to Company table for identity
- `source_url` (String, nullable)
- `content_languages` (JSON, nullable)
- `audience_focus` (String, nullable)
- `editorial_policy_url` (String, nullable)
- `publisher_quality_score` (Float, nullable)
- `content_guidelines` (JSON, nullable)
- `created_at` (Timestamp, non-nullable)
- `updated_at` (Timestamp, non-nullable)

#### PublisherObservation
- `id` (UUID, non-nullable)
- `publisher_id` (UUID, non-nullable)
- `observed_at` (Timestamp, non-nullable)
- `price` (Float, nullable)
- `currency` (String, nullable)
- `metric_da` (Float, nullable)
- `metric_dr` (Float, nullable)
- `metric_organic_traffic` (Float, nullable)
- `metric_referring_domains` (Float, nullable)
- `turnaround_time_days` (Float, nullable)
- `do_follow_links_allowed` (Integer, nullable)
- `sponsor_tag_forced` (Boolean, nullable)
- `evidence_source` (String, nullable)

#### CampaignProfile
- `id` (UUID, non-nullable)
- `company_id` (UUID, non-nullable)
- `target_industry` (String, nullable)
- `target_geography` (String, nullable)
- `target_audience` (JSON, nullable)
- `min_domain_authority` (Float, nullable)
- `min_organic_traffic` (Float, nullable)
- `max_budget` (Float, nullable)
- `budget_currency` (String, nullable)
- `requires_dofollow` (Boolean, nullable)
- `created_at` (Timestamp, non-nullable)
- `updated_at` (Timestamp, non-nullable)

#### MatchingRun
- `id` (UUID, non-nullable)
- `campaign_profile_id` (UUID, non-nullable)
- `status` (String, non-nullable)
- `run_started_at` (Timestamp, non-nullable)
- `run_completed_at` (Timestamp, nullable)
- `total_eligible` (Integer, nullable)
- `total_excluded` (Integer, nullable)
- `profile_snapshot` (JSON, nullable)

#### MatchResult
- `id` (UUID, non-nullable)
- `matching_run_id` (UUID, non-nullable)
- `publisher_id` (UUID, non-nullable)
- `overall_score` (Float, non-nullable)
- `rank` (Integer, non-nullable)
- `component_scores` (JSON, non-nullable)
- `reasons` (JSON, non-nullable)
- `warnings` (JSON, nullable)

#### Shortlist / ShortlistItem
- Standard relations mapping MatchResults to user-curated Shortlists.

#### MediaPlan
- `id` (UUID, non-nullable)
- `company_id` (UUID, non-nullable, references `companies.id`)
- `name` (String, non-nullable, default "Draft Media Plan")
- `status` (String, non-nullable, values: "DRAFT", "FINAL")
- `notes` (Text, nullable)
- `created_at` (Timestamp with timezone, non-nullable)
- `updated_at` (Timestamp with timezone, non-nullable)

#### MediaPlanItem
- `id` (UUID, non-nullable)
- `media_plan_id` (UUID, non-nullable, references `media_plans.id`)
- `publisher_id` (UUID, non-nullable, references `publisher_records.id`)
- `match_result_id` (UUID, nullable, references `match_results.id`)
- `proposed_price` (Float, nullable)
- `proposed_currency` (String, nullable)
- `notes` (Text, nullable)
- `created_at` (Timestamp with timezone, non-nullable)

#### Workflow
- `id` (UUID, non-nullable)
- `name` (String, non-nullable)
- `discovery_query` (String, nullable)
- `target_company_count` (Integer, nullable)
- `selected_company_ids` (JSONB list of strings, nullable)
- `enabled_stages` (JSONB list of strings, non-nullable)
- `schedule_cron` (String, nullable)
- `schedule_timezone` (String, nullable)
- `last_run_at` (Timestamp with timezone, nullable)
- `batch_size` (Integer, nullable)
- `provider_request_limits` (JSONB dict, nullable)
- `max_retries` (Integer, nullable, default 3)
- `retry_backoff_seconds` (Integer, nullable, default 300)
- `max_runtime_seconds` (Integer, nullable)
- `is_enabled` (Boolean, non-nullable, default False)
- `created_at` (Timestamp with timezone, non-nullable)
- `updated_at` (Timestamp with timezone, non-nullable)

#### WorkflowRun
- `id` (UUID, non-nullable)
- `workflow_id` (UUID, non-nullable, references `workflows.id`)
- `trigger_type` (String, non-nullable, values: "MANUAL", "SCHEDULED")
- `status` (String, non-nullable, values: "QUEUED", "RUNNING", "PARTIAL", "COMPLETED", "FAILED", "CANCELLED", "PAUSED", "PENDING_APPROVAL")
- `current_stage` (String, nullable)
- `total_companies` (Integer, non-nullable, default 0)
- `successful_companies` (Integer, non-nullable, default 0)
- `failed_companies` (Integer, non-nullable, default 0)
- `skipped_stages` (JSONB list of strings, nullable)
- `retry_counts` (JSONB dict of stage -> int, nullable)
- `provider_failures` (JSONB dict of stage -> str, nullable)
- `stage_progress` (JSONB dict with stage metrics, timestamps, notes, nullable)
- `parameters` (JSONB dict with target company IDs and discovery configs, nullable)
- `approved_at` (Timestamp with timezone, nullable)
- `approved_by` (String, nullable)
- `error_summary` (Text, nullable)
- `started_at` (Timestamp with timezone, nullable)
- `completed_at` (Timestamp with timezone, nullable)
- `created_at` (Timestamp with timezone, non-nullable)
- `updated_at` (Timestamp with timezone, non-nullable)

### Phase 2.4 Outreach Automation Models

#### CompanyContact
- `id` (UUID, primary key)
- `company_id` (UUID, non-nullable, references `companies.id`)
- `email` (String, non-nullable)
- `first_name` (String, nullable)
- `last_name` (String, nullable)
- `full_name` (String, nullable)
- `job_title` (String, nullable)
- `department` (String, nullable)
- `source_type` (String, non-nullable, e.g. "WEBSITE_PAGE", "SECURITY_TXT", "INFERRED_ROLE")
- `source_url` (String, nullable)
- `confidence` (Float, non-nullable, default 0.5)
- `verification_status` (String, non-nullable, values: "VERIFIED", "INFERRED", "UNVERIFIED")
- `opt_out` (Boolean, non-nullable, default False)
- `opt_out_at` (Timestamp with timezone, nullable)
- `retrieval_timestamp` (Timestamp with timezone, non-nullable)
- `created_at` (Timestamp with timezone, non-nullable)
- `updated_at` (Timestamp with timezone, non-nullable)

#### OutreachCampaign
- `id` (UUID, primary key)
- `name` (String, non-nullable)
- `description` (Text, nullable)
- `status` (String, non-nullable, default "DRAFT", values: "DRAFT", "ACTIVE", "PAUSED", "ARCHIVED")
- `daily_send_limit` (Integer, non-nullable, default 20)
- `schedule_timezone` (String, non-nullable, default "UTC")
- `follow_up_delay_days` (Integer, non-nullable, default 3)
- `max_follow_ups` (Integer, non-nullable, default 2)
- `stop_on_reply` (Boolean, non-nullable, default True)
- `stop_on_bounce` (Boolean, non-nullable, default True)
- `stop_on_unsubscribe` (Boolean, non-nullable, default True)
- `template_subject` (String, nullable)
- `template_body` (Text, nullable)
- `created_at` (Timestamp with timezone, non-nullable)
- `updated_at` (Timestamp with timezone, non-nullable)

#### OutreachDraft
- `id` (UUID, primary key)
- `company_id` (UUID, non-nullable, references `companies.id`)
- `campaign_id` (UUID, nullable, references `outreach_campaigns.id`)
- `contact_id` (UUID, nullable, references `company_contacts.id`)
- `recipient_email` (String, non-nullable)
- `recipient_name` (String, nullable)
- `subject_line` (String, non-nullable)
- `body_text` (Text, non-nullable)
- `body_html` (Text, nullable)
- `call_to_action` (String, nullable)
- `prospect_summary` (Text, nullable)
- `evidence_citations` (JSONB list of citation dicts, nullable)
- `status` (String, non-nullable, default "DRAFT", values: "DRAFT", "PENDING_APPROVAL", "APPROVED", "QUEUED", "SENT", "FAILED", "CANCELLED")
- `approval_status` (String, non-nullable, default "UNAPPROVED", values: "UNAPPROVED", "APPROVED", "REJECTED")
- `approved_by` (String, nullable)
- `approved_at` (Timestamp with timezone, nullable)
- `rejection_reason` (String, nullable)
- `is_follow_up` (Boolean, non-nullable, default False)
- `sequence_step` (Integer, non-nullable, default 1)
- `parent_draft_id` (UUID, nullable, references `outreach_drafts.id`)
- `scheduled_send_at` (Timestamp with timezone, nullable)
- `sent_at` (Timestamp with timezone, nullable)
- `error_message` (Text, nullable)
- `created_at` (Timestamp with timezone, non-nullable)
- `updated_at` (Timestamp with timezone, non-nullable)

#### OutreachMessage
- `id` (UUID, primary key)
- `draft_id` (UUID, non-nullable, references `outreach_drafts.id`)
- `campaign_id` (UUID, nullable, references `outreach_campaigns.id`)
- `company_id` (UUID, non-nullable, references `companies.id`)
- `contact_id` (UUID, nullable, references `company_contacts.id`)
- `provider` (String, non-nullable, e.g. "Gmail", "SMTP", "Mock")
- `provider_message_id` (String, nullable)
- `provider_thread_id` (String, nullable)
- `sender_email` (String, non-nullable)
- `recipient_email` (String, non-nullable)
- `subject_line` (String, non-nullable)
- `body_text` (Text, non-nullable)
- `status` (String, non-nullable, default "SENT", values: "SENT", "DELIVERED", "OPENED", "REPLIED", "BOUNCED", "FAILED")
- `delivery_error` (Text, nullable)
- `sent_at` (Timestamp with timezone, non-nullable)
- `opened_at` (Timestamp with timezone, nullable)
- `replied_at` (Timestamp with timezone, nullable)
- `bounced_at` (Timestamp with timezone, nullable)
- `unsubscribed_at` (Timestamp with timezone, nullable)
- `created_at` (Timestamp with timezone, non-nullable)

#### OutreachSuppression
- `id` (UUID, primary key)
- `email` (String, non-nullable, unique index)
- `domain` (String, nullable, index)
- `reason` (String, non-nullable, default "MANUAL_OPTOUT", values: "UNSUBSCRIBE", "BOUNCE", "COMPLAINT", "MANUAL_OPTOUT")
- `source` (String, nullable)
- `created_at` (Timestamp with timezone, non-nullable)

### Phase 2.5 CRM & Sales Pipeline Entities

#### Company Alterations
- `sales_stage` (String, non-nullable, default "NEW", index) - Values: `NEW`, `RESEARCHED`, `QUALIFIED`, `CONTACTED`, `REPLIED`, `MEETING_SCHEDULED`, `PROPOSAL_SENT`, `NEGOTIATION`, `WON`, `LOST`, `NURTURE`
- `target_market` (String, nullable)
- `qualification_notes` (Text, nullable)
- `stage_updated_at` (Timestamp with timezone, non-nullable, default now)
- `stage_reason` (String, nullable)

#### CRMDeal
- `id` (UUID, primary key)
- `company_id` (UUID, non-nullable, FK to `companies.id`, index)
- `contact_id` (UUID, nullable, FK to `company_contacts.id`)
- `media_plan_id` (UUID, nullable, FK to `media_plans.id`)
- `campaign_id` (UUID, nullable, FK to `outreach_campaigns.id`, index) - Attribution linkage
- `deal_name` (String, non-nullable)
- `service_category` (String, non-nullable, default "FULL_SERVICE", values: "TECHNICAL_SEO", "LINK_BUILDING", "CONTENT_STRATEGY", "DIGITAL_PR", "FULL_SERVICE", "OTHER")
- `stage` (String, non-nullable, default "DISCOVERY", values: "DISCOVERY", "QUALIFICATION", "PROPOSAL", "NEGOTIATION", "WON", "LOST", index)
- `estimated_value` (Float, non-nullable, default 0.0)
- `proposed_value` (Float, nullable)
- `closed_amount` (Float, nullable) - Earned revenue upon authorized closure
- `cost_amount` (Float, nullable) - Recorded fulfillment/publisher costs
- `invoice_status` (String, nullable, values: "UNINVOICED", "DRAFT", "ISSUED", "PAID", "PARTIALLY_PAID", "REFUNDED")
- `invoiced_amount` (Float, nullable)
- `paid_amount` (Float, nullable)
- `discount_amount` (Float, default 0.0, nullable)
- `tax_amount` (Float, default 0.0, nullable)
- `refunded_amount` (Float, default 0.0, nullable)
- `currency` (String, non-nullable, default "USD")
- `expected_close_date` (Timestamp with timezone, nullable)
- `actual_close_date` (Timestamp with timezone, nullable)
- `outcome` (String, nullable, values: "OPEN", "WON", "LOST")
- `loss_reason` (String, nullable)
- `win_reason` (String, nullable)
- `notes` (Text, nullable)
- `created_at` (Timestamp with timezone, non-nullable)
- `updated_at` (Timestamp with timezone, non-nullable)

#### CRMTask
- `id` (UUID, primary key)
- `company_id` (UUID, non-nullable, FK to `companies.id`, index)
- `contact_id` (UUID, nullable, FK to `company_contacts.id`)
- `deal_id` (UUID, nullable, FK to `crm_deals.id`)
- `title` (String, non-nullable)
- `description` (Text, nullable)
- `task_type` (String, non-nullable, default "FOLLOW_UP", values: "CALL", "MEETING", "RESEARCH", "FOLLOW_UP", "EMAIL", "OTHER", index)
- `priority` (String, non-nullable, default "MEDIUM", values: "LOW", "MEDIUM", "HIGH", "URGENT")
- `status` (String, non-nullable, default "PENDING", values: "PENDING", "IN_PROGRESS", "COMPLETED", "CANCELLED", index)
- `due_date` (Timestamp with timezone, nullable)
- `completed_at` (Timestamp with timezone, nullable)
- `completed_by` (String, nullable)
- `completion_notes` (Text, nullable)
- `idempotency_key` (String, nullable, unique, index) - Prevents duplicate tasks on workflow retries
- `created_at` (Timestamp with timezone, non-nullable)
- `updated_at` (Timestamp with timezone, non-nullable)

#### CRMActivity
- `id` (UUID, primary key)
- `company_id` (UUID, non-nullable, FK to `companies.id`, index)
- `deal_id` (UUID, nullable, FK to `crm_deals.id`)
- `contact_id` (UUID, nullable, FK to `company_contacts.id`)
- `activity_type` (String, non-nullable, values: "STAGE_CHANGED", "DEAL_CREATED", "DEAL_WON", "DEAL_LOST", "TASK_CREATED", "TASK_COMPLETED", "NOTE_ADDED", "OUTREACH_SENT", "REPLY_RECEIVED", index)
- `actor` (String, non-nullable, default "human_reviewer")
- `title` (String, non-nullable)
- `details` (JSONB, nullable)
- `created_at` (Timestamp with timezone, non-nullable)

#### CRMNote
- `id` (UUID, primary key)
- `company_id` (UUID, non-nullable, FK to `companies.id`, index)
- `deal_id` (UUID, nullable, FK to `crm_deals.id`)
- `author` (String, non-nullable, default "human_reviewer")
- `content` (Text, non-nullable)
- `created_at` (Timestamp with timezone, non-nullable)
- `updated_at` (Timestamp with timezone, non-nullable)

### Phase 3.0: AI Sales Intelligence & Lead Prioritization Models

#### SalesIntelligenceScore
- `id` (UUID, primary key)
- `company_id` (UUID, non-nullable, FK to `companies.id`, unique, index)
- `scoring_version` (String, non-nullable, default "v3.0.0")
- `overall_priority_score` (Float, non-nullable, default 0.0, index)
- `seo_severity_score` (Float, non-nullable, default 0.0)
- `service_fit_score` (Float, non-nullable, default 0.0)
- `publisher_fit_score` (Float, non-nullable, default 0.0)
- `business_fit_score` (Float, non-nullable, default 0.0)
- `evidence_confidence_score` (Float, non-nullable, default 0.0)
- `data_completeness` (Float, non-nullable, default 0.0)
- `primary_recommended_service` (String, nullable)
- `recommended_services` (JSONB list of dicts, nullable)
- `positive_indicators` (JSONB list of strings, nullable)
- `limitations` (JSONB list of strings, nullable)
- `missing_information` (JSONB list of strings, nullable)
- `component_weights` (JSONB dict, nullable)
- `recommended_next_action` (String, nullable)
- `review_status` (String, non-nullable, default "UNREVIEWED", values: "UNREVIEWED", "IN_REVIEW", "QUALIFIED", "REJECTED", index)
- `human_override_score` (Float, nullable)
- `human_override_reason` (String, nullable)
- `human_override_by` (String, nullable)
- `human_override_at` (Timestamp with timezone, nullable)
- `evaluated_at` (Timestamp with timezone, default UTC now)
- `created_at` (Timestamp with timezone, default UTC now)
- `updated_at` (Timestamp with timezone, default UTC now)

#### SalesOpportunity
- `id` (UUID, primary key)
- `company_id` (UUID, non-nullable, FK to `companies.id`, index)
- `category` (String, non-nullable, values: "TECHNICAL_SEO", "INDEXABILITY_CRAWLABILITY", "PAGE_METADATA", "CONTENT_COVERAGE", "INTERNAL_LINKING", "BACKLINK_AUTHORITY", "COMPETITIVE_GAP", "DIGITAL_PR_PUBLISHER", index)
- `title` (String, non-nullable)
- `description` (Text, non-nullable)
- `severity` (String, non-nullable, values: "CRITICAL", "HIGH", "MEDIUM", "LOW", "INFORMATIONAL", index)
- `impact_rationale` (Text, non-nullable)
- `confidence` (Float, default 1.0, non-nullable)
- `recommended_service` (String, non-nullable)
- `supporting_evidence` (JSONB list of dicts, nullable)
- `status` (String, non-nullable, default "ACTIVE", values: "ACTIVE", "ADDRESSED", "DISMISSED", index)
- `detection_rule` (String, non-nullable)
- `detection_timestamp` (Timestamp with timezone, default UTC now)
- `created_at` (Timestamp with timezone, default UTC now)
- `updated_at` (Timestamp with timezone, default UTC now)

#### SalesBrief
- `id` (UUID, primary key)
- `company_id` (UUID, non-nullable, FK to `companies.id`, unique, index)
- `title` (String, non-nullable)
- `company_overview` (Text, non-nullable)
- `seo_findings_summary` (Text, non-nullable)
- `top_opportunities` (JSONB list of dicts, nullable)
- `recommended_services` (JSONB list of dicts, nullable)
- `matched_publishers` (JSONB list of dicts, nullable)
- `data_gaps` (JSONB list of strings, nullable)
- `discovery_questions` (JSONB list of strings, nullable)
- `recommended_next_action` (String, nullable)
- `full_brief_markdown` (Text, non-nullable)
- `is_customized` (Boolean, default False, non-nullable)
- `last_edited_by` (String, nullable)
- `last_edited_at` (Timestamp with timezone, nullable)
- `created_at` (Timestamp with timezone, default UTC now)
- `updated_at` (Timestamp with timezone, default UTC now)

### Phase 3.1 Tables (Publisher Intelligence & Data Quality Monitoring)

#### PublisherQualityScore
- `id` (UUID, primary key)
- `publisher_id` (UUID, non-nullable, FK to `publisher_records.id`, unique, index)
- `overall_quality_score` (Float, non-nullable, default 100.0, index)
- `completeness_score` (Float, non-nullable, default 100.0)
- `freshness_score` (Float, non-nullable, default 100.0)
- `validity_score` (Float, non-nullable, default 100.0)
- `consistency_score` (Float, non-nullable, default 100.0)
- `price_freshness_status` (String, non-nullable, default "UNKNOWN", values: "FRESH", "STALE", "MISSING", "EXPIRED")
- `metrics_freshness_status` (String, non-nullable, default "UNKNOWN", values: "FRESH", "STALE", "MISSING", "EXPIRED")
- `site_freshness_status` (String, non-nullable, default "UNKNOWN", values: "FRESH", "STALE", "MISSING", "EXPIRED")
- `last_price_checked_at` (Timestamp with timezone, nullable)
- `last_metrics_checked_at` (Timestamp with timezone, nullable)
- `last_site_checked_at` (Timestamp with timezone, nullable)
- `open_issues_count` (Integer, non-nullable, default 0)
- `critical_issues_count` (Integer, non-nullable, default 0)
- `has_duplicates` (Boolean, non-nullable, default False)
- `has_conflicts` (Boolean, non-nullable, default False)
- `last_audited_at` (Timestamp with timezone, default UTC now)
- `created_at` (Timestamp with timezone, default UTC now)
- `updated_at` (Timestamp with timezone, default UTC now)

#### PublisherQualityFinding
- `id` (UUID, primary key)
- `publisher_id` (UUID, non-nullable, FK to `publisher_records.id`, index)
- `issue_type` (String, non-nullable, values: "MISSING_FIELD", "STALE_DATA", "INVALID_DATA", "DUPLICATE_RECORD", "CONFLICTING_DATA", "UNSUPPORTED_CURRENCY", index)
- `field_name` (String, non-nullable, values: "price", "currency", "metric_da", "metric_dr", "metric_traffic", "audience_focus", "website_url", "canonical_domain")
- `severity` (String, non-nullable, default "MEDIUM", values: "CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO", index)
- `status` (String, non-nullable, default "OPEN", values: "OPEN", "RESOLVED", "IGNORED", index)
- `title` (String, non-nullable)
- `description` (Text, non-nullable)
- `evidence` (JSONB dict, nullable)
- `recommended_action` (Text, non-nullable)
- `resolution_notes` (Text, nullable)
- `resolved_by` (String, nullable)
- `resolved_at` (Timestamp with timezone, nullable)
- `created_at` (Timestamp with timezone, default UTC now)
- `updated_at` (Timestamp with timezone, default UTC now)

#### PublisherRefreshLog
- `id` (UUID, primary key)
- `publisher_id` (UUID, non-nullable, FK to `publisher_records.id`, index)
- `target_field` (String, non-nullable, values: "metrics", "site", "price", "all")
- `provider_attempted` (String, non-nullable, values: "Moz", "Ahrefs", "Semrush", "Crawler", "Manual", "SEO Provider Registry")
- `status` (String, non-nullable, values: "SUCCESS", "FAILED", "RATE_LIMITED", "PROVIDER_NOT_CONFIGURED", "UNAVAILABLE", index)
- `details` (JSONB dict, nullable)
- `error_message` (Text, nullable)
- `initiated_by` (String, non-nullable, default "system_audit")
- `created_at` (Timestamp with timezone, default UTC now)

---

### Phase 3.2: Revenue & Performance Analytics

#### RevenueAnalyticsSnapshot
- `id` (UUID, primary key)
- `period_start` (Timestamp with timezone, nullable)
- `period_end` (Timestamp with timezone, nullable)
- `period_type` (String, non-nullable, default "ALL_TIME", values: "ALL_TIME", "30D", "90D", "180D", "YTD", "MONTHLY", "CUSTOM", index)
- `reporting_currency` (String(3), non-nullable, default "USD")
- `total_realized_revenue` (Float, non-nullable, default 0.0) - Strictly closed-won revenue
- `total_open_pipeline_value` (Float, non-nullable, default 0.0) - Strictly unearned open pipeline
- `weighted_pipeline_value` (Float, non-nullable, default 0.0) - Probability-weighted pipeline
- `total_recorded_costs` (Float, nullable) - Verified fulfillment costs (None if unrecorded)
- `gross_profit` (Float, nullable) - Realized revenue minus verified costs (None if unrecorded)
- `gross_margin_pct` (Float, nullable) - Gross profit margin percentage (None if unrecorded)
- `deal_count_won` (Integer, non-nullable, default 0)
- `deal_count_lost` (Integer, non-nullable, default 0)
- `deal_count_open` (Integer, non-nullable, default 0)
- `average_deal_size_won` (Float, nullable)
- `average_sales_cycle_days` (Float, nullable) - Days from creation to closure
- `revenue_by_service` (JSONB dict, nullable) - Segmentation by service category
- `revenue_by_client` (JSONB list, nullable) - Revenue leaderboard by client company
- `revenue_by_campaign` (JSONB list, nullable) - Campaign-attributed ROI with caveats
- `funnel_metrics` (JSONB dict, nullable) - Conversion rates and bottleneck diagnosis
- `currency_breakdown` (JSONB dict, nullable) - Native un-normalized totals per currency
- `data_limitations` (JSONB list, nullable) - Audit disclosures and missing-data caveats
- `created_at` (Timestamp with timezone, default UTC now, index)
- `created_by` (String, non-nullable, default "system")

---

### Phase 3.3: Advanced Competitive SEO Intelligence

#### CompanyCompetitor
- `id` (UUID, primary key)
- `company_id` (UUID, non-nullable, FK to `companies.id`, index) - Prospect company
- `competitor_company_id` (UUID, nullable, FK to `companies.id`, index) - Matched competitor company record if present
- `competitor_name` (String, non-nullable) - Business name of the tracked competitor
- `competitor_domain` (String, non-nullable, index) - Canonical domain of the competitor
- `relevance_score` (Float, non-nullable, default 0.85) - Relevance score from 0.0 to 1.0
- `relevance_tier` (String, non-nullable, default "DIRECT", values: "DIRECT", "INDIRECT", "TOPICAL_PEER", "IRRELEVANT", index)
- `validation_status` (String, non-nullable, default "VERIFIED", values: "VERIFIED", "UNVERIFIED", "REJECTED", index)
- `validation_evidence` (JSONB dict, nullable) - Traceable reasons, keyword terms, and discovery metadata
- `discovery_method` (String, non-nullable, default "MANUAL", values: "INDUSTRY_TOPICAL_OVERLAP", "MANUAL", "AI_DISCOVERY")
- `is_active` (Boolean, non-nullable, default True, index)
- `notes` (Text, nullable) - Operator notes and strategic context
- `created_at` (Timestamp with timezone, default UTC now)
- `updated_at` (Timestamp with timezone, default UTC now, auto-update)

#### CompetitiveAnalysisRun
- `id` (UUID, primary key)
- `company_id` (UUID, non-nullable, FK to `companies.id`, index) - Target prospect company
- `competitor_id` (UUID, non-nullable, FK to `company_competitors.id`, index) - Tracked competitor record
- `status` (String, non-nullable, default "COMPLETED", values: "RUNNING", "COMPLETED", "FAILED", index)
- `prospect_scan_id` (UUID, nullable, FK to `website_scans.id`) - Reference to input prospect crawl
- `competitor_scan_id` (UUID, nullable, FK to `website_scans.id`) - Reference to input competitor crawl
- `summary_findings` (JSONB dict, nullable) - Comparative crawl metrics and strategic diagnosis
- `content_gaps` (JSONB list, nullable) - Search-intent tagged keyword & content gaps (`INFORMATIONAL`, `COMMERCIAL`, `TRANSACTIONAL`, `NAVIGATIONAL`)
- `technical_gaps` (JSONB list, nullable) - Observable crawl disparities (SSL, Robots, Sitemap, Schema, Headings, Viewport)
- `internal_linking_gaps` (JSONB list, nullable) - Topical silo depth and internal link equity analysis
- `backlink_gaps` (JSONB dict, nullable) - DA/DR differential via authorized providers (None if unconfigured, strictly non-fabricated)
- `publisher_opportunities` (JSONB list, nullable) - Real inventory matches from `publisher_records` and `publisher_observations`
- `prioritized_recommendations` (JSONB list, nullable) - GrokxSEO action items ranked by ROI priority score (0-100)
- `data_limitations` (JSONB list, nullable) - Explicit disclosures of unconfigured providers and crawl constraints
- `analyzed_at` (Timestamp with timezone, default UTC now, index)
- `created_at` (Timestamp with timezone, default UTC now)
- `updated_at` (Timestamp with timezone, default UTC now, auto-update)

---

### Phase 3.4: Automated Reporting & Client Portals

#### PortalUser
- `id` (UUID, primary key)
- `email` (String, unique, non-nullable, index) - Portal user login address
- `hashed_password` (String, non-nullable) - Salted PBKDF2-HMAC-SHA256 password hash (100,000 rounds)
- `full_name` (String, non-nullable)
- `role` (String, non-nullable, default "CLIENT_USER", values: "ADMIN", "AGENCY_STAFF", "CLIENT_USER", index)
- `company_id` (UUID, nullable, FK to `companies.id`, index) - Assigned client company for tenant isolation
- `is_active` (Boolean, non-nullable, default True, index)
- `last_login_at` (Timestamp with timezone, nullable)
- `created_at` (Timestamp with timezone, default UTC now)
- `updated_at` (Timestamp with timezone, default UTC now, auto-update)

#### ClientInvitation
- `id` (UUID, primary key)
- `company_id` (UUID, non-nullable, FK to `companies.id`, index) - Target client workspace
- `email` (String, non-nullable, index) - Invitee email address
- `invitation_token` (String, unique, non-nullable, index) - Unguessable 32-byte secure URL token
- `role` (String, non-nullable, default "CLIENT_USER", values: "CLIENT_USER", "AGENCY_STAFF")
- `invited_by_user_id` (UUID, nullable, FK to `portal_users.id`)
- `status` (String, non-nullable, default "PENDING", values: "PENDING", "ACCEPTED", "EXPIRED", "REVOKED", index)
- `expires_at` (Timestamp with timezone, non-nullable) - 7-day expiration boundary
- `accepted_at` (Timestamp with timezone, nullable)
- `created_at` (Timestamp with timezone, default UTC now)

#### ClientReport
- `id` (UUID, primary key)
- `company_id` (UUID, non-nullable, FK to `companies.id`, index) - Target client account
- `title` (String, non-nullable) - Branded report headline
- `report_type` (String, non-nullable, default "MONTHLY_PERFORMANCE", values: "MONTHLY_PERFORMANCE", "QUARTERLY_REVIEW", "SEO_AUDIT_DELIVERABLE", "EXECUTIVE_SUMMARY", "CAMPAIGN_SUMMARY", index)
- `reporting_period_start` (Timestamp with timezone, nullable)
- `reporting_period_end` (Timestamp with timezone, nullable)
- `status` (String, non-nullable, default "DRAFT", values: "DRAFT", "PENDING_REVIEW", "APPROVED", "DELIVERED", "ARCHIVED", index)
- `approval_status` (String, non-nullable, default "UNAPPROVED", values: "UNAPPROVED", "APPROVED", "REJECTED", index) - Mandated agency approval barrier
- `approved_by_user_id` (UUID, nullable, FK to `portal_users.id`)
- `approved_at` (Timestamp with timezone, nullable)
- `branding` (JSONB dict, nullable) - Logo URL, primary color, agency name, client name, footer disclaimer
- `sections` (JSONB list, nullable) - Structured, sanitized report sections (Executive Summary, Technical SEO, Content Gaps, Backlinks Disclosure, Placements, Recommendations)
- `summary_metrics` (JSONB dict, nullable) - Client-visible high-level metrics
- `delivery_status` (String, non-nullable, default "NOT_DELIVERED", values: "NOT_DELIVERED", "SCHEDULED", "SENT", "FAILED", "DELIVERED")
- `generated_by` (String, non-nullable, default "manual_operator", values: "manual_operator", "automated_job")
- `data_limitations` (JSONB list, nullable) - Transparency disclosures and non-fabrication caveats
- `export_formats` (JSONB dict, nullable) - Export endpoints for Markdown, HTML, and PDF
- `created_at` (Timestamp with timezone, default UTC now)
- `updated_at` (Timestamp with timezone, default UTC now, auto-update)

#### ReportSchedule
- `id` (UUID, primary key)
- `company_id` (UUID, non-nullable, FK to `companies.id`, index) - Client company
- `report_type` (String, non-nullable, default "MONTHLY_PERFORMANCE")
- `frequency` (String, non-nullable, default "MONTHLY", values: "WEEKLY", "MONTHLY", "QUARTERLY")
- `day_of_month` (Integer, non-nullable, default 1)
- `day_of_week` (Integer, non-nullable, default 0)
- `time_of_day` (String, non-nullable, default "09:00")
- `time_zone` (String, non-nullable, default "UTC") - Client timezone handling
- `recipients` (JSONB list, nullable) - Array of validated recipient email addresses
- `is_active` (Boolean, non-nullable, default True, index)
- `requires_approval` (Boolean, non-nullable, default True) - Safety gate before automated external dispatch
- `last_generated_at` (Timestamp with timezone, nullable)
- `next_run_at` (Timestamp with timezone, nullable)
- `created_at` (Timestamp with timezone, default UTC now)
- `updated_at` (Timestamp with timezone, default UTC now, auto-update)

#### ReportDeliveryLog
- `id` (UUID, primary key)
- `report_id` (UUID, non-nullable, FK to `client_reports.id`, index)
- `recipient_email` (String, non-nullable, index)
- `delivery_channel` (String, non-nullable, default "EMAIL")
- `idempotency_key` (String, unique, non-nullable, index) - Deterministic key preventing duplicate sends on job retries
- `status` (String, non-nullable, default "PENDING", values: "PENDING", "SENT", "FAILED", "SIMULATED", index)
- `sent_at` (Timestamp with timezone, nullable)
- `error_message` (Text, nullable)
- `created_at` (Timestamp with timezone, default UTC now)

#### PortalAuditLog
- `id` (UUID, primary key)
- `user_id` (UUID, nullable, FK to `portal_users.id`, index)
- `company_id` (UUID, nullable, FK to `companies.id`, index)
- `action` (String, non-nullable, index, values: "LOGIN_SUCCESS", "LOGIN_FAILED", "CREATE_REPORT", "VIEW_REPORT", "EXPORT_REPORT_MARKDOWN", "EXPORT_REPORT_HTML", "APPROVE_REPORT", "REJECT_REPORT", "DELIVER_REPORT", "CREATE_SCHEDULE", "UPDATE_SCHEDULE", "INVITE_USER", "ACCEPT_INVITATION", "REVOKE_INVITATION", "VIEW_WORKSPACE", "UNAUTHORIZED_ACCESS_ATTEMPT")
- `resource_type` (String, non-nullable)
- `resource_id` (String, nullable)
- `details` (JSONB dict, nullable)
- `ip_address` (String, nullable)
- `timestamp` (Timestamp with timezone, default UTC now, index)

