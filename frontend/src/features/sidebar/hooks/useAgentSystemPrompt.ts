import { useQuery } from '@tanstack/react-query'
import { getAgentSystemPrompt } from '../../../api/endpoints'

export function useAgentSystemPrompt(agentName: string) {
  return useQuery({
    queryKey: ['agent-prompt', agentName],
    queryFn: () => getAgentSystemPrompt(agentName),
    staleTime: Infinity,
  })
}
