export interface Env {
  DB: D1Database;
  KV?: KVNamespace;
  R2?: R2Bucket;
  AI?: any;
  ASSETS?: Fetcher;
  ENVIRONMENT: string;
  TARGET_MONTHLY_COST: string;
  ANTHROPIC_API_KEY?: string;
  ANTHROPIC_API_URL?: string;
  ANTHROPIC_ENABLED?: string;
  GEMINI_API_KEY?: string;
  GEMINI_API_URL?: string;
  GROQ_API_KEY?: string;
  GROQ_API_URL?: string;
  JWT_SECRET: string;
}

export interface UserPayload {
  sub: string;
  email: string;
  role: string;
  company_id?: string | null;
  exp?: number;
}
