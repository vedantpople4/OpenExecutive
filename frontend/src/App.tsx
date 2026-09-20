import { QueryClientProvider } from '@tanstack/react-query'
import { MotionConfig } from 'motion/react'
import { RouterProvider } from 'react-router-dom'
import { queryClient } from './queryClient'
import { router } from './routes/router'

export function App() {
  return (
    <QueryClientProvider client={queryClient}>
      {/* One provider instead of a useReducedMotion() check in every animated component.
          "user" switches transform animations off when the OS asks for reduced motion while
          leaving opacity alone -- a crossfade is the recommended fallback for a movement, not
          something to also suppress. Matches the existing hand-written guard on the sidebar
          collapse transition (routes/AppShell.css). */}
      <MotionConfig reducedMotion="user">
        <RouterProvider router={router} />
      </MotionConfig>
    </QueryClientProvider>
  )
}
