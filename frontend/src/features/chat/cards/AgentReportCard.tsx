import { RoleBadge } from '../../../components/RoleBadge'
import { AlignmentScoreMeter } from '../../../components/AlignmentScoreMeter'
import { CollapsibleSection } from '../../../components/CollapsibleSection'
import type { AgentReportEntry } from '../chat.types'
import './AgentReportCard.css'

interface AgentReportCardProps {
  entry: AgentReportEntry
}

function ListSection({ label, items }: { label: string; items: string[] }) {
  if (items.length === 0) return null
  return (
    <div className="agent-report-card__list-section">
      <h4>{label}</h4>
      <ul>
        {items.map((item, i) => (
          <li key={i}>{item}</li>
        ))}
      </ul>
    </div>
  )
}

/**
 * Renders one AgentReport. Reused for Phase-2 blind reports, Phase-2.5 specialist/team
 * reports, and Phase-3 round reports — it knows nothing about phases, rounds, or streaming
 * transport. Round-only fields render via the optional RoundDeltaSection below.
 */
export function AgentReportCard({ entry }: AgentReportCardProps) {
  const { agentName, report, parentCXO } = entry
  const isRoundReport = report.round_number > 0

  return (
    <div className="agent-report-card">
      <div className="agent-report-card__header">
        <RoleBadge name={agentName} />
        <span className="agent-report-card__title">{report.title}</span>
        {parentCXO && <span className="agent-report-card__parent">reporting to {parentCXO.toUpperCase()}</span>}
        {report.is_fallback && <span className="agent-report-card__fallback-badge">fallback response</span>}
        <AlignmentScoreMeter score={report.alignment_score} />
      </div>

      <p className="agent-report-card__summary">{report.summary}</p>

      <CollapsibleSection title="Details">
        <ListSection label="Key findings" items={report.key_findings} />
        <ListSection label="Recommendations" items={report.recommendations} />
        <ListSection label="Risks" items={report.risks} />
        <ListSection label="Contingencies" items={report.contingencies} />
      </CollapsibleSection>

      {isRoundReport && <RoundDeltaSection report={report} />}
    </div>
  )
}

function RoundDeltaSection({ report }: { report: AgentReportEntry['report'] }) {
  const hasDelta =
    report.agreements.length > 0 ||
    report.conflicts.length > 0 ||
    report.required_changes.length > 0 ||
    report.revised_recommendations.length > 0

  if (!hasDelta) return null

  return (
    <div className="agent-report-card__delta">
      <ListSection label="Agreements" items={report.agreements} />
      <ListSection label="Conflicts" items={report.conflicts} />
      <ListSection label="Required changes" items={report.required_changes} />
      <ListSection label="Revised recommendations" items={report.revised_recommendations} />
    </div>
  )
}
