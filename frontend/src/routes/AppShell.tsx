import { useEffect, useState } from 'react'
import { Outlet } from 'react-router-dom'
import { Sidebar } from '../features/sidebar/Sidebar'
import './AppShell.css'

const COLLAPSE_KEY = 'openexec.sidebarCollapsed'

/** Guarded because vite.config.ts runs vitest with `environment: 'node'`,
 * where there is no localStorage — an unguarded read throws at import time and
 * takes every test that touches the shell down with it. */
function readCollapsed(): boolean {
  try {
    return globalThis.localStorage?.getItem(COLLAPSE_KEY) === 'true'
  } catch {
    return false
  }
}

export function AppShell() {
  const [collapsed, setCollapsed] = useState(readCollapsed)

  useEffect(() => {
    try {
      globalThis.localStorage?.setItem(COLLAPSE_KEY, String(collapsed))
    } catch {
      // Private mode or a storage quota — the toggle still works for this
      // session, it just will not be remembered.
    }
  }, [collapsed])

  return (
    <div className={`app-shell${collapsed ? ' app-shell--collapsed' : ''}`}>
      <Sidebar collapsed={collapsed} onToggleCollapse={() => setCollapsed((c) => !c)} />
      <main className="app-shell__content">
        <Outlet />
      </main>
    </div>
  )
}
