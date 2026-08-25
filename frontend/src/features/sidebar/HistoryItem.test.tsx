// @vitest-environment jsdom
import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { HistoryItem } from './HistoryItem'
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
  return render(
    <MemoryRouter>
      <HistoryItem decision={makeDecision(status)} isActive={false} />
    </MemoryRouter>,
  )
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
