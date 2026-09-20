// @vitest-environment jsdom
// queryClient.ts transitively imports routes/router.tsx, which calls createBrowserRouter at
// module load -- that needs a window/history, so this file needs jsdom even though it only
// tests a pure function.
import { describe, it, expect } from 'vitest'
import { ApiError } from './api/client'
import { isAuthError } from './queryClient'

describe('isAuthError', () => {
  it('treats a 401 ApiError as an auth error', () => {
    expect(isAuthError(new ApiError('nope', 401))).toBe(true)
  })

  it('treats a 403 ApiError as an auth error', () => {
    expect(isAuthError(new ApiError('nope', 403))).toBe(true)
  })

  it('does not treat a 404 or 500 ApiError as an auth error', () => {
    expect(isAuthError(new ApiError('missing', 404))).toBe(false)
    expect(isAuthError(new ApiError('broken', 500))).toBe(false)
  })

  it('does not treat a plain Error or non-error value as an auth error', () => {
    expect(isAuthError(new Error('network down'))).toBe(false)
    expect(isAuthError(undefined)).toBe(false)
  })
})
