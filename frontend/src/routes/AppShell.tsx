import { Outlet } from 'react-router-dom'
import { Sidebar } from '../features/sidebar/Sidebar'
import './AppShell.css'

export function AppShell() {
  return (
    <div className="app-shell">
      <Sidebar />
      <main className="app-shell__content">
        <Outlet />
      </main>
    </div>
  )
}
