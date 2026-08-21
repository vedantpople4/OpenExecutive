import { formatAgentName } from '../../lib/formatAgentName'
import type { Specialist } from '../../api/types'
import './SpecialistList.css'

interface SpecialistListProps {
  specialists: Specialist[]
}

export function SpecialistList({ specialists }: SpecialistListProps) {
  if (specialists.length === 0) return null

  return (
    <div className="specialist-list">
      {specialists.map((specialist) => (
        <span key={specialist.name} className="specialist-list__chip">
          {formatAgentName(specialist.name)}
        </span>
      ))}
    </div>
  )
}
