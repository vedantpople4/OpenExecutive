import { useState } from 'react'
import { AnimatePresence, motion } from 'motion/react'
import { AgentReportCard } from './AgentReportCard'
import { AgentSpeakingIndicator } from './AgentSpeakingIndicator'
import { RoundCard } from './RoundCard'
import type { PhaseCardData, PhaseKind } from '../chat.types'
import { listVariants, itemVariants } from './transcriptMotion'
import './PhaseCard.css'

const PHASE_LABELS: Record<PhaseKind, string> = {
  inception: 'Inception',
  analysis: 'Analysis',
  team_analysis: 'Team Analysis',
  deliberation: 'Deliberation',
}

interface PhaseCardProps {
  phase: PhaseCardData;
}

export function PhaseCard({ phase }: PhaseCardProps) {
  const [manuallyOpen, setManuallyOpen] = useState<boolean | null>(null)
  const isOpen = manuallyOpen ?? phase.status === 'running'

  return (
    <div className="phase-card">
      <button
        type="button"
        className="phase-card__header"
        onClick={() => setManuallyOpen(!isOpen)}
        aria-expanded={isOpen}
      >
        <span className={`phase-card__chevron ${isOpen ? 'phase-card__chevron--open' : ''}`}>▸</span>
        <span className="phase-card__title">{PHASE_LABELS[phase.phase]}</span>
        <span className={`phase-card__status phase-card__status--${phase.status}`}>
          {phase.status === 'running' ? 'in progress' : 'done'}
        </span>
      </button>

      {isOpen && (
        <motion.div
          className="phase-card__body"
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
            {phase.speaking.map((entry) => (
              <motion.div key={`speaking-${entry.agentName}`} variants={itemVariants} exit="exit">
                <AgentSpeakingIndicator entry={entry} />
              </motion.div>
            ))}
            {phase.reports.map((entry) => (
              <motion.div key={`report-${entry.agentName}`} variants={itemVariants} exit="exit">
                <AgentReportCard entry={entry} />
              </motion.div>
            ))}
          </AnimatePresence>
          {phase.rounds.map((round) => (
            <RoundCard key={round.id} round={round} />
          ))}
        </motion.div>
      )}
    </div>
  )
}
