import { Link } from 'react-router-dom'
import { useDecisionDetail } from './hooks/useDecisionDetail'
import './BranchChain.css'

interface BranchChainProps {
  parentRunId: string
}

function truncate(text: string, max = 60): string {
  return text.length > max ? `${text.slice(0, max - 1)}…` : text
}

/** Breadcrumb shown when the current run was started via "Continue this decision" — the real
 * parent/child tree edge (see plan Section 9), as opposed to the flat, recency-grouped history list. */
export function BranchChain({ parentRunId }: BranchChainProps) {
  const { data: parent } = useDecisionDetail(parentRunId)

  return (
    <div className="branch-chain">
      <span>↳ Continued from</span>
      <Link to={`/chat/${parentRunId}`}>{parent ? truncate(parent.prompt) : parentRunId}</Link>
    </div>
  )
}
