import type { DecisionDetail, DecisionSummary } from '../types'
import { makeReport } from './reportFactory'

const HIRE_VS_AGENTS_PROMPT = 'Should we hire more Software Engineers or build AI agents to do the work?'

export const primaryDecisionDetail: DecisionDetail = {
  runId: 'run-20260810-141200',
  timestamp: '2026-08-10T14:12:00.000Z',
  prompt: HIRE_VS_AGENTS_PROMPT,
  decision_point: 'Decision required for: Should we hire more Software Engineers or build AI agents to do the work?',
  executive_summary:
    'Pursue a hybrid approach: fund two senior engineering hires this quarter while piloting AI agents on well-scoped, repeatable backlog work. Revisit the mix after the pilot reports throughput and defect-rate data.',
  agent_reports: {
    ceo: makeReport({
      title: 'Strategic framing',
      summary: 'This is a build-vs-buy-vs-augment call, not a headcount call — decide what our moat is first.',
      key_findings: ['Our differentiation is product velocity, not raw headcount.'],
      recommendations: ['Frame this as an augmentation decision, not a replacement decision.'],
      risks: ['Over-indexing on AI agents before proving reliability on our own codebase.'],
      alignment_score: 0.88,
      verdict: 'Proceed with a bounded pilot before committing budget either way.',
    }),
    cfo: makeReport({
      title: 'Financial analysis',
      summary: 'Two senior hires cost ~$420k/yr fully loaded; an agent pilot costs a fraction of that in API spend.',
      key_findings: ['Fully loaded senior engineer cost: ~$210k/yr.', 'Estimated agent pilot cost: ~$18k/quarter.'],
      recommendations: ['Cap pilot spend at $25k for one quarter before re-evaluating.'],
      risks: ['Runway impact if both tracks are funded simultaneously without a kill criterion.'],
      alignment_score: 0.82,
      verdict: 'Fund the pilot before the second hire; let pilot data inform hire count.',
    }),
    cto: makeReport({
      title: 'Technical feasibility',
      summary: 'Repeatable backlog work (test coverage, migrations, small bug fixes) is a good pilot fit; core architecture work is not.',
      key_findings: ['~30% of the current backlog is well-scoped enough for agent execution.'],
      recommendations: ['Pilot on test coverage and dependency upgrades first — low blast radius.'],
      risks: ['Agent-authored code without strong review gates can quietly erode code quality.'],
      alignment_score: 0.79,
      verdict: 'Feasible for a bounded pilot; not a substitute for senior engineering judgment yet.',
    }),
    cmo: makeReport({
      title: 'Market read',
      summary: 'Customers care about ship speed and reliability, not how the code got written — this is an internal efficiency question.',
      key_findings: ['No competitive signal either way from customers surveyed this quarter.'],
      recommendations: ['No external messaging needed until the pilot produces a result worth sharing.'],
      risks: ['Overselling "AI-built" features externally before reliability is proven could backfire.'],
      alignment_score: 0.75,
      verdict: 'Neutral — this is an internal execution decision, not a market one.',
    }),
  },
  deliberation_rounds: {
    1: {
      ceo: makeReport({
        title: 'Round 1 — framing challenges',
        summary: 'CFO: show me the pilot cost cap. CTO: show me what backlog is actually safe to hand to agents.',
        round_number: 1,
        alignment_score: 0.85,
        challenges_for_cfo: ['What is the maximum pilot spend before this needs board sign-off?'],
        challenges_for_cto: ['Which backlog categories are safe for agent execution without a human rewrite pass?'],
        challenges_for_cmo: ['Is there any external risk to piloting this quietly?'],
      }),
    },
    2: {
      cfo: makeReport({
        title: 'Round 2 — financial response',
        summary: 'Capping pilot spend at $25k/quarter keeps this well under CFO discretionary authority.',
        round_number: 2,
        alignment_score: 0.83,
        agreements: ['Bounded pilot before committing to a second hire.'],
        required_changes: ['Add an explicit kill criterion: pilot ends if defect rate rises above baseline.'],
      }),
      cto: makeReport({
        title: 'Round 2 — technical response',
        summary: 'Test coverage and dependency upgrades are the safest pilot lanes; core service logic stays off-limits.',
        round_number: 2,
        alignment_score: 0.81,
        agreements: ['Pilot scope limited to low-blast-radius backlog items.'],
        conflicts: ['CFO wants a hard 1-quarter timebox; engineering may need longer to get reliable signal.'],
      }),
    },
    3: {
      cmo: makeReport({
        title: 'Round 3 — market response',
        summary: 'No external communication needed during the pilot; revisit messaging only if results are strong enough to be a differentiator.',
        round_number: 3,
        alignment_score: 0.77,
        agreements: ['Keep pilot internal, no external announcement.'],
      }),
    },
    4: {
      cfo: makeReport({
        title: 'Round 4 — revised position',
        summary: 'Agree to extend the pilot window to 6 weeks if CTO needs it, spend cap unchanged.',
        round_number: 4,
        alignment_score: 0.85,
        revised_recommendations: ['Extend pilot window to 6 weeks, keep the $25k cap.'],
      }),
      cto: makeReport({
        title: 'Round 4 — revised position',
        summary: 'A 6-week window is enough to get a real defect-rate signal on the chosen backlog lanes.',
        round_number: 4,
        alignment_score: 0.84,
        agreements: ['6-week pilot window with a defect-rate kill criterion.'],
      }),
      cmo: makeReport({
        title: 'Round 4 — revised position',
        summary: 'No change — still neutral, still recommending no external messaging during the pilot.',
        round_number: 4,
        alignment_score: 0.78,
      }),
    },
    5: {
      ceo: makeReport({
        title: 'Round 5 — board synthesis',
        summary: 'Board converges on a bounded, 6-week AI-agent pilot on low-risk backlog work, funded instead of an immediate second hire.',
        round_number: 5,
        alignment_score: 0.86,
        board_decision: {
          consensus_points: [
            'Run a 6-week AI-agent pilot on test coverage and dependency upgrades.',
            'Cap pilot spend at $25k for the quarter.',
            'No external messaging during the pilot.',
          ],
          dissent_points: ['CTO flagged the 6-week window as tight for a confident reliability signal.'],
          final_priority_actions: [
            '[Launch AI-agent pilot on test coverage backlog] | Owner: CTO | Timeframe: 2 weeks',
            '[Define defect-rate kill criterion and dashboard] | Owner: CFO | Timeframe: 1 week',
            '[Re-evaluate second engineering hire after pilot] | Owner: CEO | Timeframe: 6 weeks',
          ],
          dissenting_opinions: ['CTO: prefers an 8-week window given current team bandwidth.'],
          contingencies: ['If defect rate exceeds baseline by 15%, pilot ends immediately and hiring resumes.'],
          summary: 'Hybrid approach: fund a bounded AI-agent pilot before committing to additional headcount.',
          status: 'converged',
        },
      }),
    },
  },
  board_decision: {
    consensus_points: [
      'Run a 6-week AI-agent pilot on test coverage and dependency upgrades.',
      'Cap pilot spend at $25k for the quarter.',
      'No external messaging during the pilot.',
    ],
    dissent_points: ['CTO flagged the 6-week window as tight for a confident reliability signal.'],
    final_priority_actions: [
      '[Launch AI-agent pilot on test coverage backlog] | Owner: CTO | Timeframe: 2 weeks',
      '[Define defect-rate kill criterion and dashboard] | Owner: CFO | Timeframe: 1 week',
      '[Re-evaluate second engineering hire after pilot] | Owner: CEO | Timeframe: 6 weeks',
    ],
    dissenting_opinions: ['CTO: prefers an 8-week window given current team bandwidth.'],
    contingencies: ['If defect rate exceeds baseline by 15%, pilot ends immediately and hiring resumes.'],
    summary: 'Hybrid approach: fund a bounded AI-agent pilot before committing to additional headcount.',
    status: 'converged',
  },
  action_items: [
    { priority: 'HIGH', task: 'Launch AI-agent pilot on test coverage backlog', owner: 'CTO', due_date: '2026-08-24' },
    { priority: 'HIGH', task: 'Define defect-rate kill criterion and dashboard', owner: 'CFO', due_date: '2026-08-17' },
    { priority: 'MEDIUM', task: 'Re-evaluate second engineering hire after pilot', owner: 'CEO', due_date: '2026-09-21' },
  ],
  overall_risk_assessment: [
    'Agent-authored code without strong review gates can quietly erode code quality.',
    'Runway impact if both hiring and pilot tracks are funded without a kill criterion.',
  ],
  synthesized_recommendations: [
    'Run a bounded 6-week AI-agent pilot on low-risk backlog work.',
    'Delay the second engineering hire decision until pilot data lands.',
  ],
  fallback_warnings: [],
}

export const followUpDecisionDetail: DecisionDetail = {
  runId: 'run-20260817-093000',
  timestamp: '2026-08-17T09:30:00.000Z',
  prompt: 'The AI-agent pilot from two weeks ago is showing a 40% throughput gain with no defect-rate increase — should we expand it?',
  decision_point: 'Decision required for: expand the AI-agent pilot given early positive results?',
  parentRunId: primaryDecisionDetail.runId,
  executive_summary:
    'Expand the pilot to two more backlog categories (dependency upgrades already included) while keeping the defect-rate kill criterion in place; hold off on a second engineering hire for another cycle.',
  agent_reports: {
    ceo: makeReport({
      title: 'Strategic framing',
      summary: 'Early data supports expansion, but expand scope, not headcount replacement, until we have a full 6-week read.',
      alignment_score: 0.87,
    }),
    cfo: makeReport({
      title: 'Financial analysis',
      summary: 'Throughput gain at flat spend is a strong signal; approve doubling the pilot budget to $50k for the extension.',
      alignment_score: 0.86,
    }),
  },
  deliberation_rounds: {},
  board_decision: {
    consensus_points: ['Expand pilot scope to two more backlog categories.', 'Keep the existing kill criterion.'],
    dissent_points: [],
    final_priority_actions: [
      '[Expand pilot to code-review-assist tasks] | Owner: CTO | Timeframe: 1 week',
    ],
    dissenting_opinions: [],
    contingencies: ['Kill criterion from the original pilot still applies.'],
    summary: 'Expand the pilot; hold the hiring decision one more cycle.',
    status: 'converged',
  },
  action_items: [
    { priority: 'MEDIUM', task: 'Expand pilot to code-review-assist tasks', owner: 'CTO', due_date: '2026-08-24' },
  ],
  overall_risk_assessment: ['Scope creep on the pilot without re-tightening the kill criterion.'],
  synthesized_recommendations: ['Expand pilot scope at flat risk tolerance.'],
  fallback_warnings: [],
}

export const secondaryDecisionDetail: DecisionDetail = {
  runId: 'run-20260805-101500',
  timestamp: '2026-08-05T10:15:00.000Z',
  prompt: 'Should we raise prices on the Pro tier by 15% next quarter?',
  decision_point: 'Decision required for: Pro tier pricing increase?',
  executive_summary: 'Hold off on a blanket increase; grandfather existing customers and test the higher price on new signups only.',
  agent_reports: {},
  deliberation_rounds: {},
  board_decision: {
    consensus_points: ['Test pricing on new signups only.'],
    dissent_points: ['CMO worried about competitive positioning if the test leaks.'],
    final_priority_actions: ['[Launch new-signup price test] | Owner: CMO | Timeframe: 3 weeks'],
    dissenting_opinions: [],
    contingencies: [],
    summary: 'A/B the price increase on new signups before a blanket change.',
    status: 'converged',
  },
  action_items: [
    { priority: 'MEDIUM', task: 'Launch new-signup price test', owner: 'CMO', due_date: '2026-09-05' },
  ],
  overall_risk_assessment: ['Competitive reaction if the test is noticed by rivals.'],
  synthesized_recommendations: ['A/B test before committing to a blanket price change.'],
  fallback_warnings: [],
}

/** A run that died mid-deliberation, so mock mode exercises the failure paths
 * (replay error card, sidebar status badge) without needing a real backend. */
export const failedDecisionDetail: DecisionDetail = {
  ...secondaryDecisionDetail,
  runId: 'run-20260812-141500',
  timestamp: '2026-08-12T14:15:00.000Z',
  prompt: 'Should we migrate the billing system to a third-party provider?',
  status: 'error',
  error_message: 'LLM provider unreachable after 3 attempts (connection refused).',
  board_decision: {} as DecisionDetail['board_decision'],
  action_items: [],
}

export const mockDecisionDetails: Record<string, DecisionDetail> = {
  [primaryDecisionDetail.runId]: primaryDecisionDetail,
  [followUpDecisionDetail.runId]: followUpDecisionDetail,
  [secondaryDecisionDetail.runId]: secondaryDecisionDetail,
  [failedDecisionDetail.runId]: failedDecisionDetail,
}

function toSummary(detail: DecisionDetail): DecisionSummary {
  const hasChildren = Object.values(mockDecisionDetails).some((d) => d.parentRunId === detail.runId)
  return {
    runId: detail.runId,
    timestamp: detail.timestamp,
    prompt: detail.prompt,
    decisionPoint: detail.decision_point ?? undefined,
    executiveSummary: detail.executive_summary,
    actionItemCount: detail.action_items.length,
    topRisks: detail.overall_risk_assessment.slice(0, 3),
    agentAlignment: Object.fromEntries(
      Object.entries(detail.agent_reports).map(([agent, report]) => [agent, report.alignment_score]),
    ),
    parentRunId: detail.parentRunId,
    hasChildren,
    status: detail.status,
  }
}

export const mockDecisionHistory: DecisionSummary[] = [
  failedDecisionDetail,
  followUpDecisionDetail,
  secondaryDecisionDetail,
  primaryDecisionDetail,
]
  .map(toSummary)
  .sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime())
