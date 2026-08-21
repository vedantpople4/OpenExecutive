/** "financial_analyst" -> "Financial Analyst" */
export function formatAgentName(name: string): string {
  return name
    .split('_')
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(' ')
}
