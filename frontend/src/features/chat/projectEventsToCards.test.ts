import { describe, expect, it } from 'vitest'
import { projectEventsToCards } from './projectEventsToCards'
import { buildMockTimeline } from '../../api/mock/timeline'
import type { PhaseCardData } from './chat.types'

const AGENTS = ['ceo', 'cfo', 'cto', 'cmo'] as const

describe('projectEventsToCards', () => {
  it('folds the full mock timeline into inception, analysis, deliberation phases and a board decision', () => {
    const events = buildMockTimeline('run-1', 'test prompt', [...AGENTS])
    const cards = projectEventsToCards(events)

    const phases = cards.filter((c) => c.kind === 'phase') as PhaseCardData[]
    expect(phases.map((p) => p.phase)).toEqual(['inception', 'analysis', 'deliberation'])
    expect(phases.every((p) => p.status === 'done')).toBe(true)

    const analysis = phases.find((p) => p.phase === 'analysis')!
    expect(analysis.reports).toHaveLength(4)
    expect(analysis.speaking).toHaveLength(0) // all speaking placeholders resolved into reports

    const deliberation = phases.find((p) => p.phase === 'deliberation')!
    expect(deliberation.rounds).toHaveLength(5)
    expect(deliberation.rounds.every((r) => r.status === 'done')).toBe(true)
    expect(deliberation.rounds[0].reports.map((r) => r.agentName)).toEqual(['ceo'])
    expect(deliberation.rounds[1].reports.map((r) => r.agentName).sort()).toEqual(['cfo', 'cto'])

    const boardDecision = cards.find((c) => c.kind === 'board_decision')
    expect(boardDecision).toBeDefined()
    if (boardDecision?.kind === 'board_decision') {
      expect(boardDecision.boardDecision.consensus_points.length).toBeGreaterThan(0)
    }
  })

  it('shows an agent as speaking before its report lands, mid-stream', () => {
    const events = buildMockTimeline('run-1', 'test prompt', [...AGENTS])
    const analysisStartIndex = events.findIndex((e) => e.type === 'analysis_started')
    const firstSpeakingIndex = events.findIndex((e) => e.type === 'agent_speaking')
    // events between analysis_started and the first agent_report_generated
    const partial = events.slice(0, firstSpeakingIndex + 1)
    expect(analysisStartIndex).toBeGreaterThanOrEqual(0)

    const cards = projectEventsToCards(partial)
    const analysis = cards.find((c) => c.kind === 'phase' && c.phase === 'analysis') as
      | PhaseCardData
      | undefined
    expect(analysis?.status).toBe('running')
    expect(analysis?.speaking).toHaveLength(1)
    expect(analysis?.reports).toHaveLength(0)
  })

  it('produces stable ids for already-closed cards as more events are appended (no remount)', () => {
    const events = buildMockTimeline('run-1', 'test prompt', [...AGENTS])
    const analysisCompletedIndex = events.findIndex((e) => e.type === 'analysis_completed')

    const prefix = events.slice(0, analysisCompletedIndex + 1)
    const fuller = events.slice(0, analysisCompletedIndex + 5)

    const prefixCards = projectEventsToCards(prefix)
    const fullerCards = projectEventsToCards(fuller)

    const prefixAnalysis = prefixCards.find((c) => c.kind === 'phase' && c.phase === 'analysis')!
    const fullerAnalysis = fullerCards.find((c) => c.kind === 'phase' && c.phase === 'analysis')!

    expect(fullerAnalysis.id).toBe(prefixAnalysis.id)
  })

  it('renders error_occurred events as inline error cards', () => {
    const events = buildMockTimeline('run-1', 'test prompt', [...AGENTS])
    const withError = [
      ...events.slice(0, 3),
      {
        event_id: 'err-1',
        timestamp: new Date().toISOString(),
        aggregate_id: 'run-1',
        type: 'error_occurred' as const,
        error_message: 'LLM call failed',
        phase: 'analysis',
        agent_name: 'cfo',
      },
      ...events.slice(3),
    ]
    const cards = projectEventsToCards(withError)
    const errorCard = cards.find((c) => c.kind === 'error')
    expect(errorCard).toBeDefined()
  })
})

describe('projectEventsToCards — team analysis phase', () => {
  // Hand-built rather than extending buildMockTimeline: the first test above
  // asserts the mock timeline yields exactly three phases.
  const base = { aggregate_id: 'run-team', timestamp: '2026-01-01T00:00:00.000Z' }

  function specialistReport(agentName: string, parentCxo: string) {
    return {
      ...base,
      event_id: `report-${agentName}`,
      type: 'specialist_report_generated' as const,
      agent_name: agentName,
      parent_cxo: parentCxo,
      report_data: {
        title: 't',
        summary: 's',
        key_findings: [],
        recommendations: [],
        risks: [],
        alignment_score: 0.8,
        // 0 is what files this under the team phase instead of a round.
        round_number: 0,
      },
    }
  }

  function teamEvents() {
    return [
      { ...base, event_id: 'a-done', type: 'analysis_completed' as const, reports_generated: [] },
      { ...base, event_id: 'team-start', type: 'team_analysis_started' as const },
      { ...base, event_id: 'sp-1', type: 'agent_speaking' as const, agent_name: 'financial_analyst' },
      specialistReport('financial_analyst', 'cfo'),
      { ...base, event_id: 'sp-2', type: 'agent_speaking' as const, agent_name: 'risk_analyst' },
      specialistReport('risk_analyst', 'cfo'),
      { ...base, event_id: 'team-done', type: 'team_analysis_completed' as const },
    ]
  }

  it('opens and closes a team_analysis phase', () => {
    const cards = projectEventsToCards(teamEvents() as never)
    const phases = cards.filter((c) => c.kind === 'phase') as PhaseCardData[]

    const team = phases.find((p) => p.phase === 'team_analysis')!
    expect(team).toBeDefined()
    expect(team.status).toBe('done')
  })

  it('files specialist reports on the team phase with their parent CXO', () => {
    const cards = projectEventsToCards(teamEvents() as never)
    const team = (cards.filter((c) => c.kind === 'phase') as PhaseCardData[]).find(
      (p) => p.phase === 'team_analysis',
    )!

    expect(team.reports).toHaveLength(2)
    expect(team.reports.map((r) => r.parentCXO)).toEqual(['cfo', 'cfo'])
    expect(team.reports.map((r) => r.agentName)).toEqual(['financial_analyst', 'risk_analyst'])
  })

  it('shows a speaking indicator until that specialist reports', () => {
    const events = teamEvents()
    // Truncate mid-stream: one agent announced, no report yet.
    const midStream = projectEventsToCards(events.slice(0, 3) as never)
    const teamMid = (midStream.filter((c) => c.kind === 'phase') as PhaseCardData[]).find(
      (p) => p.phase === 'team_analysis',
    )!
    expect(teamMid.speaking.map((s) => s.agentName)).toEqual(['financial_analyst'])

    const complete = projectEventsToCards(events as never)
    const teamDone = (complete.filter((c) => c.kind === 'phase') as PhaseCardData[]).find(
      (p) => p.phase === 'team_analysis',
    )!
    expect(teamDone.speaking).toHaveLength(0)
  })

  it('dedupes repeated team_analysis_started into one card', () => {
    const events = teamEvents()
    events.splice(2, 0, { ...base, event_id: 'team-start-2', type: 'team_analysis_started' as const })

    const cards = projectEventsToCards(events as never)
    const teamPhases = (cards.filter((c) => c.kind === 'phase') as PhaseCardData[]).filter(
      (p) => p.phase === 'team_analysis',
    )
    expect(teamPhases).toHaveLength(1)
  })
})
