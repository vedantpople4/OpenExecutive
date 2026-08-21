import { useQuery } from '@tanstack/react-query'
import { getTeamStructure } from '../../../api/endpoints'

export function useTeamStructure() {
  return useQuery({ queryKey: ['team-structure'], queryFn: getTeamStructure, staleTime: Infinity })
}
