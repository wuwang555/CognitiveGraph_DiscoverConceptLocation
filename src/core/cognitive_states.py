"""
Cognitive State Module
-------------
Define CognitiveState enum and CognitiveStateManager class to manage state transitions and subjective energy updates.
"""

import random
from enum import Enum
from collections import defaultdict
from typing import List, Dict, Any

# Import state transition matrix and energy ranges from config
from config import STATE_TRANSITION_MATRIX, STATE_ENERGY_RANGES

random.seed(42)
class CognitiveState(Enum):
    """Cognitive state enumeration, corresponding to four typical cognitive states."""
    FOCUSED = "专注状态"
    EXPLORATORY = "探索状态"
    FATIGUED = "疲劳状态"
    INSPIRED = "灵感状态"


class CognitiveStateManager:
    """Cognitive state manager, maintaining current state, subjective energy, and history.

    State transitions are controlled by a Markov chain (transition matrix loaded from config); upon state change,
    subjective energy is randomly updated within the corresponding range.
    """

    def __init__(self):
        self.current_state = CognitiveState.FOCUSED
        self.subjective_energy = 1.5
        self.cognitive_energy_history: List[Dict[str, Any]] = []

    def update_cognitive_state(self) -> None:
        """Update cognitive state according to the transition matrix.

        Transition probabilities are obtained from config; decide the next state randomly. If state changes,
        call _update_subjective_energy. Regardless of state change, record current state and energy in history.
        """
        current_state_name = self.current_state.name
        transition_probs = STATE_TRANSITION_MATRIX[current_state_name]

        rand_val = random.random()
        cumulative_prob = 0

        for new_state_name, prob in transition_probs.items():
            cumulative_prob += prob
            if rand_val <= cumulative_prob:
                new_state = CognitiveState[new_state_name]
                if new_state != self.current_state:
                    self.current_state = new_state
                    self._update_subjective_energy()
                break

        # Record iteration number (using history length as iteration index)
        iteration_count = len(self.cognitive_energy_history)
        self.cognitive_energy_history.append({
            'iteration': iteration_count,
            'state': self.current_state,
            'energy': self.subjective_energy
        })

    def _update_subjective_energy(self) -> None:
        """Update subjective cognitive energy based on the current state.

        The new energy is uniformly sampled from the state's energy range (defined in config), clamped to [0.1, 3.0].
        """
        state_name = self.current_state.name
        energy_range = STATE_ENERGY_RANGES[state_name]
        self.subjective_energy = random.uniform(energy_range[0], energy_range[1])
        self.subjective_energy = max(0.1, min(3.0, self.subjective_energy))


if __name__ == "__main__":
    mgr = CognitiveStateManager()
    for _ in range(10):
        mgr.update_cognitive_state()
        print(f"State: {mgr.current_state.value}, Energy: {mgr.subjective_energy:.2f}")