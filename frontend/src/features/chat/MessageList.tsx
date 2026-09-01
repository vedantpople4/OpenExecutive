import { useEffect, useMemo, useRef } from 'react'
import { motion } from 'motion/react'
import { PhaseCard } from './cards/PhaseCard'
import { BoardDecisionCard } from './cards/BoardDecisionCard'
import { ContinueDecisionButton } from './cards/ContinueDecisionButton'
import { ErrorCard } from './cards/ErrorCard'
import { UserPromptBubble } from './cards/UserPromptBubble'
import { EmptyStateMessage } from './cards/EmptyStateMessage'
import { describeLatestActivity } from './describeLatestActivity'
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
  /** Re-asks the prompt as a fresh run. Absent when there is no prompt to re-ask with. */
  onRetry?: () => void
  /** Gates the live region: announcements are for a run unfolding, not a replayed transcript
   * that arrives all at once. */
  isStreaming?: boolean
}

const NEAR_BOTTOM_THRESHOLD_PX = 120

export function MessageList({
  prompt,
  cards,
  isLoadingReplay,
  isErrorReplay,
  onPickExample,
  onContinueDecision,
  onRetry,
  isStreaming,
}: MessageListProps) {
  const latestActivity = useMemo(
    () => (isStreaming ? describeLatestActivity(cards) : null),
    [isStreaming, cards],
  )
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
      {/* Polite, so it waits for a gap rather than cutting across whatever the user is
          reading. role="status" carries the same politeness on the browsers that ignore a
          bare aria-live on a non-live-region element. */}
      <div className="sr-only" role="status" aria-live="polite">
        {latestActivity}
      </div>
      <UserPromptBubble prompt={prompt} />
      {cards.map((card) => (
        // Transform and opacity only -- deliberately never height. The effect below scrolls to
        // an anchor whenever cards.length changes, and animating height would keep moving that
        // anchor while the scroll is still in flight, so the view would chase it down the page.
        //
        // No AnimatePresence: this list is append-only, cards are never removed, and it exists
        // for exit animations. Entrance only needs initial -> animate, which runs on mount --
        // and because the keys are stable, an existing card does not remount when a new one
        // arrives, so nothing already on screen replays its entrance.
        <motion.div
          key={card.id}
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.24, ease: 'easeOut' }}
        >
          {card.kind === 'phase' && <PhaseCard phase={card} />}
          {card.kind === 'board_decision' && (
            <BoardDecisionCard boardDecision={card.boardDecision}>
              {onContinueDecision && (
                <ContinueDecisionButton
                  onContinue={() => onContinueDecision(card.sourceRunId, card.sourcePrompt)}
                />
              )}
            </BoardDecisionCard>
          )}
          {card.kind === 'error' && (
            // Not on a stopped run: the user stopped it themselves, so the way to continue
            // is the prompt box, not a button that implies something went wrong.
            <ErrorCard error={card} onRetry={card.variant === 'stopped' ? undefined : onRetry} />
          )}
        </motion.div>
      ))}
      <div ref={anchorRef} />
    </div>
  )
}
