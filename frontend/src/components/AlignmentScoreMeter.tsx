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
        <span className="alignment-meter__fill" style={{ width: `${percent}%` }} />
      </span>
      <span className="alignment-meter__label">{percent}%</span>
    </span>
  )
}
