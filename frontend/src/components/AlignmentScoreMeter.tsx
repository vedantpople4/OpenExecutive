import { motion } from 'motion/react'
import './AlignmentScoreMeter.css'

interface AlignmentScoreMeterProps {
  score: number // 0.0-1.0
}

export function AlignmentScoreMeter({ score }: AlignmentScoreMeterProps) {
  const clamped = Math.max(0, Math.min(1, score))
  const percent = Math.round(clamped * 100)

  return (
    <span className="alignment-meter" title={`Alignment score: ${percent}%`}>
      <span className="alignment-meter__track">
        {/* scaleX rather than width: a transform is what <MotionConfig reducedMotion="user">
            switches off, so this reads as a measurement being taken for everyone else and
            snaps straight to its value for anyone who asked the OS for less motion.
            Animating width would ignore that setting and thrash layout besides. */}
        <motion.span
          className="alignment-meter__fill"
          style={{ transformOrigin: 'left' }}
          initial={{ scaleX: 0 }}
          animate={{ scaleX: clamped }}
          transition={{ duration: 0.45, ease: 'easeOut' }}
        />
      </span>
      <span className="alignment-meter__label">{percent}%</span>
    </span>
  )
}
