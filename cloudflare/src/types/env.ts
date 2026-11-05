export interface Env {
  DB: D1Database;
  KV?: KVNamespace;
  R2?: R2Bucket;
  AI?: any;
  ENVIRONMENT: string;
  TARGET_MONTHLY_COST: string;
  GROQ_API_KEY?: string;
  GEMINI_API_KEY?: string;
  GROQ_API_URL: string;
  GEMINI_API_URL: string;
  JWT_SECRET: string;
}

export interface UserPayload {
  sub: string;
  email: string;
  role: string;
  company_id?: string | null;
  exp?: number;
}

