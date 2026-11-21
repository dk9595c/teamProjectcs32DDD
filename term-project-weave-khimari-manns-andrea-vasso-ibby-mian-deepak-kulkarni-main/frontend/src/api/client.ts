/// <reference types="vite/client" />
import { z } from 'zod';

export const apiBaseUrl = import.meta.env.VITE_API_BASE_URL || '/api/v1';

export async function apiGet<T>(path: string, schema: z.ZodSchema<T>): Promise<T> {
  const response = await fetch(`${apiBaseUrl}${path}`);
  if (!response.ok) {
    throw new Error(`API error: ${response.status} ${response.statusText}`);
  }
  const data = await response.json();
  return schema.parse(data);
}

export async function apiPost<T, U>(path: string, body: T, responseSchema: z.ZodSchema<U>): Promise<U> {
  const response = await fetch(`${apiBaseUrl}${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  if (!response.ok) {
    throw new Error(`API error: ${response.status} ${response.statusText}`);
  }
  const data = await response.json();
  return responseSchema.parse(data);
}

export const healthResponseSchema = z.object({
  status: z.literal('ok'),
  timestamp: z.string(),
  version: z.string(),
});

export type HealthResponse = z.infer<typeof healthResponseSchema>;