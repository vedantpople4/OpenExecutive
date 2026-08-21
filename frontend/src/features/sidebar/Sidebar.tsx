import { Link, useNavigate } from 'react-router-dom'
import { SelectionPanel } from './SelectionPanel'
import { TeamRosterPanel } from './TeamRosterPanel'
import { HistorySection } from './HistorySection'
import { useRunStore } from '../../stores/useRunStore'
import './Sidebar.css'

export function Sidebar() {
  const navigate = useNavigate()
  const resetActiveRun = useRunStore((s) => s.resetActiveRun)

  function handleNewDecision() {
    resetActiveRun()
    navigate('/')
  }

  return (
    <aside className="sidebar">
      <div className="sidebar__brand">OpenExec</div>

      <SelectionPanel />

      <TeamRosterPanel />

      <button type="button" className="sidebar__new-chat" onClick={handleNewDecision}>
        + New Decision
      </button>

      <HistorySection />

      <nav className="sidebar__footer-nav" aria-label="Secondary views">
        <Link to="/compare">Compare</Link>
        <Link to="/dashboard">Dashboard</Link>
      </nav>
    </aside>
  )
}
