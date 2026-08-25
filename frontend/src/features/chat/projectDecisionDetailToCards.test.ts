import { describe, expect, it } from 'vitest'
import { projectDecisionDetailToCards } from './projectDecisionDetailToCards'
import { primaryDecisionDetail } from '../../api/mock/decisions'
import type { ErrorCardData, PhaseCardData } from './chat.types'

describe('projectDecisionDetailToCards', () => {
  it('produces done inception/analysis/deliberation phases and a board decision card', () => {
    const cards = projectDecisionDetailToCards(primaryDecisionDetail)
    const phases = cards.filter((c) => c.kind === 'phase') as PhaseCardData[]

    expect(phases.map((p) => p.phase)).toEqual(['inception', 'analysis', 'deliberation'])
    expect(phases.every((p) => p.status === 'done')).toBe(true)

    const analysis = phases.find((p) => p.phase === 'analysis')!
    expect(analysis.reports).toHaveLength(Object.keys(primaryDecisionDetail.agent_reports).length)

    const deliberation = phases.find((p) => p.phase === 'deliberation')!
    expect(deliberation.rounds).toHaveLength(
      Object.keys(primaryDecisionDetail.deliberation_rounds).length,
    )
    expect(deliberation.rounds.every((r) => r.status === 'done')).toBe(true)

    const boardDecision = cards.find((c) => c.kind === 'board_decision')
    expect(boardDecision).toBeDefined()
  })

  it('omits the deliberation phase entirely when there are no rounds recorded', () => {
    const cards = projectDecisionDetailToCards({
      ...primaryDecisionDetail,
      deliberation_rounds: {},
    })
    const phases = cards.filter((c) => c.kind === 'phase') as PhaseCardData[]
    expect(phases.map((p) => p.phase)).toEqual(['inception', 'analysis'])
  })
})

describe('projectDecisionDetailToCards — failed and stopped runs', () => {
  it('renders an error card and no board decision when the run failed', () => {
    const cards = projectDecisionDetailToCards({
      ...primaryDecisionDetail,
      status: 'error',
      error_message: 'LLM provider unreachable',
      board_decision: {} as typeof primaryDecisionDetail.board_decision,
    })

    expect(cards.find((c) => c.kind === 'board_decision')).toBeUndefined()
    const error = cards.find((c) => c.kind === 'error') as ErrorCardData
    expect(error.variant).toBe('error')
    expect(error.message).toBe('LLM provider unreachable')
  })

  it('keeps completed rounds visible when a run was stopped part-way', () => {
    const cards = projectDecisionDetailToCards({
      ...primaryDecisionDetail,
      status: 'stopped',
      board_decision: {} as typeof primaryDecisionDetail.board_decision,
    })

    expect(cards.find((c) => c.kind === 'board_decision')).toBeUndefined()
    const error = cards.find((c) => c.kind === 'error') as ErrorCardData
    expect(error.variant).toBe('stopped')
    // The whole point of saving partial results: the discussion survives.
    const phases = cards.filter((c) => c.kind === 'phase') as PhaseCardData[]
    expect(phases.map((p) => p.phase)).toContain('deliberation')
  })

  it('falls back gracefully for legacy rows persisted before status existed', () => {
    const cards = projectDecisionDetailToCards({
      ...primaryDecisionDetail,
      board_decision: {} as typeof primaryDecisionDetail.board_decision,
    })

    const error = cards.find((c) => c.kind === 'error') as ErrorCardData
    expect(error.message).toBe('No board decision was recorded for this run.')
  })
})
