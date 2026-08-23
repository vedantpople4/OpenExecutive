// @vitest-environment jsdom
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, act } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { HistorySection } from './HistorySection'
import type { DecisionSummary } from '../../api/types'

const { useDecisionHistoryMock } = vi.hoisted(() => ({ useDecisionHistoryMock: vi.fn() }))

vi.mock('./hooks/useDecisionHistory', () => ({
  useDecisionHistory: useDecisionHistoryMock,
}))

function makeDecision(runId: string): DecisionSummary {
  return {
    runId,
    timestamp: '2026-01-01T00:00:00.000Z',
    prompt: `prompt ${runId}`,
    actionItemCount: 0,
    topRisks: [],
    agentAlignment: {},
  }
}

function renderSection() {
  return render(
    <MemoryRouter>
      <HistorySection />
    </MemoryRouter>,
  )
}

describe('HistorySection', () => {
  beforeEach(() => {
    useDecisionHistoryMock.mockReset()
  })

  it('shows a Load more button when hasNextPage is true, and calls fetchNextPage on click', () => {
    const fetchNextPage = vi.fn()
    useDecisionHistoryMock.mockReturnValue({
      decisions: [makeDecision('r1')],
      isLoading: false,
      isError: false,
      fetchNextPage,
      hasNextPage: true,
      isFetchingNextPage: false,
    })

    renderSection()

    const button = screen.getByRole('button', { name: 'Load more' })
    fireEvent.click(button)
    expect(fetchNextPage).toHaveBeenCalledTimes(1)
  })

  it('hides the Load more button when hasNextPage is false', () => {
    useDecisionHistoryMock.mockReturnValue({
      decisions: [makeDecision('r1')],
      isLoading: false,
      isError: false,
      fetchNextPage: vi.fn(),
      hasNextPage: false,
      isFetchingNextPage: false,
    })

    renderSection()

    expect(screen.queryByRole('button', { name: /load more/i })).not.toBeInTheDocument()
  })

  it('debounces search input before passing it to useDecisionHistory', () => {
    useDecisionHistoryMock.mockReturnValue({
      decisions: [makeDecision('r1')],
      isLoading: false,
      isError: false,
      fetchNextPage: vi.fn(),
      hasNextPage: false,
      isFetchingNextPage: false,
    })

    vi.useFakeTimers()
    try {
      renderSection()
      expect(useDecisionHistoryMock).toHaveBeenLastCalledWith('')

      fireEvent.change(screen.getByRole('searchbox', { name: 'Search decision history' }), {
        target: { value: 'berlin' },
      })
      expect(useDecisionHistoryMock).toHaveBeenLastCalledWith('')

      act(() => {
        vi.advanceTimersByTime(300)
      })
      expect(useDecisionHistoryMock).toHaveBeenLastCalledWith('berlin')
    } finally {
      vi.useRealTimers()
    }
  })
})
