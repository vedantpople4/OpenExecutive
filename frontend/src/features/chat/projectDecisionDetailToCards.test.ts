import { describe, expect, it } from 'vitest'
import { projectDecisionDetailToCards } from './projectDecisionDetailToCards'
import { primaryDecisionDetail } from '../../api/mock/decisions'
import type { PhaseCardData } from './chat.types'

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
