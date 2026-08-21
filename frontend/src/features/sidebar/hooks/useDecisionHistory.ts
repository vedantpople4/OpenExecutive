import { useQuery } from '@tanstack/react-query'
import { getDecisionHistory } from '../../../api/endpoints'

export function useDecisionHistory() {
  return useQuery({ queryKey: ['decision-history'], queryFn: getDecisionHistory, staleTime: 10_000 })
}
