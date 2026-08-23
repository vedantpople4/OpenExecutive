// @vitest-environment jsdom
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { renderHook, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import type { ReactNode } from 'react'
import { useDecisionHistory } from './useDecisionHistory'
import type { DecisionSummary } from '../../../api/types'
import type { DecisionHistoryPage } from '../../../api/dto'

const { getDecisionHistoryMock } = vi.hoisted(() => ({ getDecisionHistoryMock: vi.fn() }))

vi.mock('../../../api/endpoints', () => ({
  getDecisionHistory: getDecisionHistoryMock,
}))

function makeDecision(runId: string, prompt: string): DecisionSummary {
  return {
    runId,
    timestamp: '2026-01-01T00:00:00.000Z',
    prompt,
    actionItemCount: 0,
    topRisks: [],
    agentAlignment: {},
  }
}

function wrapper({ children }: { children: ReactNode }) {
  const queryClient = new QueryClient()
  return <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
}

describe('useDecisionHistory', () => {
  beforeEach(() => {
    getDecisionHistoryMock.mockReset()
  })

  it('accumulates pages across fetchNextPage', async () => {
    const page1: DecisionHistoryPage = { items: [makeDecision('r1', 'first')], nextCursor: '1' }
    const page2: DecisionHistoryPage = { items: [makeDecision('r2', 'second')], nextCursor: null }
    getDecisionHistoryMock.mockImplementation(({ cursor }: { cursor?: string }) =>
      Promise.resolve(cursor === '1' ? page2 : page1),
    )

    const { result } = renderHook(() => useDecisionHistory(''), { wrapper })

    await waitFor(() => expect(result.current.decisions).toEqual([makeDecision('r1', 'first')]))
    expect(result.current.hasNextPage).toBe(true)

    await result.current.fetchNextPage()

    await waitFor(() =>
      expect(result.current.decisions).toEqual([makeDecision('r1', 'first'), makeDecision('r2', 'second')]),
    )
    expect(result.current.hasNextPage).toBe(false)
  })

  it('starts a fresh single-page result when q changes rather than merging with the old query', async () => {
    getDecisionHistoryMock.mockImplementation(({ q }: { q?: string }) =>
      Promise.resolve<DecisionHistoryPage>({
        items: [makeDecision(`r-${q ?? 'none'}`, q ?? 'unfiltered')],
        nextCursor: null,
      }),
    )

    const { result, rerender } = renderHook(({ q }: { q: string }) => useDecisionHistory(q), {
      wrapper,
      initialProps: { q: '' },
    })

    await waitFor(() => expect(result.current.decisions).toHaveLength(1))
    expect(result.current.decisions?.[0].runId).toBe('r-none')

    rerender({ q: 'berlin' })

    await waitFor(() => expect(result.current.decisions?.[0].runId).toBe('r-berlin'))
    expect(result.current.decisions).toHaveLength(1)
  })
})
