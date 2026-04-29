# This is just a patch - do not use
# Priority 3: Inject memory context into simulation
memory_context = memory_system.get_memory_context(prompt)
if memory_context:
    print("\n📚 Memory context loaded from past decisions")
    state.data_corpus["memory_context.md"] = memory_context

# Create orchestrator and run simulation
orchestrator = Orchestrator(registry)
orchestrator.initialize(state)

try:
    final_results = orchestrator.run()

    # Priority 3: Store conversation in memory
    memory_system.store_conversation(prompt, final_results)
    print("✓ Conversation stored in memory")

    # Quantify risks
    final_results = quantify_risks(final_results)