/**
 * Thin config layer. Set VITE_API_BASE_URL (e.g. in .env.local — see .env.example) to point the
 * app at a real backend; endpoints.ts then dispatches every call to endpoints.real.ts instead of
 * the in-memory mock layer (src/api/mock/*). Forced to mocks under `vitest` regardless of any
 * local .env.local, since jsdom/node have no EventSource/fetch-to-a-real-server and Vitest does
 * load .env.local (unlike plain `vite dev`) — this MODE check is the actual safeguard, not the
 * env-loading behavior.
 */
export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL as string | undefined
export const USE_MOCK_API = import.meta.env.MODE === 'test' || !API_BASE_URL

/** Supabase project config for sign-in only (see src/api/supabaseClient.ts). The frontend never
 * touches Supabase's data client or RLS, the backend keeps owning every data read/write. */
export const SUPABASE_URL = import.meta.env.VITE_SUPABASE_URL as string | undefined
export const SUPABASE_ANON_KEY = import.meta.env.VITE_SUPABASE_ANON_KEY as string | undefined

/** Simulates network latency for the mock layer so loading states are visible/testable. */
export function mockDelay<T>(value: T, ms = 300): Promise<T> {
  return new Promise((resolve) => setTimeout(() => resolve(value), ms))
}

/** Carries the HTTP status so a global handler (App.tsx's QueryCache/MutationCache) can react to
 * 401 specifically, rather than parsing it back out of a message string. */
export class ApiError extends Error {
  readonly status: number

  constructor(message: string, status: number) {
    super(message)
    this.name = 'ApiError'
    this.status = status
  }
}
