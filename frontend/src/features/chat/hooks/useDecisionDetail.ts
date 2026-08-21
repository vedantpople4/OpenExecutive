import { useQuery } from '@tanstack/react-query'
import { getDecisionDetail } from '../../../api/endpoints'

export function useDecisionDetail(runId: string | null) {
  return useQuery({
    queryKey: ['decision-detail', runId],
    queryFn: () => getDecisionDetail(runId as string),
    enabled: runId !== null,
    staleTime: 10_000,
  })
}
