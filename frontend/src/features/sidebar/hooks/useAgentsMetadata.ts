import { useQuery } from '@tanstack/react-query'
import { getAgents } from '../../../api/endpoints'

export function useAgentsMetadata() {
  return useQuery({ queryKey: ['agents'], queryFn: getAgents, staleTime: Infinity })
}
