// @vitest-environment jsdom
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { screen, fireEvent, waitFor } from '@testing-library/react'
import { renderWithProviders } from '../../test/renderWithProviders'
import { HistoryItem } from './HistoryItem'
import { deleteDecision } from '../../api/endpoints'

vi.mock('../../api/endpoints', () => ({ deleteDecision: vi.fn() }))
const deleteDecisionMock = vi.mocked(deleteDecision)
import type { DecisionSummary, RunOutcome } from '../../api/types'

function makeDecision(status?: RunOutcome): DecisionSummary {
  return {
    runId: 'run-1',
    timestamp: '2026-01-01T00:00:00.000Z',
    prompt: 'Should we expand to Berlin?',
    actionItemCount: 0,
    topRisks: [],
    agentAlignment: {},
    status,
  }
}

function renderItem(status?: RunOutcome) {
  return renderWithProviders(<HistoryItem decision={makeDecision(status)} isActive={false} />)
}

describe('HistoryItem run status badge', () => {
  it('badges a failed run', () => {
    renderItem('error')
    expect(screen.getByLabelText('Deliberation failed')).toBeInTheDocument()
  })

  it('badges a stopped run', () => {
    renderItem('stopped')
    expect(screen.getByLabelText('Stopped before a decision')).toBeInTheDocument()
  })

  it.each([['completed' as const], ['running' as const], [undefined]])(
    'stays silent for %s runs',
    (status) => {
      renderItem(status)
      expect(screen.queryByLabelText('Deliberation failed')).not.toBeInTheDocument()
      expect(screen.queryByLabelText('Stopped before a decision')).not.toBeInTheDocument()
    },
  )
})


describe('HistoryItem delete', () => {
  beforeEach(() => {
    deleteDecisionMock.mockReset()
    deleteDecisionMock.mockResolvedValue(undefined)
  })

  it('does not delete on the first click -- it asks first', () => {
    renderItem()

    fireEvent.click(screen.getByLabelText(/^Delete decision:/))

    expect(screen.getByText('Delete permanently?')).toBeInTheDocument()
    expect(deleteDecisionMock).not.toHaveBeenCalled()
  })

  it('deletes the run once confirmed', async () => {
    renderItem()
    fireEvent.click(screen.getByLabelText(/^Delete decision:/))

    fireEvent.click(screen.getByRole('button', { name: 'Delete' }))

    await waitFor(() => expect(deleteDecisionMock).toHaveBeenCalledWith('run-1'))
  })

  it('cancel backs out without calling the API', () => {
    renderItem()
    fireEvent.click(screen.getByLabelText(/^Delete decision:/))

    fireEvent.click(screen.getByRole('button', { name: 'Cancel' }))

    expect(screen.queryByText('Delete permanently?')).not.toBeInTheDocument()
    expect(deleteDecisionMock).not.toHaveBeenCalled()
  })

  it("surfaces the server's reason instead of failing silently", async () => {
    // What a 409 looks like: the backend refuses to delete a running decision
    // because its worker would write the row back minutes later.
    deleteDecisionMock.mockRejectedValue(
      new Error('Decision is still running. Stop it before deleting.'),
    )
    renderItem()
    fireEvent.click(screen.getByLabelText(/^Delete decision:/))

    fireEvent.click(screen.getByRole('button', { name: 'Delete' }))

    expect(
      await screen.findByText('Decision is still running. Stop it before deleting.'),
    ).toBeInTheDocument()
  })
})
