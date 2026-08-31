import { useMutation, useQueryClient } from '@tanstack/react-query'
import { deleteDecision } from '../../../api/endpoints'

/** Removes a decision and refreshes the history list.
 *
 * Invalidation rather than an optimistic cache edit: the list is paged
 * (useInfiniteQuery), so surgically removing one item would leave that page
 * one short and shift every subsequent cursor boundary. A refetch of the pages
 * already loaded is cheap and always consistent with the server.
 */
export function useDeleteDecision() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (runId: string) => deleteDecision(runId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['decision-history'] })
      // The dashboard counts every stored decision, so it is stale now too.
      queryClient.invalidateQueries({ queryKey: ['register-dashboard'] })
    },
  })
}
