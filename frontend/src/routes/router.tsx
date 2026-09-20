import { Suspense, type ReactNode } from 'react'
import { createBrowserRouter } from 'react-router-dom'
import { AppShell } from './AppShell'
import { NotFoundPage } from './NotFoundPage'
import { ChatPage } from '../features/chat/ChatPage'
import { ComparePage, LoginPage, RegisterDashboardPage } from './lazyRoutes'

/** Both lazy routes show their own loading state once mounted; this only covers the chunk
 * fetch itself, which is a local request on a warm cache and near-invisible. */
function lazyRoute(element: ReactNode) {
  return <Suspense fallback={<p className="route-loading">Loading...</p>}>{element}</Suspense>
}

export const router = createBrowserRouter([
  // Outside AppShell: a signed-out visitor gets a bare page, no sidebar chrome that would
  // try to fetch a decision history it isn't authenticated to see.
  { path: '/login', element: lazyRoute(<LoginPage />) },
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
