import json
from typing import Dict, Any
from openexec.orchestrator import Orchestrator, SimulationState
from openexec.agents import AgentRegistry, register_default_agents

from openexec.event_store import EventStore


def run_stress_test():
    # 1. Setup: Scenario 1 - Tech Debt vs Market Window
    core_prompt = (
        "Our main competitor just leaked a feature that handles real-time data sync. "
        "We have a stable but slow legacy engine. Should we rush a 'hacky' implementation ' "
        "to hit the Q3 window, or spend 4 months rebuilding the core engine to avoid "
        "catastrophic tech debt?"
    )

    data_corpus = {
        "current_latency.txt": "Current search latency: 200ms. User complaints about speed increased by 40% last month.",
        "competitor_leak.md": "Competitor X is launching 'InstantSync' in August. Expected latency: 20ms. "
                             "Market anticipation is very high; early testers report 2x productivity gain.",
        "customer_churn_risk.csv": "Churn risk for high-value accounts: 15% if we don't match real-time sync by Q4."
    }

    print("\n" + "="*60)
    print("STRESS TEST: Tech Debt vs Market Window")
    print("="*60)

    # 2. Initialize Infrastructure
    registry = AgentRegistry()
    # We must register the agents to the registration instance we are passing to the orchestrator
    from openexec.agents import register_default_agents

    # The current register_default_agents uses the module-level registry.
    # We need to make sure it uses OUR registry instance.
    import openexec.agents as agents_mod
    agents_mod.registry = registry
    register_default_agents()

    # Ensure teams are enabled if we want the hierarchical flow
    orchestrator = Orchestrator(registry, verbose=True)
    orchestrator.teams_enabled = True

    state = SimulationState(
        core_prompt=core_prompt,
        data_corpus=data_corpus,
        decision_point="Strategic Technical Direction Q3"
    )

    # Use a dummy event store to capture the trace
    event_store = EventStore()
    orchestrator.set_event_store(event_store)

    orchestrator.initialize(state)

    # 3. Run Full Flow
    try:
        # This calls inception -> analysis -> teams -> deliberation -> synthesis
        final_report = orchestrator.run()

        print("\n" + "="*60)
        print("FINAL BOARD DECISION")
        print("="*60)

        decision = final_report.get("board_decision", {})
        print(f"Summary: {decision.get('summary', 'N/A')}")
        print("\nConsensus Points:")
        for p in decision.get("consensus_points", []):
            print(f"- {p}")

        print("\nDissent Points:")
        for d in decision.get("dissent_points", []):
            print(f"- {d}")

        print("\nFinal Priority Actions:")
        for a in decision.get("final_priority_actions", []):
            print(f"- {a}")

    except Exception as e:
        print(f"\n❌ STRESS TEST FAILED: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    run_stress_test()
