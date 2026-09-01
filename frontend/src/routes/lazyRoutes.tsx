import { lazy } from 'react'

/**
 * The code-split route components, kept in their own module so router.tsx can go on
 * exporting the router itself. A file that exports both components and a non-component
 * breaks fast refresh, which is what oxlint's react(only-export-components) is guarding.
 *
 * Chat is deliberately absent: it is the app, and belongs in the main bundle.
 */
export const ComparePage = lazy(() =>
  import('../features/compare/ComparePage').then((m) => ({ default: m.ComparePage })),
)

export const RegisterDashboardPage = lazy(() =>
  import('../features/dashboard/RegisterDashboardPage').then((m) => ({
    default: m.RegisterDashboardPage,
  })),
)
