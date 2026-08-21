import { createBrowserRouter } from 'react-router-dom'
import { AppShell } from './AppShell'
import { NotFoundPage } from './NotFoundPage'
import { ChatPage } from '../features/chat/ChatPage'
import { ComparePage } from '../features/compare/ComparePage'
import { RegisterDashboardPage } from '../features/dashboard/RegisterDashboardPage'

export const router = createBrowserRouter([
  {
    element: <AppShell />,
    children: [
      { path: '/', element: <ChatPage /> },
      { path: '/chat/:runId', element: <ChatPage /> },
      { path: '/compare', element: <ComparePage /> },
      { path: '/compare/:oldId/:newId', element: <ComparePage /> },
      { path: '/dashboard', element: <RegisterDashboardPage /> },
      { path: '*', element: <NotFoundPage /> },
    ],
  },
])
