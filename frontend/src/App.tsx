import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { MotionConfig } from 'motion/react'
import { RouterProvider } from 'react-router-dom'
import { router } from './routes/router'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 30_000,
      refetchOnWindowFocus: false,
    },
  },
})

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
