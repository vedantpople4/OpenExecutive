import type { AgentReport, CXOName, DeliberationEvent } from '../types'
import { primaryDecisionDetail } from './decisions'

let eventCounter = 0
function nextEventId(): string {
  eventCounter += 1
  return `mock-evt-${eventCounter}`
}

function baseEvent(aggregateId: string) {
  return {
    event_id: nextEventId(),
    timestamp: new Date().toISOString(),
    aggregate_id: aggregateId,
  }
}

/**
 * Builds the full scripted event sequence for a mocked deliberation run, mirroring the shape
 * of `primaryDecisionDetail`. Mirrors a real 5-round run: Inception -> Analysis -> Deliberation
 * (rounds 1-5) -> Synthesis. See openexec/orchestrator.py / orchestrator_deliberation.py for the
 * real phase layout this reproduces.
 */
export function buildMockTimeline(
  runId: string,
  prompt: string,
  agents: CXOName[],
  parentRunId?: string,
): DeliberationEvent[] {
  const events: DeliberationEvent[] = []
  const detail = primaryDecisionDetail
  const b = () => baseEvent(runId)

  events.push({
    ...b(),
    type: 'simulation_initialized',
    core_prompt: prompt,
    decision_point: detail.decision_point,
    agent_names: agents,
  })

  events.push({ ...b(), type: 'inception_started' })
  events.push({ ...b(), type: 'inception_completed' })

  events.push({ ...b(), type: 'analysis_started' })
  for (const agent of agents) {
    const report = detail.agent_reports[agent]
    if (!report) continue
    events.push({ ...b(), type: 'agent_speaking', agent_name: agent })
    events.push({
      ...b(),
      type: 'agent_report_generated',
      agent_name: agent,
      report_data: report,
    })
  }
  events.push({ ...b(), type: 'analysis_completed' })

  events.push({ ...b(), type: 'deliberation_started' })
  const roundNumbers = Object.keys(detail.deliberation_rounds)
    .map(Number)
    .sort((a, x) => a - x)

  for (const roundNumber of roundNumbers) {
    const roundReports = detail.deliberation_rounds[roundNumber]
    events.push({ ...b(), type: 'deliberation_round_started', round_number: roundNumber })

    const reportsInRound: Record<string, AgentReport> = {}
    for (const [agent, report] of Object.entries(roundReports)) {
      if (!agents.includes(agent as CXOName) && agent !== 'ceo') continue
      events.push({ ...b(), type: 'agent_speaking', agent_name: agent, round_number: roundNumber })
      events.push({
        ...b(),
        type: 'agent_report_generated',
        agent_name: agent,
        report_data: report,
      })
      reportsInRound[agent] = report
    }

    events.push({
      ...b(),
      type: 'deliberation_round_completed',
      round_number: roundNumber,
      reports: reportsInRound,
    })
  }
  events.push({ ...b(), type: 'deliberation_completed' })

  events.push({ ...b(), type: 'synthesis_started' })
  events.push({
    ...b(),
    type: 'synthesis_completed',
    final_report: { ...detail, runId, prompt, parentRunId },
  })

  return events
}
