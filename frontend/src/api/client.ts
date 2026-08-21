/**
 * Thin config layer. Every endpoint in endpoints.ts currently reads from the in-memory mock
 * layer (src/api/mock/*) instead of a real backend, which doesn't exist yet (see plan Section 8).
 * When a real backend exists, this is the only file that should need a base URL / fetch setup.
 */
export const USE_MOCK_API = true

/** Simulates network latency for the mock layer so loading states are visible/testable. */
export function mockDelay<T>(value: T, ms = 300): Promise<T> {
  return new Promise((resolve) => setTimeout(() => resolve(value), ms))
}
