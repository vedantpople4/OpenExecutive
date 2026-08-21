import { useEffect, useRef } from 'react'
import { PhaseCard } from './cards/PhaseCard'
import { BoardDecisionCard } from './cards/BoardDecisionCard'
import { ContinueDecisionButton } from './cards/ContinueDecisionButton'
import { ErrorCard } from './cards/ErrorCard'
import { UserPromptBubble } from './cards/UserPromptBubble'
import { EmptyStateMessage } from './cards/EmptyStateMessage'
import type { TranscriptCard } from './chat.types'
import './MessageList.css'

interface MessageListProps {
  prompt: string | null
  cards: TranscriptCard[]
  /** True while a persisted decision is being fetched for replay (distinct from a fresh, empty "/"). */
  isLoadingReplay?: boolean
  /** True when that fetch failed — distinct from "no decision yet" so we don't show the
   * example-prompts empty state for what's actually a load failure. */
  isErrorReplay?: boolean
  onPickExample?: (prompt: string) => void
  onContinueDecision?: (sourceRunId: string, sourcePrompt: string) => void
}

const NEAR_BOTTOM_THRESHOLD_PX = 120

export function MessageList({
  prompt,
  cards,
  isLoadingReplay,
  isErrorReplay,
  onPickExample,
  onContinueDecision,
}: MessageListProps) {
  const containerRef = useRef<HTMLDivElement>(null)
  const anchorRef = useRef<HTMLDivElement>(null)
  const wasNearBottomRef = useRef(true)

  useEffect(() => {
    const container = containerRef.current
    if (!container) return
    function handleScroll() {
      if (!container) return
      const distanceFromBottom = container.scrollHeight - container.scrollTop - container.clientHeight
      wasNearBottomRef.current = distanceFromBottom < NEAR_BOTTOM_THRESHOLD_PX
    }
    container.addEventListener('scroll', handleScroll)
    return () => container.removeEventListener('scroll', handleScroll)
  }, [])

  useEffect(() => {
    if (wasNearBottomRef.current && typeof anchorRef.current?.scrollIntoView === 'function') {
      anchorRef.current.scrollIntoView({ behavior: 'smooth', block: 'end' })
    }
  }, [cards.length])

  if (isLoadingReplay) {
    return <p className="message-list__loading">Loading decision...</p>
  }

  if (isErrorReplay) {
    return (
      <p className="message-list__loading" role="alert">
        Couldn't load this decision. It may have been removed.
      </p>
    )
  }

  if (!prompt) {
    return <EmptyStateMessage onPickExample={onPickExample} />
  }

  return (
    <div className="message-list" ref={containerRef}>
      <UserPromptBubble prompt={prompt} />
      {cards.map((card) => {
        if (card.kind === 'phase') return <PhaseCard key={card.id} phase={card} />
        if (card.kind === 'board_decision') {
          return (
            <BoardDecisionCard key={card.id} boardDecision={card.boardDecision}>
              {onContinueDecision && (
                <ContinueDecisionButton
                  onContinue={() => onContinueDecision(card.sourceRunId, card.sourcePrompt)}
                />
              )}
            </BoardDecisionCard>
          )
        }
        return <ErrorCard key={card.id} error={card} />
      })}
      <div ref={anchorRef} />
    </div>
  )
}
