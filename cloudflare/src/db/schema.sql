-- ProspectOS Cloudflare D1 Relational Schema (SQLite 3 compatible)
-- Auto-generated from SQLAlchemy metadata in strict topological order
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS "ai_provider_settings" (
    "id" TEXT PRIMARY KEY,
    "provider_name" TEXT NOT NULL,
    "display_name" TEXT NOT NULL,
    "is_enabled" INTEGER NOT NULL DEFAULT True,
    "is_default" INTEGER NOT NULL DEFAULT False,
    "default_model" TEXT NOT NULL,
    "available_models" TEXT NOT NULL,
    "api_key_masked" TEXT,
    "api_key_encrypted" TEXT,
    "rpm_limit" INTEGER NOT NULL DEFAULT 60,
    "tpm_limit" INTEGER NOT NULL DEFAULT 100000,
    "tokens_used_today" INTEGER NOT NULL DEFAULT 0,
    "total_tokens_used" INTEGER NOT NULL DEFAULT 0,
    "estimated_cost_usd" REAL NOT NULL DEFAULT 0.0,
    "last_tested_at" TEXT,
    "last_error" TEXT,
    "feature_flags" TEXT NOT NULL,
    "updated_at" TEXT NOT NULL
);
CREATE UNIQUE INDEX IF NOT EXISTS "ix_ai_provider_settings_provider_name" ON "ai_provider_settings" ("provider_name");

CREATE TABLE IF NOT EXISTS "crm_lead_segments" (
    "id" TEXT PRIMARY KEY,
    "name" TEXT NOT NULL,
    "description" TEXT,
    "is_dynamic" INTEGER NOT NULL DEFAULT True,
    "filter_criteria" TEXT NOT NULL,
    "color" TEXT NOT NULL DEFAULT 'blue',
    "icon" TEXT,
    "member_count" INTEGER NOT NULL DEFAULT 0,
    "created_at" TEXT NOT NULL,
    "updated_at" TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS "ix_crm_lead_segments_name" ON "crm_lead_segments" ("name");
CREATE INDEX IF NOT EXISTS "ix_crm_lead_segments_created_at" ON "crm_lead_segments" ("created_at");

CREATE TABLE IF NOT EXISTS "crm_user_preferences" (
    "id" TEXT PRIMARY KEY,
    "user_id" TEXT NOT NULL DEFAULT 'default_user',
    "preferred_industries" TEXT NOT NULL,
    "preferred_countries" TEXT NOT NULL,
    "min_lead_score" REAL NOT NULL DEFAULT 50.0,
    "scoring_weights" TEXT NOT NULL,
    "target_market_rules" TEXT NOT NULL,
    "created_at" TEXT NOT NULL,
    "updated_at" TEXT NOT NULL
);
CREATE UNIQUE INDEX IF NOT EXISTS "ix_crm_user_preferences_user_id" ON "crm_user_preferences" ("user_id");

CREATE TABLE IF NOT EXISTS "google_drive_connections" (
    "id" TEXT PRIMARY KEY,
    "is_connected" INTEGER NOT NULL DEFAULT False,
    "account_email" TEXT,
    "access_token_encrypted" TEXT,
    "refresh_token_encrypted" TEXT,
    "token_expiry" TEXT,
    "client_id" TEXT,
    "client_secret_encrypted" TEXT,
    "selected_folder_id" TEXT,
    "selected_folder_path" TEXT NOT NULL DEFAULT 'ProspectOS/Leads/',
    "master_sheet_id" TEXT,
    "master_sheet_url" TEXT,
    "export_format" TEXT NOT NULL DEFAULT 'GOOGLE_SHEET',
    "last_sync_at" TEXT,
    "last_sync_status" TEXT NOT NULL DEFAULT 'IDLE',
    "last_error_message" TEXT,
    "auto_sync_enabled" INTEGER NOT NULL DEFAULT True,
    "created_at" TEXT NOT NULL,
    "updated_at" TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS "import_batches" (
    "id" TEXT PRIMARY KEY,
    "original_filename" TEXT NOT NULL,
    "status" TEXT NOT NULL,
    "total_rows" INTEGER NOT NULL DEFAULT 0,
    "valid_rows" INTEGER NOT NULL DEFAULT 0,
    "invalid_rows" INTEGER NOT NULL DEFAULT 0,
    "created_records" INTEGER NOT NULL DEFAULT 0,
    "updated_records" INTEGER NOT NULL DEFAULT 0,
    "skipped_rows" INTEGER NOT NULL DEFAULT 0,
    "failed_rows" INTEGER NOT NULL DEFAULT 0,
    "error_details" TEXT,
    "created_at" TEXT NOT NULL,
    "updated_at" TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS "outreach_campaigns" (
    "id" TEXT PRIMARY KEY,
    "name" TEXT NOT NULL,
    "description" TEXT,
    "status" TEXT NOT NULL DEFAULT 'DRAFT',
    "daily_send_limit" INTEGER NOT NULL DEFAULT 20,
    "schedule_timezone" TEXT NOT NULL DEFAULT 'UTC',
    "follow_up_delay_days" INTEGER NOT NULL DEFAULT 3,
    "max_follow_ups" INTEGER NOT NULL DEFAULT 2,
    "stop_on_reply" INTEGER NOT NULL DEFAULT True,
    "stop_on_bounce" INTEGER NOT NULL DEFAULT True,
    "stop_on_unsubscribe" INTEGER NOT NULL DEFAULT True,
    "template_subject" TEXT,
    "template_body" TEXT,
    "created_at" TEXT NOT NULL,
    "updated_at" TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS "outreach_suppressions" (
    "id" TEXT PRIMARY KEY,
    "email" TEXT NOT NULL,
    "domain" TEXT,
    "reason" TEXT NOT NULL,
    "source" TEXT,
    "created_at" TEXT NOT NULL
);
CREATE UNIQUE INDEX IF NOT EXISTS "ix_outreach_suppressions_email" ON "outreach_suppressions" ("email");
CREATE INDEX IF NOT EXISTS "ix_outreach_suppressions_domain" ON "outreach_suppressions" ("domain");

CREATE TABLE IF NOT EXISTS "platform_settings" (
    "id" TEXT PRIMARY KEY,
    "category" TEXT NOT NULL,
    "key" TEXT NOT NULL,
    "value" TEXT NOT NULL,
    "description" TEXT,
    "updated_by" TEXT,
    "updated_at" TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS "ix_platform_settings_category" ON "platform_settings" ("category");
CREATE UNIQUE INDEX IF NOT EXISTS "ix_platform_settings_key" ON "platform_settings" ("key");

CREATE TABLE IF NOT EXISTS "revenue_analytics_snapshots" (
    "id" TEXT PRIMARY KEY,
    "period_start" TEXT,
    "period_end" TEXT,
    "period_type" TEXT NOT NULL DEFAULT 'ALL_TIME',
    "reporting_currency" TEXT NOT NULL DEFAULT 'USD',
    "total_realized_revenue" REAL NOT NULL DEFAULT 0.0,
    "total_open_pipeline_value" REAL NOT NULL DEFAULT 0.0,
    "weighted_pipeline_value" REAL NOT NULL DEFAULT 0.0,
    "total_recorded_costs" REAL,
    "gross_profit" REAL,
    "gross_margin_pct" REAL,
    "deal_count_won" INTEGER NOT NULL DEFAULT 0,
    "deal_count_lost" INTEGER NOT NULL DEFAULT 0,
    "deal_count_open" INTEGER NOT NULL DEFAULT 0,
    "average_deal_size_won" REAL,
    "average_sales_cycle_days" REAL,
    "revenue_by_service" TEXT,
    "revenue_by_client" TEXT,
    "revenue_by_campaign" TEXT,
    "funnel_metrics" TEXT,
    "currency_breakdown" TEXT,
    "data_limitations" TEXT,
    "created_at" TEXT NOT NULL,
    "created_by" TEXT NOT NULL DEFAULT 'system'
);
CREATE INDEX IF NOT EXISTS "ix_revenue_analytics_snapshots_period_type" ON "revenue_analytics_snapshots" ("period_type");

CREATE TABLE IF NOT EXISTS "role_permissions" (
    "id" TEXT PRIMARY KEY,
    "role_name" TEXT NOT NULL,
    "display_name" TEXT NOT NULL,
    "description" TEXT,
    "permissions" TEXT NOT NULL,
    "is_system_role" INTEGER NOT NULL DEFAULT True,
    "created_at" TEXT NOT NULL,
    "updated_at" TEXT NOT NULL
);
CREATE UNIQUE INDEX IF NOT EXISTS "ix_role_permissions_role_name" ON "role_permissions" ("role_name");

CREATE TABLE IF NOT EXISTS "scraper_api_keys" (
    "id" TEXT PRIMARY KEY,
    "key_hash" TEXT NOT NULL,
    "name" TEXT NOT NULL,
    "prefix" TEXT NOT NULL,
    "is_active" INTEGER NOT NULL DEFAULT True,
    "rate_limit_rpm" INTEGER NOT NULL DEFAULT 60,
    "last_used_at" TEXT,
    "created_at" TEXT NOT NULL
);
CREATE UNIQUE INDEX IF NOT EXISTS "ix_scraper_api_keys_key_hash" ON "scraper_api_keys" ("key_hash");

CREATE TABLE IF NOT EXISTS "scraper_tasks" (
    "id" TEXT PRIMARY KEY,
    "name" TEXT NOT NULL,
    "description" TEXT,
    "task_type" TEXT NOT NULL DEFAULT 'CUSTOM',
    "template_id" TEXT,
    "target_url" TEXT,
    "workflow_config" TEXT NOT NULL,
    "execution_mode" TEXT NOT NULL DEFAULT 'CLOUD',
    "status" TEXT NOT NULL DEFAULT 'DRAFT',
    "schedule_type" TEXT NOT NULL DEFAULT 'NONE',
    "schedule_cron" TEXT,
    "schedule_timezone" TEXT NOT NULL DEFAULT 'UTC',
    "is_schedule_active" INTEGER NOT NULL DEFAULT False,
    "last_run_at" TEXT,
    "next_run_at" TEXT,
    "total_records" INTEGER NOT NULL DEFAULT 0,
    "successful_records" INTEGER NOT NULL DEFAULT 0,
    "failed_records" INTEGER NOT NULL DEFAULT 0,
    "duplicate_records" INTEGER NOT NULL DEFAULT 0,
    "last_error" TEXT,
    "created_at" TEXT NOT NULL,
    "updated_at" TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS "ix_scraper_tasks_name" ON "scraper_tasks" ("name");
CREATE INDEX IF NOT EXISTS "ix_scraper_tasks_task_type" ON "scraper_tasks" ("task_type");
CREATE INDEX IF NOT EXISTS "ix_scraper_tasks_status" ON "scraper_tasks" ("status");
CREATE INDEX IF NOT EXISTS "ix_scraper_tasks_template_id" ON "scraper_tasks" ("template_id");
CREATE INDEX IF NOT EXISTS "ix_scraper_tasks_created_at" ON "scraper_tasks" ("created_at");

CREATE TABLE IF NOT EXISTS "seo_global_configs" (
    "id" TEXT PRIMARY KEY,
    "site_name" TEXT NOT NULL DEFAULT 'ProspectOS',
    "default_meta_title" TEXT NOT NULL DEFAULT 'ProspectOS | AI Web Scraping & Lead Intelligence Platform',
    "default_meta_description" TEXT NOT NULL DEFAULT 'Enterprise web scraping, autonomous prospect discovery, and AI-powered CRM intelligence system.',
    "default_canonical_domain" TEXT NOT NULL DEFAULT 'https://prospectos.com',
    "default_og_image_url" TEXT DEFAULT '/og-image.png',
    "robots_txt_content" TEXT,
    "sitemap_enabled" INTEGER NOT NULL DEFAULT True,
    "gsc_verification_code" TEXT,
    "ga4_measurement_id" TEXT,
    "bing_verification_code" TEXT,
    "updated_at" TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS "seo_public_pages" (
    "id" TEXT PRIMARY KEY,
    "path" TEXT NOT NULL,
    "page_name" TEXT NOT NULL,
    "meta_title" TEXT NOT NULL,
    "meta_description" TEXT NOT NULL,
    "canonical_url" TEXT NOT NULL,
    "og_title" TEXT,
    "og_description" TEXT,
    "og_image_url" TEXT,
    "twitter_card" TEXT NOT NULL DEFAULT 'summary_large_image',
    "robots_directives" TEXT NOT NULL DEFAULT 'index,follow',
    "schema_type" TEXT NOT NULL DEFAULT 'SoftwareApplication',
    "structured_data_json" TEXT,
    "sitemap_priority" REAL NOT NULL DEFAULT 0.8,
    "change_frequency" TEXT NOT NULL DEFAULT 'weekly',
    "is_published" INTEGER NOT NULL DEFAULT True,
    "last_audited_at" TEXT,
    "audit_score" INTEGER NOT NULL DEFAULT 100,
    "audit_issues" TEXT NOT NULL,
    "created_at" TEXT NOT NULL,
    "updated_at" TEXT NOT NULL
);
CREATE UNIQUE INDEX IF NOT EXISTS "ix_seo_public_pages_path" ON "seo_public_pages" ("path");

CREATE TABLE IF NOT EXISTS "social_connections" (
    "id" TEXT PRIMARY KEY,
    "channel" TEXT NOT NULL,
    "account_name" TEXT,
    "account_id" TEXT,
    "phone_number" TEXT,
    "is_connected" INTEGER NOT NULL DEFAULT False,
    "permissions" TEXT,
    "access_token_encrypted" TEXT,
    "token_expires_at" TEXT,
    "messaging_enabled" INTEGER NOT NULL DEFAULT False,
    "last_successful_operation_at" TEXT,
    "configuration_error" TEXT,
    "settings_data" TEXT,
    "created_at" TEXT NOT NULL,
    "updated_at" TEXT NOT NULL
);
CREATE UNIQUE INDEX IF NOT EXISTS "ix_social_connections_channel" ON "social_connections" ("channel");

CREATE TABLE IF NOT EXISTS "sources" (
    "id" TEXT PRIMARY KEY,
    "name" TEXT NOT NULL,
    "source_type" TEXT NOT NULL,
    "base_url" TEXT,
    "description" TEXT,
    "created_at" TEXT NOT NULL,
    "updated_at" TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS "workflows" (
    "id" TEXT PRIMARY KEY,
    "name" TEXT NOT NULL,
    "discovery_query" TEXT,
    "target_company_count" INTEGER,
    "selected_company_ids" TEXT,
    "enabled_stages" TEXT NOT NULL,
    "schedule_cron" TEXT,
    "schedule_timezone" TEXT,
    "last_run_at" TEXT,
    "batch_size" INTEGER,
    "provider_request_limits" TEXT,
    "max_retries" INTEGER DEFAULT 3,
    "retry_backoff_seconds" INTEGER DEFAULT 300,
    "max_runtime_seconds" INTEGER,
    "is_enabled" INTEGER NOT NULL DEFAULT False,
    "created_at" TEXT NOT NULL,
    "updated_at" TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS "companies" (
    "id" TEXT PRIMARY KEY,
    "company_name" TEXT,
    "legal_name" TEXT,
    "website_url" TEXT,
    "canonical_domain" TEXT,
    "country" TEXT,
    "state" TEXT,
    "city" TEXT,
    "industry" TEXT,
    "sub_industry" TEXT,
    "description" TEXT,
    "company_status" TEXT,
    "sales_stage" TEXT NOT NULL DEFAULT 'NEW',
    "target_market" TEXT,
    "qualification_notes" TEXT,
    "stage_updated_at" TEXT NOT NULL,
    "stage_reason" TEXT,
    "facebook_url" TEXT,
    "instagram_url" TEXT,
    "whatsapp_number" TEXT,
    "whatsapp_click_url" TEXT,
    "phone_number" TEXT,
    "public_email" TEXT,
    "contact_page_url" TEXT,
    "lead_priority" TEXT NOT NULL DEFAULT 'MEDIUM',
    "lead_score" REAL,
    "lead_score_components" TEXT,
    "recommended_services" TEXT,
    "seo_summary_findings" TEXT,
    "gdrive_file_id" TEXT,
    "gdrive_file_url" TEXT,
    "gdrive_synced_at" TEXT,
    "gdrive_sync_status" TEXT NOT NULL DEFAULT 'NOT_SYNCED',
    "lead_owner" TEXT,
    "next_followup_date" TEXT,
    "lead_source" TEXT DEFAULT 'SCRAPER',
    "source_task_id" TEXT REFERENCES "scraper_tasks"("id") ON DELETE SET NULL,
    "tags" TEXT,
    "custom_fields" TEXT,
    "company_size" TEXT,
    "contact_person" TEXT,
    "contact_title" TEXT,
    "linkedin_url" TEXT,
    "domain_rating" REAL,
    "domain_authority" REAL,
    "organic_traffic" REAL,
    "website_status" TEXT DEFAULT 'ACTIVE',
    "technology_stack" TEXT,
    "data_verification_status" TEXT DEFAULT 'VERIFIED',
    "first_discovered_at" TEXT NOT NULL,
    "last_seen_at" TEXT,
    "last_verified_at" TEXT,
    "created_at" TEXT NOT NULL,
    "updated_at" TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS "ix_companies_sales_stage" ON "companies" ("sales_stage");
CREATE UNIQUE INDEX IF NOT EXISTS "ix_companies_canonical_domain" ON "companies" ("canonical_domain");

CREATE TABLE IF NOT EXISTS "export_jobs" (
    "id" TEXT PRIMARY KEY,
    "task_id" TEXT REFERENCES "scraper_tasks"("id") ON DELETE SET NULL,
    "format" TEXT NOT NULL,
    "file_path" TEXT,
    "file_size_bytes" INTEGER NOT NULL DEFAULT 0,
    "record_count" INTEGER NOT NULL DEFAULT 0,
    "filter_criteria" TEXT,
    "status" TEXT NOT NULL DEFAULT 'PENDING',
    "download_url" TEXT,
    "error_message" TEXT,
    "created_at" TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS "ix_export_jobs_task_id" ON "export_jobs" ("task_id");
CREATE INDEX IF NOT EXISTS "ix_export_jobs_created_at" ON "export_jobs" ("created_at");

CREATE TABLE IF NOT EXISTS "import_audit_rows" (
    "id" TEXT PRIMARY KEY,
    "import_batch_id" TEXT NOT NULL REFERENCES "import_batches"("id"),
    "row_index" INTEGER NOT NULL,
    "raw_data" TEXT NOT NULL,
    "status" TEXT NOT NULL,
    "action_taken" TEXT,
    "entity_id" TEXT,
    "errors" TEXT,
    "warnings" TEXT,
    "created_at" TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS "scraper_task_runs" (
    "id" TEXT PRIMARY KEY,
    "task_id" TEXT NOT NULL REFERENCES "scraper_tasks"("id") ON DELETE CASCADE,
    "run_number" INTEGER NOT NULL DEFAULT 1,
    "execution_mode" TEXT NOT NULL DEFAULT 'CLOUD',
    "status" TEXT NOT NULL DEFAULT 'QUEUED',
    "started_at" TEXT,
    "completed_at" TEXT,
    "duration_seconds" REAL NOT NULL DEFAULT 0.0,
    "records_extracted" INTEGER NOT NULL DEFAULT 0,
    "records_saved" INTEGER NOT NULL DEFAULT 0,
    "records_duplicate" INTEGER NOT NULL DEFAULT 0,
    "error_message" TEXT,
    "logs" TEXT NOT NULL,
    "created_at" TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS "ix_scraper_task_runs_status" ON "scraper_task_runs" ("status");
CREATE INDEX IF NOT EXISTS "ix_scraper_task_runs_task_id" ON "scraper_task_runs" ("task_id");
CREATE INDEX IF NOT EXISTS "ix_scraper_task_runs_created_at" ON "scraper_task_runs" ("created_at");

CREATE TABLE IF NOT EXISTS "workflow_runs" (
    "id" TEXT PRIMARY KEY,
    "workflow_id" TEXT NOT NULL REFERENCES "workflows"("id"),
    "trigger_type" TEXT NOT NULL,
    "status" TEXT NOT NULL,
    "current_stage" TEXT,
    "total_companies" INTEGER NOT NULL DEFAULT 0,
    "successful_companies" INTEGER NOT NULL DEFAULT 0,
    "failed_companies" INTEGER NOT NULL DEFAULT 0,
    "skipped_stages" TEXT,
    "retry_counts" TEXT,
    "provider_failures" TEXT,
    "stage_progress" TEXT,
    "parameters" TEXT,
    "error_summary" TEXT,
    "planned_run_at" TEXT,
    "started_at" TEXT,
    "completed_at" TEXT,
    "approved_at" TEXT,
    "approved_by" TEXT
);

CREATE TABLE IF NOT EXISTS "campaign_profiles" (
    "id" TEXT PRIMARY KEY,
    "company_id" TEXT NOT NULL REFERENCES "companies"("id"),
    "target_geography" TEXT,
    "target_industry" TEXT,
    "target_audience" TEXT,
    "topics" TEXT,
    "max_budget" REAL,
    "budget_currency" TEXT NOT NULL DEFAULT 'USD',
    "campaign_objective" TEXT,
    "mandatory_constraints" TEXT,
    "created_at" TEXT NOT NULL,
    "updated_at" TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS "company_competitors" (
    "id" TEXT PRIMARY KEY,
    "company_id" TEXT NOT NULL REFERENCES "companies"("id"),
    "competitor_company_id" TEXT REFERENCES "companies"("id"),
    "competitor_name" TEXT NOT NULL,
    "competitor_domain" TEXT NOT NULL,
    "relevance_score" REAL NOT NULL DEFAULT 0.0,
    "relevance_tier" TEXT NOT NULL DEFAULT 'DIRECT',
    "validation_status" TEXT NOT NULL DEFAULT 'VERIFIED',
    "validation_evidence" TEXT,
    "discovery_method" TEXT NOT NULL DEFAULT 'INDUSTRY_TOPICAL_OVERLAP',
    "is_active" INTEGER NOT NULL DEFAULT True,
    "notes" TEXT,
    "created_at" TEXT NOT NULL,
    "updated_at" TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS "ix_company_competitors_company_id" ON "company_competitors" ("company_id");
CREATE INDEX IF NOT EXISTS "ix_company_competitors_competitor_domain" ON "company_competitors" ("competitor_domain");
CREATE INDEX IF NOT EXISTS "ix_company_competitors_competitor_company_id" ON "company_competitors" ("competitor_company_id");

CREATE TABLE IF NOT EXISTS "company_contacts" (
    "id" TEXT PRIMARY KEY,
    "company_id" TEXT NOT NULL REFERENCES "companies"("id"),
    "email" TEXT,
    "first_name" TEXT,
    "last_name" TEXT,
    "full_name" TEXT,
    "job_title" TEXT,
    "department" TEXT,
    "phone" TEXT,
    "linkedin_url" TEXT,
    "source_type" TEXT NOT NULL,
    "source_url" TEXT,
    "retrieval_timestamp" TEXT NOT NULL,
    "verification_status" TEXT NOT NULL DEFAULT 'UNVERIFIED',
    "confidence" REAL DEFAULT 0.5,
    "is_primary" INTEGER NOT NULL DEFAULT False,
    "opt_out" INTEGER NOT NULL DEFAULT False,
    "opt_out_at" TEXT,
    "notes" TEXT,
    "created_at" TEXT NOT NULL,
    "updated_at" TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS "ix_company_contacts_company_id" ON "company_contacts" ("company_id");
CREATE INDEX IF NOT EXISTS "ix_company_contacts_email" ON "company_contacts" ("email");

CREATE TABLE IF NOT EXISTS "crm_ai_research" (
    "id" TEXT PRIMARY KEY,
    "company_id" TEXT NOT NULL REFERENCES "companies"("id") ON DELETE CASCADE,
    "executive_summary" TEXT,
    "target_market" TEXT,
    "value_proposition" TEXT,
    "seo_weaknesses" TEXT NOT NULL,
    "backlink_opportunities" TEXT NOT NULL,
    "recommended_services" TEXT NOT NULL,
    "growth_opportunities" TEXT NOT NULL,
    "tech_stack_detected" TEXT NOT NULL,
    "confidence_score" REAL NOT NULL DEFAULT 0.85,
    "model_used" TEXT NOT NULL DEFAULT 'gemini-2.5-pro',
    "analyzed_at" TEXT NOT NULL,
    "created_at" TEXT NOT NULL,
    "updated_at" TEXT NOT NULL
);
CREATE UNIQUE INDEX IF NOT EXISTS "ix_crm_ai_research_company_id" ON "crm_ai_research" ("company_id");

CREATE TABLE IF NOT EXISTS "crm_custom_fields" (
    "id" TEXT PRIMARY KEY,
    "company_id" TEXT NOT NULL REFERENCES "companies"("id") ON DELETE CASCADE,
    "field_key" TEXT NOT NULL,
    "field_value" TEXT,
    "field_type" TEXT NOT NULL DEFAULT 'TEXT',
    "created_at" TEXT NOT NULL,
    "updated_at" TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS "ix_crm_custom_fields_field_key" ON "crm_custom_fields" ("field_key");
CREATE INDEX IF NOT EXISTS "ix_crm_custom_fields_company_id" ON "crm_custom_fields" ("company_id");

CREATE TABLE IF NOT EXISTS "crm_feedback_logs" (
    "id" TEXT PRIMARY KEY,
    "company_id" TEXT NOT NULL REFERENCES "companies"("id") ON DELETE CASCADE,
    "action_taken" TEXT NOT NULL,
    "previous_stage" TEXT,
    "new_stage" TEXT,
    "previous_score" REAL,
    "new_score" REAL,
    "feedback_reason" TEXT,
    "actor" TEXT NOT NULL DEFAULT 'human_reviewer',
    "created_at" TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS "ix_crm_feedback_logs_action_taken" ON "crm_feedback_logs" ("action_taken");
CREATE INDEX IF NOT EXISTS "ix_crm_feedback_logs_company_id" ON "crm_feedback_logs" ("company_id");
CREATE INDEX IF NOT EXISTS "ix_crm_feedback_logs_created_at" ON "crm_feedback_logs" ("created_at");

CREATE TABLE IF NOT EXISTS "crm_segment_members" (
    "id" TEXT PRIMARY KEY,
    "segment_id" TEXT NOT NULL REFERENCES "crm_lead_segments"("id") ON DELETE CASCADE,
    "company_id" TEXT NOT NULL REFERENCES "companies"("id") ON DELETE CASCADE,
    "added_at" TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS "ix_crm_segment_members_company_id" ON "crm_segment_members" ("company_id");
CREATE INDEX IF NOT EXISTS "ix_crm_segment_members_segment_id" ON "crm_segment_members" ("segment_id");

CREATE TABLE IF NOT EXISTS "discoveries" (
    "id" TEXT PRIMARY KEY,
    "company_id" TEXT NOT NULL REFERENCES "companies"("id"),
    "source_id" TEXT REFERENCES "sources"("id"),
    "source_url" TEXT,
    "discovery_method" TEXT NOT NULL,
    "discovered_at" TEXT NOT NULL,
    "query" TEXT,
    "job_id" TEXT,
    "confidence" REAL
);

CREATE TABLE IF NOT EXISTS "domains" (
    "id" TEXT PRIMARY KEY,
    "company_id" TEXT NOT NULL REFERENCES "companies"("id"),
    "domain" TEXT NOT NULL,
    "canonical_domain" TEXT NOT NULL,
    "registrar" TEXT,
    "domain_created_at" TEXT,
    "domain_expiry_at" TEXT,
    "first_seen_at" TEXT,
    "last_checked_at" TEXT,
    "status" TEXT NOT NULL,
    "created_at" TEXT NOT NULL,
    "updated_at" TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS "evidence" (
    "id" TEXT PRIMARY KEY,
    "company_id" TEXT NOT NULL REFERENCES "companies"("id"),
    "field_name" TEXT NOT NULL,
    "value" TEXT NOT NULL,
    "source_url" TEXT,
    "source_type" TEXT,
    "provider" TEXT,
    "retrieved_at" TEXT NOT NULL,
    "extraction_method" TEXT,
    "confidence" REAL,
    "verification_status" TEXT NOT NULL,
    "raw_reference" TEXT,
    "created_at" TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS "extracted_records" (
    "id" TEXT PRIMARY KEY,
    "task_id" TEXT REFERENCES "scraper_tasks"("id") ON DELETE SET NULL,
    "run_id" TEXT REFERENCES "scraper_task_runs"("id") ON DELETE SET NULL,
    "record_hash" TEXT NOT NULL,
    "raw_data" TEXT NOT NULL,
    "cleaned_data" TEXT NOT NULL,
    "company_name" TEXT,
    "website" TEXT,
    "domain" TEXT,
    "industry" TEXT,
    "category" TEXT,
    "country" TEXT,
    "city" TEXT,
    "email" TEXT,
    "phone" TEXT,
    "address" TEXT,
    "description" TEXT,
    "social_profiles" TEXT,
    "source_url" TEXT,
    "discovery_source" TEXT NOT NULL DEFAULT 'SCRAPER',
    "validation_status" TEXT NOT NULL DEFAULT 'VALID',
    "quality_score" REAL NOT NULL DEFAULT 100.0,
    "quality_status" TEXT NOT NULL DEFAULT 'HIGH',
    "validation_details" TEXT,
    "is_duplicate" INTEGER NOT NULL DEFAULT False,
    "created_at" TEXT NOT NULL,
    "updated_at" TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS "ix_extracted_records_created_at" ON "extracted_records" ("created_at");
CREATE INDEX IF NOT EXISTS "ix_extracted_records_discovery_source" ON "extracted_records" ("discovery_source");
CREATE INDEX IF NOT EXISTS "ix_extracted_records_is_duplicate" ON "extracted_records" ("is_duplicate");
CREATE INDEX IF NOT EXISTS "ix_extracted_records_country" ON "extracted_records" ("country");
CREATE INDEX IF NOT EXISTS "ix_extracted_records_run_id" ON "extracted_records" ("run_id");
CREATE INDEX IF NOT EXISTS "ix_extracted_records_company_name" ON "extracted_records" ("company_name");
CREATE INDEX IF NOT EXISTS "ix_extracted_records_record_hash" ON "extracted_records" ("record_hash");
CREATE INDEX IF NOT EXISTS "ix_extracted_records_task_id" ON "extracted_records" ("task_id");
CREATE INDEX IF NOT EXISTS "ix_extracted_records_validation_status" ON "extracted_records" ("validation_status");
CREATE INDEX IF NOT EXISTS "ix_extracted_records_industry" ON "extracted_records" ("industry");
CREATE INDEX IF NOT EXISTS "ix_extracted_records_domain" ON "extracted_records" ("domain");

CREATE TABLE IF NOT EXISTS "google_drive_sync_jobs" (
    "id" TEXT PRIMARY KEY,
    "company_id" TEXT NOT NULL REFERENCES "companies"("id"),
    "status" TEXT NOT NULL DEFAULT 'PENDING',
    "sync_type" TEXT NOT NULL DEFAULT 'AUTOMATIC',
    "resource_id" TEXT,
    "resource_url" TEXT,
    "destination_folder" TEXT,
    "attempts" INTEGER NOT NULL DEFAULT 0,
    "error_message" TEXT,
    "synced_at" TEXT,
    "created_at" TEXT NOT NULL,
    "updated_at" TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS "ix_google_drive_sync_jobs_status" ON "google_drive_sync_jobs" ("status");
CREATE INDEX IF NOT EXISTS "ix_google_drive_sync_jobs_company_id" ON "google_drive_sync_jobs" ("company_id");

CREATE TABLE IF NOT EXISTS "health_assessments" (
    "id" TEXT PRIMARY KEY,
    "company_id" TEXT NOT NULL REFERENCES "companies"("id"),
    "health_score" REAL,
    "health_status" TEXT NOT NULL,
    "health_signals" TEXT,
    "methodology_version" TEXT NOT NULL,
    "assessed_at" TEXT NOT NULL,
    "created_at" TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS "historical_snapshots" (
    "id" TEXT PRIMARY KEY,
    "company_id" TEXT NOT NULL REFERENCES "companies"("id"),
    "metric_name" TEXT NOT NULL,
    "metric_value" TEXT NOT NULL,
    "provider" TEXT,
    "observed_at" TEXT NOT NULL,
    "confidence" REAL,
    "source_url" TEXT,
    "created_at" TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS "jobs" (
    "id" TEXT PRIMARY KEY,
    "workflow_run_id" TEXT REFERENCES "workflow_runs"("id"),
    "job_type" TEXT NOT NULL,
    "status" TEXT NOT NULL,
    "requested_count" INTEGER,
    "discovered_count" INTEGER,
    "validated_count" INTEGER,
    "stored_count" INTEGER,
    "duplicate_count" INTEGER,
    "failed_count" INTEGER,
    "processed_count" INTEGER,
    "successful_count" INTEGER,
    "partial_count" INTEGER,
    "provider_error_count" INTEGER,
    "metrics_created" INTEGER,
    "metrics_skipped" INTEGER,
    "parameters" TEXT,
    "error_message" TEXT,
    "created_at" TEXT NOT NULL,
    "started_at" TEXT,
    "completed_at" TEXT,
    "updated_at" TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS "matching_runs" (
    "id" TEXT PRIMARY KEY,
    "company_id" TEXT NOT NULL REFERENCES "companies"("id"),
    "profile_snapshot" TEXT NOT NULL,
    "scoring_model_version" TEXT NOT NULL,
    "status" TEXT NOT NULL,
    "total_eligible" INTEGER NOT NULL DEFAULT 0,
    "total_excluded" INTEGER NOT NULL DEFAULT 0,
    "error_message" TEXT,
    "started_at" TEXT NOT NULL,
    "completed_at" TEXT
);

CREATE TABLE IF NOT EXISTS "media_plans" (
    "id" TEXT PRIMARY KEY,
    "company_id" TEXT NOT NULL REFERENCES "companies"("id"),
    "name" TEXT NOT NULL DEFAULT 'Draft Media Plan',
    "status" TEXT NOT NULL DEFAULT 'DRAFT',
    "notes" TEXT,
    "created_at" TEXT NOT NULL,
    "updated_at" TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS "opportunity_profiles" (
    "id" TEXT PRIMARY KEY,
    "company_id" TEXT NOT NULL REFERENCES "companies"("id"),
    "recommended_service" TEXT NOT NULL,
    "opportunity_score" REAL NOT NULL,
    "supporting_evidence" TEXT,
    "identified_problems" TEXT,
    "confidence_level" REAL NOT NULL,
    "data_freshness" TEXT NOT NULL,
    "missing_information" TEXT,
    "recommended_next_action" TEXT,
    "methodology_version" TEXT NOT NULL,
    "calculation_timestamp" TEXT NOT NULL,
    "created_at" TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS "portal_users" (
    "id" TEXT PRIMARY KEY,
    "email" TEXT NOT NULL,
    "hashed_password" TEXT NOT NULL,
    "full_name" TEXT NOT NULL,
    "role" TEXT NOT NULL DEFAULT 'CLIENT_USER',
    "company_id" TEXT REFERENCES "companies"("id"),
    "is_active" INTEGER NOT NULL DEFAULT True,
    "last_login_at" TEXT,
    "created_at" TEXT NOT NULL,
    "updated_at" TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS "ix_portal_users_company_id" ON "portal_users" ("company_id");
CREATE INDEX IF NOT EXISTS "ix_portal_users_is_active" ON "portal_users" ("is_active");
CREATE UNIQUE INDEX IF NOT EXISTS "ix_portal_users_email" ON "portal_users" ("email");
CREATE INDEX IF NOT EXISTS "ix_portal_users_role" ON "portal_users" ("role");

CREATE TABLE IF NOT EXISTS "publisher_records" (
    "id" TEXT PRIMARY KEY,
    "company_id" TEXT NOT NULL REFERENCES "companies"("id"),
    "original_submitted_url" TEXT,
    "publisher_name" TEXT,
    "audience_focus" TEXT,
    "editorial_attributes" TEXT,
    "status" TEXT NOT NULL DEFAULT 'UNVERIFIED',
    "created_at" TEXT NOT NULL,
    "updated_at" TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS "report_schedules" (
    "id" TEXT PRIMARY KEY,
    "company_id" TEXT NOT NULL REFERENCES "companies"("id"),
    "report_type" TEXT NOT NULL DEFAULT 'MONTHLY_PERFORMANCE',
    "frequency" TEXT NOT NULL DEFAULT 'MONTHLY',
    "day_of_month" INTEGER NOT NULL DEFAULT 1,
    "day_of_week" INTEGER NOT NULL DEFAULT 0,
    "time_of_day" TEXT NOT NULL DEFAULT '09:00',
    "time_zone" TEXT NOT NULL DEFAULT 'UTC',
    "recipients" TEXT,
    "is_active" INTEGER NOT NULL DEFAULT True,
    "requires_approval" INTEGER NOT NULL DEFAULT True,
    "last_generated_at" TEXT,
    "next_run_at" TEXT,
    "created_at" TEXT NOT NULL,
    "updated_at" TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS "ix_report_schedules_company_id" ON "report_schedules" ("company_id");
CREATE INDEX IF NOT EXISTS "ix_report_schedules_is_active" ON "report_schedules" ("is_active");

CREATE TABLE IF NOT EXISTS "risk_assessments" (
    "id" TEXT PRIMARY KEY,
    "company_id" TEXT NOT NULL REFERENCES "companies"("id"),
    "risk_score" REAL,
    "risk_level" TEXT NOT NULL,
    "risk_signals" TEXT,
    "confidence" REAL,
    "methodology_version" TEXT NOT NULL,
    "assessed_at" TEXT NOT NULL,
    "created_at" TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS "sales_briefs" (
    "id" TEXT PRIMARY KEY,
    "company_id" TEXT NOT NULL REFERENCES "companies"("id"),
    "title" TEXT NOT NULL,
    "company_overview" TEXT NOT NULL,
    "seo_findings_summary" TEXT NOT NULL,
    "top_opportunities" TEXT,
    "recommended_services" TEXT,
    "matched_publishers" TEXT,
    "data_gaps" TEXT,
    "discovery_questions" TEXT,
    "recommended_next_action" TEXT,
    "full_brief_markdown" TEXT NOT NULL,
    "is_customized" INTEGER NOT NULL DEFAULT False,
    "last_edited_by" TEXT,
    "last_edited_at" TEXT,
    "created_at" TEXT NOT NULL,
    "updated_at" TEXT NOT NULL
);
CREATE UNIQUE INDEX IF NOT EXISTS "ix_sales_briefs_company_id" ON "sales_briefs" ("company_id");

CREATE TABLE IF NOT EXISTS "sales_intelligence_scores" (
    "id" TEXT PRIMARY KEY,
    "company_id" TEXT NOT NULL REFERENCES "companies"("id"),
    "scoring_version" TEXT NOT NULL DEFAULT 'v3.0.0',
    "overall_priority_score" REAL NOT NULL DEFAULT 0.0,
    "seo_severity_score" REAL NOT NULL DEFAULT 0.0,
    "service_fit_score" REAL NOT NULL DEFAULT 0.0,
    "publisher_fit_score" REAL NOT NULL DEFAULT 0.0,
    "business_fit_score" REAL NOT NULL DEFAULT 0.0,
    "evidence_confidence_score" REAL NOT NULL DEFAULT 0.0,
    "data_completeness" REAL NOT NULL DEFAULT 0.0,
    "primary_recommended_service" TEXT,
    "recommended_services" TEXT,
    "positive_indicators" TEXT,
    "limitations" TEXT,
    "missing_information" TEXT,
    "component_weights" TEXT,
    "recommended_next_action" TEXT,
    "review_status" TEXT NOT NULL DEFAULT 'UNREVIEWED',
    "human_override_score" REAL,
    "human_override_reason" TEXT,
    "human_override_by" TEXT,
    "human_override_at" TEXT,
    "evaluated_at" TEXT NOT NULL,
    "created_at" TEXT NOT NULL,
    "updated_at" TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS "ix_sales_intelligence_scores_review_status" ON "sales_intelligence_scores" ("review_status");
CREATE INDEX IF NOT EXISTS "ix_sales_intelligence_scores_overall_priority_score" ON "sales_intelligence_scores" ("overall_priority_score");
CREATE UNIQUE INDEX IF NOT EXISTS "ix_sales_intelligence_scores_company_id" ON "sales_intelligence_scores" ("company_id");

CREATE TABLE IF NOT EXISTS "sales_opportunities" (
    "id" TEXT PRIMARY KEY,
    "company_id" TEXT NOT NULL REFERENCES "companies"("id"),
    "category" TEXT NOT NULL,
    "title" TEXT NOT NULL,
    "description" TEXT NOT NULL,
    "severity" TEXT NOT NULL DEFAULT 'MEDIUM',
    "impact_rationale" TEXT NOT NULL,
    "confidence" REAL NOT NULL DEFAULT 1.0,
    "recommended_service" TEXT NOT NULL,
    "supporting_evidence" TEXT,
    "status" TEXT NOT NULL DEFAULT 'ACTIVE',
    "detection_rule" TEXT NOT NULL,
    "detection_timestamp" TEXT NOT NULL,
    "created_at" TEXT NOT NULL,
    "updated_at" TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS "ix_sales_opportunities_company_id" ON "sales_opportunities" ("company_id");
CREATE INDEX IF NOT EXISTS "ix_sales_opportunities_status" ON "sales_opportunities" ("status");
CREATE INDEX IF NOT EXISTS "ix_sales_opportunities_category" ON "sales_opportunities" ("category");
CREATE INDEX IF NOT EXISTS "ix_sales_opportunities_severity" ON "sales_opportunities" ("severity");

CREATE TABLE IF NOT EXISTS "seo_metrics" (
    "id" TEXT PRIMARY KEY,
    "company_id" TEXT NOT NULL REFERENCES "companies"("id"),
    "metric_name" TEXT NOT NULL,
    "metric_value" REAL,
    "unit" TEXT,
    "provider" TEXT NOT NULL,
    "domain" TEXT,
    "provider_metric_name" TEXT,
    "provider_endpoint" TEXT,
    "request_id" TEXT,
    "source_url" TEXT,
    "retrieved_at" TEXT NOT NULL,
    "confidence" REAL,
    "verification_status" TEXT NOT NULL,
    "raw_reference" TEXT,
    "created_at" TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS "shortlists" (
    "id" TEXT PRIMARY KEY,
    "company_id" TEXT NOT NULL REFERENCES "companies"("id"),
    "name" TEXT NOT NULL,
    "created_at" TEXT NOT NULL,
    "updated_at" TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS "social_profiles" (
    "id" TEXT PRIMARY KEY,
    "company_id" TEXT NOT NULL REFERENCES "companies"("id"),
    "platform" TEXT NOT NULL,
    "profile_url" TEXT NOT NULL,
    "source_url" TEXT,
    "verification_method" TEXT NOT NULL,
    "confidence" REAL,
    "verification_status" TEXT NOT NULL,
    "discovered_at" TEXT NOT NULL,
    "last_verified_at" TEXT,
    "created_at" TEXT NOT NULL,
    "updated_at" TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS "website_scans" (
    "id" TEXT PRIMARY KEY,
    "company_id" TEXT NOT NULL REFERENCES "companies"("id"),
    "url" TEXT NOT NULL,
    "http_status" INTEGER,
    "https_enabled" INTEGER,
    "final_url" TEXT,
    "redirect_chain" TEXT,
    "title" TEXT,
    "meta_description" TEXT,
    "canonical_url" TEXT,
    "robots_meta" TEXT,
    "viewport" TEXT,
    "language" TEXT,
    "charset" TEXT,
    "h1" TEXT,
    "h2" TEXT,
    "open_graph" TEXT,
    "twitter_card" TEXT,
    "robots_txt_status" TEXT,
    "sitemap_status" TEXT,
    "schema_detected" TEXT,
    "cms_detected" TEXT,
    "technology_signals" TEXT,
    "scanned_at" TEXT NOT NULL,
    "scan_status" TEXT NOT NULL,
    "error_message" TEXT,
    "created_at" TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS "agent_runs" (
    "id" TEXT PRIMARY KEY,
    "agent_name" TEXT NOT NULL,
    "job_id" TEXT REFERENCES "jobs"("id"),
    "status" TEXT NOT NULL,
    "input_reference" TEXT,
    "output_reference" TEXT,
    "started_at" TEXT,
    "completed_at" TEXT,
    "error_message" TEXT,
    "created_at" TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS "ai_extraction_runs" (
    "id" TEXT PRIMARY KEY,
    "company_id" TEXT NOT NULL REFERENCES "companies"("id"),
    "job_id" TEXT REFERENCES "jobs"("id"),
    "provider" TEXT NOT NULL,
    "model" TEXT NOT NULL,
    "prompt_version" TEXT NOT NULL,
    "schema_version" TEXT NOT NULL,
    "status" TEXT NOT NULL,
    "total_tokens" INTEGER,
    "estimated_cost" REAL,
    "error_message" TEXT,
    "started_at" TEXT NOT NULL,
    "completed_at" TEXT
);

CREATE TABLE IF NOT EXISTS "client_invitations" (
    "id" TEXT PRIMARY KEY,
    "company_id" TEXT NOT NULL REFERENCES "companies"("id"),
    "email" TEXT NOT NULL,
    "invitation_token" TEXT NOT NULL,
    "role" TEXT NOT NULL DEFAULT 'CLIENT_USER',
    "invited_by_user_id" TEXT REFERENCES "portal_users"("id"),
    "status" TEXT NOT NULL DEFAULT 'PENDING',
    "expires_at" TEXT NOT NULL,
    "accepted_at" TEXT,
    "created_at" TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS "ix_client_invitations_email" ON "client_invitations" ("email");
CREATE INDEX IF NOT EXISTS "ix_client_invitations_company_id" ON "client_invitations" ("company_id");
CREATE UNIQUE INDEX IF NOT EXISTS "ix_client_invitations_invitation_token" ON "client_invitations" ("invitation_token");
CREATE INDEX IF NOT EXISTS "ix_client_invitations_status" ON "client_invitations" ("status");

CREATE TABLE IF NOT EXISTS "client_reports" (
    "id" TEXT PRIMARY KEY,
    "company_id" TEXT NOT NULL REFERENCES "companies"("id"),
    "title" TEXT NOT NULL,
    "report_type" TEXT NOT NULL DEFAULT 'MONTHLY_PERFORMANCE',
    "reporting_period_start" TEXT,
    "reporting_period_end" TEXT,
    "status" TEXT NOT NULL DEFAULT 'DRAFT',
    "approval_status" TEXT NOT NULL DEFAULT 'UNAPPROVED',
    "approved_by_user_id" TEXT REFERENCES "portal_users"("id"),
    "approved_at" TEXT,
    "branding" TEXT,
    "sections" TEXT,
    "summary_metrics" TEXT,
    "delivery_status" TEXT NOT NULL DEFAULT 'NOT_DELIVERED',
    "generated_by" TEXT NOT NULL DEFAULT 'manual_operator',
    "data_limitations" TEXT,
    "export_formats" TEXT,
    "created_at" TEXT NOT NULL,
    "updated_at" TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS "ix_client_reports_status" ON "client_reports" ("status");
CREATE INDEX IF NOT EXISTS "ix_client_reports_report_type" ON "client_reports" ("report_type");
CREATE INDEX IF NOT EXISTS "ix_client_reports_approval_status" ON "client_reports" ("approval_status");
CREATE INDEX IF NOT EXISTS "ix_client_reports_company_id" ON "client_reports" ("company_id");

CREATE TABLE IF NOT EXISTS "competitive_analysis_runs" (
    "id" TEXT PRIMARY KEY,
    "company_id" TEXT NOT NULL REFERENCES "companies"("id"),
    "competitor_id" TEXT NOT NULL REFERENCES "company_competitors"("id"),
    "status" TEXT NOT NULL DEFAULT 'COMPLETED',
    "prospect_scan_id" TEXT REFERENCES "website_scans"("id"),
    "competitor_scan_id" TEXT REFERENCES "website_scans"("id"),
    "summary_findings" TEXT,
    "content_gaps" TEXT,
    "technical_gaps" TEXT,
    "internal_linking_gaps" TEXT,
    "backlink_gaps" TEXT,
    "publisher_opportunities" TEXT,
    "prioritized_recommendations" TEXT,
    "data_limitations" TEXT,
    "analyzed_at" TEXT NOT NULL,
    "created_at" TEXT NOT NULL,
    "updated_at" TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS "ix_competitive_analysis_runs_status" ON "competitive_analysis_runs" ("status");
CREATE INDEX IF NOT EXISTS "ix_competitive_analysis_runs_company_id" ON "competitive_analysis_runs" ("company_id");
CREATE INDEX IF NOT EXISTS "ix_competitive_analysis_runs_competitor_id" ON "competitive_analysis_runs" ("competitor_id");

CREATE TABLE IF NOT EXISTS "crm_deals" (
    "id" TEXT PRIMARY KEY,
    "company_id" TEXT NOT NULL REFERENCES "companies"("id"),
    "contact_id" TEXT REFERENCES "company_contacts"("id"),
    "deal_name" TEXT NOT NULL,
    "service_category" TEXT NOT NULL DEFAULT 'FULL_SERVICE',
    "stage" TEXT NOT NULL DEFAULT 'DISCOVERY',
    "estimated_value" REAL NOT NULL DEFAULT 0.0,
    "proposed_value" REAL,
    "closed_amount" REAL,
    "currency" TEXT NOT NULL DEFAULT 'USD',
    "expected_close_date" TEXT,
    "actual_close_date" TEXT,
    "outcome" TEXT,
    "loss_reason" TEXT,
    "win_reason" TEXT,
    "media_plan_id" TEXT REFERENCES "media_plans"("id"),
    "campaign_id" TEXT REFERENCES "outreach_campaigns"("id"),
    "cost_amount" REAL,
    "invoice_status" TEXT,
    "invoiced_amount" REAL,
    "paid_amount" REAL,
    "discount_amount" REAL DEFAULT 0.0,
    "tax_amount" REAL DEFAULT 0.0,
    "refunded_amount" REAL DEFAULT 0.0,
    "notes" TEXT,
    "created_at" TEXT NOT NULL,
    "updated_at" TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS "ix_crm_deals_stage" ON "crm_deals" ("stage");
CREATE INDEX IF NOT EXISTS "ix_crm_deals_company_id" ON "crm_deals" ("company_id");

CREATE TABLE IF NOT EXISTS "job_results" (
    "id" TEXT PRIMARY KEY,
    "job_id" TEXT NOT NULL REFERENCES "jobs"("id"),
    "company_id" TEXT REFERENCES "companies"("id"),
    "status" TEXT NOT NULL,
    "stage" TEXT,
    "error_message" TEXT,
    "created_at" TEXT NOT NULL,
    "updated_at" TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS "match_results" (
    "id" TEXT PRIMARY KEY,
    "matching_run_id" TEXT NOT NULL REFERENCES "matching_runs"("id"),
    "publisher_id" TEXT NOT NULL REFERENCES "publisher_records"("id"),
    "overall_score" REAL NOT NULL,
    "rank" INTEGER NOT NULL,
    "component_scores" TEXT NOT NULL,
    "reasons" TEXT NOT NULL,
    "warnings" TEXT,
    "created_at" TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS "outreach_drafts" (
    "id" TEXT PRIMARY KEY,
    "campaign_id" TEXT REFERENCES "outreach_campaigns"("id"),
    "company_id" TEXT NOT NULL REFERENCES "companies"("id"),
    "contact_id" TEXT REFERENCES "company_contacts"("id"),
    "recipient_email" TEXT NOT NULL,
    "recipient_name" TEXT,
    "subject_line" TEXT NOT NULL,
    "body_text" TEXT NOT NULL,
    "body_html" TEXT,
    "call_to_action" TEXT,
    "prospect_summary" TEXT,
    "evidence_citations" TEXT,
    "status" TEXT NOT NULL DEFAULT 'DRAFT',
    "approval_status" TEXT NOT NULL DEFAULT 'UNAPPROVED',
    "approved_by" TEXT,
    "approved_at" TEXT,
    "rejection_reason" TEXT,
    "is_follow_up" INTEGER NOT NULL DEFAULT False,
    "sequence_step" INTEGER NOT NULL DEFAULT 1,
    "parent_draft_id" TEXT REFERENCES "outreach_drafts"("id"),
    "scheduled_send_at" TEXT,
    "sent_at" TEXT,
    "error_message" TEXT,
    "created_at" TEXT NOT NULL,
    "updated_at" TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS "ix_outreach_drafts_recipient_email" ON "outreach_drafts" ("recipient_email");
CREATE INDEX IF NOT EXISTS "ix_outreach_drafts_company_id" ON "outreach_drafts" ("company_id");

CREATE TABLE IF NOT EXISTS "portal_audit_logs" (
    "id" TEXT PRIMARY KEY,
    "user_id" TEXT REFERENCES "portal_users"("id"),
    "company_id" TEXT REFERENCES "companies"("id"),
    "action" TEXT NOT NULL,
    "resource_type" TEXT NOT NULL,
    "resource_id" TEXT,
    "details" TEXT,
    "ip_address" TEXT,
    "timestamp" TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS "ix_portal_audit_logs_company_id" ON "portal_audit_logs" ("company_id");
CREATE INDEX IF NOT EXISTS "ix_portal_audit_logs_user_id" ON "portal_audit_logs" ("user_id");
CREATE INDEX IF NOT EXISTS "ix_portal_audit_logs_timestamp" ON "portal_audit_logs" ("timestamp");
CREATE INDEX IF NOT EXISTS "ix_portal_audit_logs_action" ON "portal_audit_logs" ("action");

CREATE TABLE IF NOT EXISTS "provider_usage" (
    "id" TEXT PRIMARY KEY,
    "provider" TEXT NOT NULL,
    "job_id" TEXT REFERENCES "jobs"("id"),
    "company_id" TEXT REFERENCES "companies"("id"),
    "request_count" INTEGER NOT NULL DEFAULT 0,
    "estimated_units" REAL,
    "actual_units" REAL,
    "endpoint" TEXT,
    "timestamp" TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS "publisher_observations" (
    "id" TEXT PRIMARY KEY,
    "publisher_id" TEXT NOT NULL REFERENCES "publisher_records"("id"),
    "price" REAL,
    "currency" TEXT,
    "pricing_model" TEXT,
    "metric_da" REAL,
    "metric_dr" REAL,
    "metric_traffic" REAL,
    "observation_timestamp" TEXT NOT NULL,
    "source_name" TEXT,
    "import_batch_id" TEXT REFERENCES "import_batches"("id"),
    "verification_status" TEXT NOT NULL DEFAULT 'UNVERIFIED',
    "created_at" TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS "publisher_quality_findings" (
    "id" TEXT PRIMARY KEY,
    "publisher_id" TEXT NOT NULL REFERENCES "publisher_records"("id"),
    "issue_type" TEXT NOT NULL,
    "field_name" TEXT NOT NULL,
    "severity" TEXT NOT NULL DEFAULT 'MEDIUM',
    "title" TEXT NOT NULL,
    "description" TEXT NOT NULL,
    "evidence" TEXT,
    "recommended_action" TEXT NOT NULL,
    "status" TEXT NOT NULL DEFAULT 'OPEN',
    "resolution_action" TEXT,
    "resolution_notes" TEXT,
    "resolved_by" TEXT,
    "resolved_at" TEXT,
    "created_at" TEXT NOT NULL,
    "updated_at" TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS "ix_publisher_quality_findings_publisher_id" ON "publisher_quality_findings" ("publisher_id");
CREATE INDEX IF NOT EXISTS "ix_publisher_quality_findings_issue_type" ON "publisher_quality_findings" ("issue_type");
CREATE INDEX IF NOT EXISTS "ix_publisher_quality_findings_status" ON "publisher_quality_findings" ("status");
CREATE INDEX IF NOT EXISTS "ix_publisher_quality_findings_severity" ON "publisher_quality_findings" ("severity");

CREATE TABLE IF NOT EXISTS "publisher_quality_scores" (
    "id" TEXT PRIMARY KEY,
    "publisher_id" TEXT NOT NULL REFERENCES "publisher_records"("id"),
    "overall_quality_score" REAL NOT NULL DEFAULT 100.0,
    "completeness_score" REAL NOT NULL DEFAULT 100.0,
    "freshness_score" REAL NOT NULL DEFAULT 100.0,
    "validity_score" REAL NOT NULL DEFAULT 100.0,
    "consistency_score" REAL NOT NULL DEFAULT 100.0,
    "price_freshness_status" TEXT NOT NULL DEFAULT 'UNKNOWN',
    "metrics_freshness_status" TEXT NOT NULL DEFAULT 'UNKNOWN',
    "site_freshness_status" TEXT NOT NULL DEFAULT 'UNKNOWN',
    "last_price_checked_at" TEXT,
    "last_metrics_checked_at" TEXT,
    "last_site_checked_at" TEXT,
    "open_issues_count" INTEGER NOT NULL DEFAULT 0,
    "critical_issues_count" INTEGER NOT NULL DEFAULT 0,
    "has_duplicates" INTEGER NOT NULL DEFAULT False,
    "has_conflicts" INTEGER NOT NULL DEFAULT False,
    "last_audited_at" TEXT NOT NULL,
    "created_at" TEXT NOT NULL,
    "updated_at" TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS "ix_publisher_quality_scores_overall_quality_score" ON "publisher_quality_scores" ("overall_quality_score");
CREATE UNIQUE INDEX IF NOT EXISTS "ix_publisher_quality_scores_publisher_id" ON "publisher_quality_scores" ("publisher_id");

CREATE TABLE IF NOT EXISTS "publisher_refresh_logs" (
    "id" TEXT PRIMARY KEY,
    "publisher_id" TEXT NOT NULL REFERENCES "publisher_records"("id"),
    "target_field" TEXT NOT NULL,
    "provider_attempted" TEXT NOT NULL,
    "status" TEXT NOT NULL,
    "details" TEXT,
    "error_message" TEXT,
    "initiated_by" TEXT NOT NULL DEFAULT 'system_audit',
    "created_at" TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS "ix_publisher_refresh_logs_publisher_id" ON "publisher_refresh_logs" ("publisher_id");
CREATE INDEX IF NOT EXISTS "ix_publisher_refresh_logs_status" ON "publisher_refresh_logs" ("status");

CREATE TABLE IF NOT EXISTS "social_message_logs" (
    "id" TEXT PRIMARY KEY,
    "company_id" TEXT NOT NULL REFERENCES "companies"("id"),
    "contact_id" TEXT REFERENCES "company_contacts"("id"),
    "channel" TEXT NOT NULL,
    "direction" TEXT NOT NULL DEFAULT 'OUTBOUND',
    "recipient_identifier" TEXT NOT NULL,
    "sender_account" TEXT,
    "message_text" TEXT NOT NULL,
    "template_name" TEXT,
    "status" TEXT NOT NULL DEFAULT 'PREPARED',
    "api_message_id" TEXT,
    "click_to_chat_url" TEXT,
    "error_details" TEXT,
    "explicit_user_confirmed" INTEGER NOT NULL DEFAULT False,
    "created_at" TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS "ix_social_message_logs_company_id" ON "social_message_logs" ("company_id");
CREATE INDEX IF NOT EXISTS "ix_social_message_logs_status" ON "social_message_logs" ("status");
CREATE INDEX IF NOT EXISTS "ix_social_message_logs_created_at" ON "social_message_logs" ("created_at");
CREATE INDEX IF NOT EXISTS "ix_social_message_logs_channel" ON "social_message_logs" ("channel");

CREATE TABLE IF NOT EXISTS "ai_observations" (
    "id" TEXT PRIMARY KEY,
    "company_id" TEXT NOT NULL REFERENCES "companies"("id"),
    "extraction_run_id" TEXT NOT NULL REFERENCES "ai_extraction_runs"("id"),
    "attribute_name" TEXT NOT NULL,
    "attribute_value" TEXT,
    "evidence_text" TEXT,
    "source_url" TEXT,
    "confidence" REAL,
    "verification_status" TEXT NOT NULL,
    "validation_errors" TEXT,
    "created_at" TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS "crm_activities" (
    "id" TEXT PRIMARY KEY,
    "company_id" TEXT NOT NULL REFERENCES "companies"("id"),
    "deal_id" TEXT REFERENCES "crm_deals"("id"),
    "contact_id" TEXT REFERENCES "company_contacts"("id"),
    "activity_type" TEXT NOT NULL,
    "actor" TEXT NOT NULL DEFAULT 'human_reviewer',
    "title" TEXT NOT NULL,
    "details" TEXT,
    "created_at" TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS "ix_crm_activities_company_id" ON "crm_activities" ("company_id");
CREATE INDEX IF NOT EXISTS "ix_crm_activities_created_at" ON "crm_activities" ("created_at");

CREATE TABLE IF NOT EXISTS "crm_notes" (
    "id" TEXT PRIMARY KEY,
    "company_id" TEXT NOT NULL REFERENCES "companies"("id"),
    "deal_id" TEXT REFERENCES "crm_deals"("id"),
    "author" TEXT NOT NULL DEFAULT 'human_reviewer',
    "content" TEXT NOT NULL,
    "created_at" TEXT NOT NULL,
    "updated_at" TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS "ix_crm_notes_company_id" ON "crm_notes" ("company_id");

CREATE TABLE IF NOT EXISTS "crm_tasks" (
    "id" TEXT PRIMARY KEY,
    "company_id" TEXT NOT NULL REFERENCES "companies"("id"),
    "contact_id" TEXT REFERENCES "company_contacts"("id"),
    "deal_id" TEXT REFERENCES "crm_deals"("id"),
    "title" TEXT NOT NULL,
    "description" TEXT,
    "task_type" TEXT NOT NULL DEFAULT 'FOLLOW_UP',
    "priority" TEXT NOT NULL DEFAULT 'MEDIUM',
    "status" TEXT NOT NULL DEFAULT 'PENDING',
    "due_date" TEXT,
    "completed_at" TEXT,
    "completed_by" TEXT,
    "completion_notes" TEXT,
    "idempotency_key" TEXT,
    "created_at" TEXT NOT NULL,
    "updated_at" TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS "ix_crm_tasks_due_date" ON "crm_tasks" ("due_date");
CREATE INDEX IF NOT EXISTS "ix_crm_tasks_status" ON "crm_tasks" ("status");
CREATE INDEX IF NOT EXISTS "ix_crm_tasks_idempotency_key" ON "crm_tasks" ("idempotency_key");
CREATE INDEX IF NOT EXISTS "ix_crm_tasks_company_id" ON "crm_tasks" ("company_id");

CREATE TABLE IF NOT EXISTS "errors" (
    "id" TEXT PRIMARY KEY,
    "job_id" TEXT REFERENCES "jobs"("id"),
    "company_id" TEXT REFERENCES "companies"("id"),
    "agent_run_id" TEXT REFERENCES "agent_runs"("id"),
    "error_type" TEXT NOT NULL,
    "message" TEXT NOT NULL,
    "details" TEXT,
    "occurred_at" TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS "media_plan_items" (
    "id" TEXT PRIMARY KEY,
    "media_plan_id" TEXT NOT NULL REFERENCES "media_plans"("id"),
    "publisher_id" TEXT NOT NULL REFERENCES "publisher_records"("id"),
    "match_result_id" TEXT REFERENCES "match_results"("id"),
    "proposed_price" REAL,
    "proposed_currency" TEXT,
    "notes" TEXT,
    "created_at" TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS "outreach_messages" (
    "id" TEXT PRIMARY KEY,
    "draft_id" TEXT NOT NULL REFERENCES "outreach_drafts"("id"),
    "campaign_id" TEXT REFERENCES "outreach_campaigns"("id"),
    "company_id" TEXT NOT NULL REFERENCES "companies"("id"),
    "contact_id" TEXT REFERENCES "company_contacts"("id"),
    "provider" TEXT NOT NULL,
    "provider_message_id" TEXT,
    "provider_thread_id" TEXT,
    "sender_email" TEXT NOT NULL,
    "recipient_email" TEXT NOT NULL,
    "subject_line" TEXT NOT NULL,
    "body_text" TEXT NOT NULL,
    "status" TEXT NOT NULL DEFAULT 'SENT',
    "delivery_error" TEXT,
    "sent_at" TEXT NOT NULL,
    "opened_at" TEXT,
    "replied_at" TEXT,
    "bounced_at" TEXT,
    "unsubscribed_at" TEXT,
    "created_at" TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS "ix_outreach_messages_company_id" ON "outreach_messages" ("company_id");
CREATE INDEX IF NOT EXISTS "ix_outreach_messages_recipient_email" ON "outreach_messages" ("recipient_email");

CREATE TABLE IF NOT EXISTS "report_delivery_logs" (
    "id" TEXT PRIMARY KEY,
    "report_id" TEXT NOT NULL REFERENCES "client_reports"("id"),
    "recipient_email" TEXT NOT NULL,
    "delivery_channel" TEXT NOT NULL DEFAULT 'EMAIL',
    "idempotency_key" TEXT NOT NULL,
    "status" TEXT NOT NULL DEFAULT 'PENDING',
    "sent_at" TEXT,
    "error_message" TEXT,
    "created_at" TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS "ix_report_delivery_logs_report_id" ON "report_delivery_logs" ("report_id");
CREATE UNIQUE INDEX IF NOT EXISTS "ix_report_delivery_logs_idempotency_key" ON "report_delivery_logs" ("idempotency_key");
CREATE INDEX IF NOT EXISTS "ix_report_delivery_logs_recipient_email" ON "report_delivery_logs" ("recipient_email");
CREATE INDEX IF NOT EXISTS "ix_report_delivery_logs_status" ON "report_delivery_logs" ("status");

CREATE TABLE IF NOT EXISTS "shortlist_items" (
    "id" TEXT PRIMARY KEY,
    "shortlist_id" TEXT NOT NULL REFERENCES "shortlists"("id"),
    "publisher_id" TEXT NOT NULL REFERENCES "publisher_records"("id"),
    "match_result_id" TEXT REFERENCES "match_results"("id"),
    "notes" TEXT,
    "created_at" TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS "ai_contradictions" (
    "id" TEXT PRIMARY KEY,
    "company_id" TEXT NOT NULL REFERENCES "companies"("id"),
    "observation_id" TEXT NOT NULL REFERENCES "ai_observations"("id"),
    "attribute_name" TEXT NOT NULL,
    "existing_value" TEXT,
    "new_value" TEXT,
    "resolution_status" TEXT NOT NULL DEFAULT 'UNRESOLVED',
    "created_at" TEXT NOT NULL
);
