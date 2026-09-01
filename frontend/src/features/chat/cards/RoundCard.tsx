import { useId, useState } from 'react'
import { AnimatePresence, motion } from 'motion/react'
import { AgentReportCard } from './AgentReportCard'
import { AgentSpeakingIndicator } from './AgentSpeakingIndicator'
import type { RoundCardData } from '../chat.types'
import { listVariants, itemVariants } from './transcriptMotion'
import './RoundCard.css'

const ROUND_LABELS: Record<number, string> = {
  1: 'Framing',
  2: 'Response',
  3: 'Response',
  4: 'Revision',
  5: 'Synthesis',
}

interface RoundCardProps {
  round: RoundCardData
}

export function RoundCard({ round }: RoundCardProps) {
  const [manuallyOpen, setManuallyOpen] = useState<boolean | null>(null)
  const isOpen = manuallyOpen ?? round.status === 'running'
  const panelId = useId()

  return (
    <div className="round-card">
      <button
        type="button"
        className="round-card__header"
        onClick={() => setManuallyOpen(!isOpen)}
        aria-expanded={isOpen}
        aria-controls={isOpen ? panelId : undefined}
      >
        <span className={`round-card__chevron ${isOpen ? 'round-card__chevron--open' : ''}`}>▸</span>
        <span className="round-card__title">
          Round {round.roundNumber}/10 — {ROUND_LABELS[round.roundNumber] ?? 'Deliberation'}
        </span>
        <span className={`round-card__status round-card__status--${round.status}`}>
          {round.status === 'running' ? 'in progress' : 'done'}
        </span>
      </button>

      {isOpen && (
        <motion.div
          id={panelId}
          className="round-card__body"
          variants={listVariants}
          initial="hidden"
          animate="show"
        >
          {/* One AnimatePresence over both lists: a speaking placeholder is replaced by its
              report card at the same position, so the exit and the entrance are two halves of
              one substitution and have to be tracked together. popLayout pulls the exiting node
              out of flow immediately, so the report lands where the placeholder was instead of
              waiting for the fade to finish. */}
          <AnimatePresence mode="popLayout">
            {round.speaking.map((entry) => (
              <motion.div key={`speaking-${entry.agentName}`} variants={itemVariants} exit="exit">
                <AgentSpeakingIndicator entry={entry} />
              </motion.div>
            ))}
            {round.reports.map((entry) => (
              <motion.div key={`report-${entry.agentName}`} variants={itemVariants} exit="exit">
                <AgentReportCard entry={entry} />
              </motion.div>
            ))}
          </AnimatePresence>
        </motion.div>
      )}
    </div>
  )
}
