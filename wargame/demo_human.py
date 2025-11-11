from .agents.human import ScriptedHumanAgent
from .agents.heuristic import HeuristicAgent
from .run_match import run_headless_match

# Demo: Astra is scripted human, others are heuristics
agents = {
    "Astra": ScriptedHumanAgent("Astra", script=["ANNEX A B 3", "BUILD_MIL B", "STRIKE B C 3"]),
    "Borealis": HeuristicAgent("Borealis"),
    "Cinder": HeuristicAgent("Cinder"),
}

if __name__ == "__main__":
    final = run_headless_match(agents, max_turns=6, debug=True)
    print("\nDemo finished. Final state:\n")
    print(final)
