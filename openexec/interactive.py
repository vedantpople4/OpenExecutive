"""
Interactive discussion mode for OpenExec.

This module provides interactive follow-up capabilities
for questioning executive board recommendations.
"""

import sys
from typing import Dict, Any, Optional
from openexec.agents.interface import AgentReport


class InteractiveDiscussion:
    """Interactive discussion interface for OpenExec."""

    def __init__(self, simulation_results: Dict[str, Any]):
        """Initialize interactive discussion with simulation results.

        Args:
            simulation_results: The results from a simulation run
        """
        self.results = simulation_results
        self.history = []  # Track conversation history

    def start_discussion(self) -> None:
        """Start interactive discussion mode."""
        print("OpenExec Interactive Discussion Mode")
        print("Type your questions or 'quit' to exit\n")

        while True:
            try:
                user_input = input("Question: ").strip()

                if user_input.lower() in ['quit', 'exit', 'q']:
                    print("Goodbye!")
                    break

                if user_input == "":
                    continue

                response = self._process_question(user_input)
                print(f"\nResponse: {response}\n")

            except KeyboardInterrupt:
                print("\nGoodbye!")
                break
            except Exception as e:
                print(f"Error: {e}")

    def _process_question(self, question: str) -> str:
        """Process a question and return appropriate response.

        Args:
            question: The user's question

        Returns:
            Formatted response
        """
        question = question.lower().strip()

        # Handle specific question types
        if "what is" in question or "what does" in question:
            return self._handle_what_question(question)
        elif "how" in question:
            return self._handle_how_question(question)
        elif "why" in question:
            return self._handle_why_question(question)
        elif "when" in question:
            return self._handle_when_question(question)
        elif "compare" in question or "versus" in question:
            return self._handle_comparison_question(question)
        else:
            return self._handle_general_question(question)

    def _handle_what_question(self, question: str) -> str:
        """Handle 'what' questions."""
        if "risk" in question:
            return self._extract_risks_info()
        elif "recommendation" in question:
            return self._extract_recommendations()
        elif "finding" in question:
            return self._extract_findings()
        else:
            return "Could you be more specific about what you're asking?"

    def _handle_how_question(self, question: str) -> str:
        """Handle 'how' questions."""
        return "I can help explain the recommendations. What specifically would you like to know about how to implement them?"

    def _handle_why_question(self, question: str) -> str:
        """Handle 'why' questions."""
        return "The recommendations are based on the analysis from the executive board simulation. What specific aspect would you like me to explain further?"

    def _handle_when_question(self, question: str) -> str:
        """Handle 'when' questions."""
        return "The timeline for implementation would depend on your specific business context. What's your target timeframe?"

    def _handle_comparison_question(self, question: str) -> str:
        """Handle comparison questions."""
        return "I can help compare different options. What specifically would you like to compare?"

    def _handle_general_question(self, question: str) -> str:
        """Handle general questions."""
        # Try to find relevant information in the results
        if "recommend" in question and "cto" in question:
            return self._get_agent_recommendation("cto")
        elif "recommend" in question and "cfo" in question:
            return self._get_agent_recommendation("cfo")
        elif "recommend" in question and "ceo" in question:
            return self._get_agent_recommendation("ceo")
        elif "recommend" in question and "cmo" in question:
            return self._get_agent_recommendation("cmo")
        else:
            return "I can help with that. Could you be more specific about what you're looking for?"

    def _extract_risks_info(self) -> str:
        """Extract risk information from results."""
        risks = []
        agent_reports = self.results.get('agent_reports', {})
        for agent_name, report in agent_reports.items():
            agent_risks = report.get('risks', [])
            if agent_risks:
                risks.extend([f"{agent_name.upper()}: {risk}" for risk in agent_risks])

        if risks:
            return "Key risks identified:\n" + "\n".join(risks)
        else:
            return "No specific risks were identified in the analysis."

    def _extract_recommendations(self) -> str:
        """Extract recommendations from results."""
        recommendations = []
        agent_reports = self.results.get('agent_reports', {})
        for agent_name, report in agent_reports.items():
            agent_recs = report.get('recommendations', [])
            if agent_recs:
                recommendations.extend([f"{agent_name.upper()}: {rec}" for rec in agent_recs])

        if recommendations:
            return "Current recommendations:\n" + "\n".join(recommendations)
        else:
            return "No specific recommendations were identified."

    def _extract_findings(self) -> str:
        """Extract key findings from results."""
        findings = []
        agent_reports = self.results.get('agent_reports', {})
        for agent_name, report in agent_reports.items():
            agent_findings = report.get('key_findings', [])
            if agent_findings:
                findings.extend([f"{agent_name.upper()}: {finding}" for finding in agent_findings])

        if findings:
            return "Key findings:\n" + "\n".join(findings)
        else:
            return "No specific findings were identified."

    def _get_agent_recommendation(self, agent_name: str) -> str:
        """Get specific agent recommendations."""
        agent_reports = self.results.get('agent_reports', {})
        if agent_name in agent_reports:
            report = agent_reports[agent_name]
            recommendations = report.get('recommendations', [])
            if recommendations:
                rec_list = "\n".join([f"- {rec}" for rec in recommendations])
                return f"{agent_name.upper()} recommendations:\n{rec_list}"
            else:
                return f"No specific recommendations from {agent_name.upper()}."
        else:
            return f"No report found for {agent_name.upper()}."

    def get_help(self) -> str:
        """Get help information for interactive mode."""
        return """
Available commands:
- Ask questions about recommendations, risks, or findings
- Type 'quit' or 'exit' to exit
- You can ask: "What are the risks?" or "How should I implement the CTO recommendations?"
        """