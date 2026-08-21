import { describe, it, expect } from 'vitest'
import { groupHistoryByRecency } from './groupHistoryByRecency'
import type { DecisionSummary } from '../api/types'

function makeDecision(runId: string, timestamp: string): DecisionSummary {
  return {
    runId,
    timestamp,
    prompt: `prompt for ${runId}`,
    actionItemCount: 0,
    topRisks: [],
    agentAlignment: {},
  }
}

describe('groupHistoryByRecency', () => {
  const now = new Date('2026-08-20T12:00:00.000Z')

  it('buckets decisions into Today/Yesterday/Previous 7 Days/Previous 30 Days/older-by-month', () => {
    const decisions = [
      makeDecision('today', '2026-08-20T09:00:00.000Z'),
      makeDecision('yesterday', '2026-08-19T09:00:00.000Z'),
      makeDecision('this-week', '2026-08-16T09:00:00.000Z'),
      makeDecision('this-month', '2026-08-01T09:00:00.000Z'),
      makeDecision('older', '2026-06-10T09:00:00.000Z'),
    ]

    const groups = groupHistoryByRecency(decisions, now)
    const labels = groups.map((g) => g.label)

    expect(labels).toContain('Today')
    expect(labels).toContain('Yesterday')
    expect(labels).toContain('Previous 7 Days')
    expect(labels).toContain('Previous 30 Days')
    expect(labels).toContain('June 2026')

    expect(groups.find((g) => g.label === 'Today')?.items.map((i) => i.runId)).toEqual(['today'])
  })

  it('preserves input order within a bucket', () => {
    const decisions = [
      makeDecision('a', '2026-08-20T10:00:00.000Z'),
      makeDecision('b', '2026-08-20T09:00:00.000Z'),
    ]
    const groups = groupHistoryByRecency(decisions, now)
    expect(groups[0].items.map((i) => i.runId)).toEqual(['a', 'b'])
  })

  it('returns an empty array for no decisions', () => {
    expect(groupHistoryByRecency([], now)).toEqual([])
  })
})
