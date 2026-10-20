/**
 * studio.ts - TypeScript interface definitions for Frontend Studio.
 */

export interface ApiEndpoint {
  method: "GET" | "POST" | "PUT" | "PATCH" | "DELETE" | string;
  path: string;
  description: string;
  sampleRequest?: Record<string, unknown> | unknown;
  sampleResponse?: Record<string, unknown> | unknown;
}

export interface StructuredError {
  file: string;
  line: number;
  rule: string;
  message: string;
}

export interface ChatMessage {
  role: "user" | "agent";
  text: string;
  details?: {
    backendFiles?: string[];
    frontendFiles?: string[];
    endpoints?: ApiEndpoint[];
    errors?: StructuredError[];
  };
}

export interface TestResult {
  status: number;
  duration: number;
  data: unknown;
  source: string;
  isSimulated: boolean;
}

export interface GenerationResponse {
  status: "success" | "partial" | "error";
  message: string;
  plan?: string;
  code?: string;
  files?: Record<string, string>;
  backend_files?: Record<string, string>;
  frontend_files?: Record<string, string>;
  api_spec?: ApiEndpoint[];
  execution_result?: string;
  backend_test_results?: string;
  errors?: StructuredError[];
  attempt?: number;
}
