import { MessageList } from './MessageList'
import { PromptInput } from './PromptInput'
import { ContinuationBanner } from './ContinuationBanner'
import { DecisionSummaryTab } from './DecisionSummaryTab'
import type { ChatTab } from './hooks/useChatTab'
import type { BoardDecisionCardData, TranscriptCard } from './chat.types'
import './ChatPanel.css'

interface ChatPanelProps {
  prompt: string | null
  cards: TranscriptCard[]
  isLoadingReplay?: boolean
  isErrorReplay?: boolean
  isStreaming: boolean
  submitDisabled: boolean
  continuingFromPrompt?: string | null
  tab: ChatTab
  boardDecisionCard?: BoardDecisionCardData
  onSubmit: (prompt: string) => void
  onStop: () => void
  onContinueDecision: (sourceRunId: string, sourcePrompt: string) => void
  onCancelContinue: () => void
  onRetry?: () => void
}

/** Owns the scroll container + composes MessageList/PromptInput (or DecisionSummaryTab, when
 * the Summary tab is active). No fetching logic of its own. */
export function ChatPanel({
  prompt,
  cards,
  isLoadingReplay,
  isErrorReplay,
  isStreaming,
  submitDisabled,
  continuingFromPrompt,
  tab,
  boardDecisionCard,
  onSubmit,
  onStop,
  onContinueDecision,
  onCancelContinue,
  onRetry,
}: ChatPanelProps) {
  const showSummary = tab === 'summary' && boardDecisionCard !== undefined

  return (
    <div className="chat-panel">
      {showSummary ? (
        <DecisionSummaryTab card={boardDecisionCard} onContinueDecision={onContinueDecision} />
      ) : (
        <MessageList
          prompt={prompt}
          cards={cards}
          isLoadingReplay={isLoadingReplay}
          isErrorReplay={isErrorReplay}
          onPickExample={onSubmit}
          onContinueDecision={onContinueDecision}
          onRetry={onRetry}
        />
      )}
      {continuingFromPrompt && (
        <ContinuationBanner parentPrompt={continuingFromPrompt} onCancel={onCancelContinue} />
      )}
      <PromptInput isStreaming={isStreaming} disabled={submitDisabled} onSubmit={onSubmit} onStop={onStop} />
    </div>
  )
}
