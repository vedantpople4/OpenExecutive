import { lazy, Suspense } from 'react'
import { createBrowserRouter } from 'react-router-dom'
import { AppShell } from './AppShell'
import { NotFoundPage } from './NotFoundPage'
import { ChatPage } from '../features/chat/ChatPage'

// Chat is the app -- it stays in the main bundle. Compare and Dashboard are places you go
// occasionally, and both drag in their own chart and diff components, so making every first
// paint download them was the bulk of the 500KB single-chunk warning from `npm run build`.
const ComparePage = lazy(() =>
  import('../features/compare/ComparePage').then((m) => ({ default: m.ComparePage })),
)
const RegisterDashboardPage = lazy(() =>
  import('../features/dashboard/RegisterDashboardPage').then((m) => ({
    default: m.RegisterDashboardPage,
  })),
)

/** Both lazy routes already show their own loading state once mounted; this only covers the
 * chunk fetch itself, which is a local request on a warm cache and near-invisible. */
function lazyRoute(element: React.ReactNode) {
  return <Suspense fallback={<p className="route-loading">Loading...</p>}>{element}</Suspense>
}

export const router = createBrowserRouter([
  {
    element: <AppShell />,
    children: [
      { path: '/', element: <ChatPage /> },
      { path: '/chat/:runId', element: <ChatPage /> },
      { path: '/compare', element: lazyRoute(<ComparePage />) },
      { path: '/compare/:oldId/:newId', element: lazyRoute(<ComparePage />) },
      { path: '/dashboard', element: lazyRoute(<RegisterDashboardPage />) },
      { path: '*', element: <NotFoundPage /> },
    ],
  },
])
