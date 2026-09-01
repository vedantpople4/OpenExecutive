import { describe, it, expect } from 'vitest'
import { describeLatestActivity } from './describeLatestActivity'
import { projectEventsToCards } from './projectEventsToCards'
import { buildMockTimeline } from '../../api/mock/timeline'

const AGENTS = ['ceo', 'cfo', 'cto', 'cmo'] as const

function cardsAfter(predicate: (type: string) => boolean, prompt = 'test prompt') {
  const timeline = buildMockTimeline('run-1', prompt, [...AGENTS])
  const cut = timeline.findIndex((e) => predicate(e.type))
  return projectEventsToCards(timeline.slice(0, cut + 1))
}

describe('describeLatestActivity', () => {
  it('has nothing to announce before the first phase starts', () => {
    expect(describeLatestActivity([])).toBeNull()
  })

  it('names the agent currently working', () => {
    const cards = cardsAfter((t) => t === 'agent_speaking')
    expect(describeLatestActivity(cards)).toMatch(/^\w+: [A-Z]+ is thinking\.$/)
  })

  it('reports the alignment score once a report lands', () => {
    const cards = cardsAfter((t) => t === 'agent_report_generated')
    const said = describeLatestActivity(cards)
    expect(said).toMatch(/[A-Z]+ reported, \d+ percent alignment\.$/)
  })

  it('announces the decision once the board converges, over any phase detail', () => {
    const cards = projectEventsToCards(buildMockTimeline('run-1', 'test prompt', [...AGENTS]))
    expect(describeLatestActivity(cards)).toBe('The board reached a decision.')
  })

  it('locates activity inside a deliberation round rather than just the phase', () => {
    const timeline = buildMockTimeline('run-1', 'test prompt', [...AGENTS])
    const cut = timeline.findIndex((e) => e.type === 'deliberation_round_started')
    const cards = projectEventsToCards(timeline.slice(0, cut + 1))
    expect(describeLatestActivity(cards)).toContain('round 1')
  })

  it('never announces a full report body -- only the frontier', () => {
    const cards = cardsAfter((t) => t === 'agent_report_generated')
    // The longest sensible announcement is one short sentence; a report body would blow past this.
    expect(describeLatestActivity(cards)!.length).toBeLessThan(80)
  })
})
