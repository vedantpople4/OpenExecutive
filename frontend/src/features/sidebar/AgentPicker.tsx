import { RoleBadge } from '../../components/RoleBadge'
import { useRunStore } from '../../stores/useRunStore'
import type { CXOName } from '../../api/types'
import './AgentPicker.css'

const AGENTS: { name: CXOName; label: string }[] = [
  { name: 'ceo', label: 'CEO' },
  { name: 'cfo', label: 'CFO' },
  { name: 'cto', label: 'CTO' },
  { name: 'cmo', label: 'CMO' },
]

export function AgentPicker() {
  const selectedAgents = useRunStore((s) => s.selectedAgents)
  const toggleAgent = useRunStore((s) => s.toggleAgent)

  return (
    <div className="agent-picker">
      {AGENTS.map((agent) => (
        <label key={agent.name} className="agent-picker__option">
          <input
            type="checkbox"
            checked={selectedAgents.includes(agent.name)}
            onChange={() => toggleAgent(agent.name)}
          />
          <RoleBadge name={agent.name} />
          <span>{agent.label}</span>
        </label>
      ))}
      {!selectedAgents.includes('ceo') && (
        <p className="agent-picker__warning">No synthesis without CEO.</p>
      )}
    </div>
  )
}
