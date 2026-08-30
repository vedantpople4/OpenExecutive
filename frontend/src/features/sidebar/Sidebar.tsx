import { Link, useNavigate } from 'react-router-dom'
import { SelectionPanel } from './SelectionPanel'
import { TeamRosterPanel } from './TeamRosterPanel'
import { HistorySection } from './HistorySection'
import { useRunStore } from '../../stores/useRunStore'
import './Sidebar.css'

interface SidebarProps {
  collapsed?: boolean
  onToggleCollapse?: () => void
}

/** Two chevrons pointing at the edge the panel moves toward. */
function CollapseIcon({ collapsed }: { collapsed: boolean }) {
  return (
    <svg
      width="16"
      height="16"
      viewBox="0 0 16 16"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.6"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      {collapsed ? (
        <>
          <path d="M6 3l4 5-4 5" />
          <path d="M2 3v10" />
        </>
      ) : (
        <>
          <path d="M10 3L6 8l4 5" />
          <path d="M14 3v10" />
        </>
      )}
    </svg>
  )
}

export function Sidebar({ collapsed = false, onToggleCollapse }: SidebarProps) {
  const navigate = useNavigate()
  const resetActiveRun = useRunStore((s) => s.resetActiveRun)

  function handleNewDecision() {
    resetActiveRun()
    navigate('/')
  }

  return (
    <aside className={`sidebar${collapsed ? ' sidebar--collapsed' : ''}`}>
      <div className="sidebar__top">
        {!collapsed && <div className="sidebar__brand">OpenExec</div>}
        {onToggleCollapse && (
          <button
            type="button"
            className="sidebar__collapse"
            onClick={onToggleCollapse}
            aria-label={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
            aria-expanded={!collapsed}
            title={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
          >
            <CollapseIcon collapsed={collapsed} />
          </button>
        )}
      </div>

      {/* Unmounted rather than hidden with CSS: HistorySection drives a paged
          query, and keeping it mounted behind display:none would go on fetching
          pages nobody can see. */}
      {collapsed ? (
        <button
          type="button"
          className="sidebar__new-chat sidebar__new-chat--icon"
          onClick={handleNewDecision}
          aria-label="New decision"
          title="New decision"
        >
          +
        </button>
      ) : (
        <>
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
        </>
      )}
    </aside>
  )
}
