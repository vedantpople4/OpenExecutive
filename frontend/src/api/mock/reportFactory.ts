import type { AgentReport } from '../types'

/** Fills in every required AgentReport field with empty defaults so fixtures only need to
 * specify what's interesting for that report. */
export function makeReport(overrides: Partial<AgentReport> & Pick<AgentReport, 'title' | 'summary'>): AgentReport {
  return {
    key_findings: [],
    recommendations: [],
    risks: [],
    alignment_score: 0.8,
    round_number: 0,
    is_fallback: false,
    contingencies: [],
    agreements: [],
    conflicts: [],
    required_changes: [],
    revised_recommendations: [],
    challenged_by: [],
    ...overrides,
  }
}
