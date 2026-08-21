import { BoardDecisionCard } from './cards/BoardDecisionCard'
import { ContinueDecisionButton } from './cards/ContinueDecisionButton'
import type { BoardDecisionCardData } from './chat.types'
import './DecisionSummaryTab.css'

interface DecisionSummaryTabProps {
  card: BoardDecisionCardData
  onContinueDecision?: (sourceRunId: string, sourcePrompt: string) => void
}

/** Alternate tab body for ChatPage — reuses BoardDecisionCard, read-only, without the full
 * phase/round transcript above it. */
export function DecisionSummaryTab({ card, onContinueDecision }: DecisionSummaryTabProps) {
  return (
    <div className="decision-summary-tab">
      <BoardDecisionCard boardDecision={card.boardDecision}>
        {onContinueDecision && (
          <ContinueDecisionButton
            onContinue={() => onContinueDecision(card.sourceRunId, card.sourcePrompt)}
          />
        )}
      </BoardDecisionCard>
    </div>
  )
}
