"""AIMA search problem for planning a segment of the NAO choreography."""

from collections import namedtuple

from aima.search import Problem, astar_search

import positions


_State = namedtuple(
    "_State",
    (
        "last_action",
        "previous_action",
        "elapsed_ms",
        "used_mask",
        "repeated_mask",
        "required_mask",
    ),
)

DIVERSITY_REPEAT_PENALTY = 4.0
GLOBAL_REUSE_PENALTY = 1.5
MAX_INTERMEDIATE_USES = 2


class NaoProblem(Problem):
    """Find a low-cost, posture-valid action sequence for one song segment."""

    def __init__(
        self,
        start_action,
        target_action,
        target_duration,
        target_energy,
        global_used_intermediates,
        executable_intermediate_actions,
        required_first_action=None,
        required_actions=(),
        required_action_windows=None,
    ):
        self.start_action = start_action
        self.target_action = target_action
        self.target_energy = target_energy
        self.global_used_intermediates = global_used_intermediates
        self.required_action_windows = required_action_windows or {}
        self.required_actions = tuple(required_actions)
        self.required_action_bits = {
            action: 1 << index
            for index, action in enumerate(self.required_actions)
        }
        self.complete_required_mask = (1 << len(self.required_actions)) - 1
        self.candidates = [
            action
            for action, data in positions.ACTIONS.items()
            if (
                data.get("dance_phrase")
                or action in executable_intermediate_actions
            )
            and (
                not data.get("cue_only")
                or action in self.required_action_bits
            )
        ]
        for action in self.required_actions:
            if action not in positions.ACTIONS:
                raise ValueError("Azione obbligatoria sconosciuta: %s" % action)
        if any(action not in self.candidates for action in self.required_actions):
            raise ValueError(
                "Le azioni obbligatorie devono essere mosse candidate per A*."
            )

        if required_first_action and not positions.is_transition_valid(
            start_action, required_first_action
        ):
            raise ValueError(
                "Transizione non valida verso l'azione richiesta: %s"
                % required_first_action
            )

        self.prefix = (
            (required_first_action,) if required_first_action else ()
        )
        initial_action = required_first_action or start_action
        initial_duration_ms = round(
            positions.get_duration(required_first_action) * 1000
        ) if required_first_action else 0
        action_bits = {
            action: 1 << index for index, action in enumerate(self.candidates)
        }
        used_mask = action_bits.get(required_first_action, 0)
        required_mask = self.required_action_bits.get(required_first_action, 0)

        self.target_ms = round(target_duration * 1000)
        self.target_post_ms = round(
            positions.get_duration(target_action) * 1000
        )
        self.action_bits = action_bits
        self.max_action_ms = max(
            round(positions.get_duration(action) * 1000)
            for action in self.candidates
        )
        self.upper_pre_goal_ms = (
            self.target_ms - self.target_post_ms + self.max_action_ms
        )
        self.upper_elapsed_ms = self.target_ms + self.max_action_ms

        initial_state = _State(
            last_action=initial_action,
            previous_action=start_action,
            elapsed_ms=initial_duration_ms,
            used_mask=used_mask,
            repeated_mask=0,
            required_mask=required_mask,
        )
        super().__init__(initial_state)

    def actions(self, state):
        if state.last_action == self.target_action:
            return []

        actions = []
        if (
            state.required_mask == self.complete_required_mask
            and positions.is_transition_valid(state.last_action, self.target_action)
            and state.elapsed_ms + self.target_post_ms <= self.upper_elapsed_ms
        ):
            actions.append(self.target_action)

        for action in self.candidates:
            if not positions.is_transition_valid(state.last_action, action):
                continue
            if action in (state.last_action, state.previous_action):
                continue

            next_elapsed_ms = state.elapsed_ms + round(
                positions.get_duration(action) * 1000
            )
            if next_elapsed_ms > self.upper_pre_goal_ms:
                continue

            required_bit = self.required_action_bits.get(action, 0)
            if required_bit and state.required_mask & required_bit:
                continue
            if required_bit:
                window = self.required_action_windows.get(action)
                if window:
                    start_seconds = state.elapsed_ms / 1000.0
                    if not window[0] <= start_seconds <= window[1]:
                        continue

            action_bit = self.action_bits[action]
            repeated = bool(state.used_mask & action_bit)
            already_repeated = bool(state.repeated_mask & action_bit)
            local_uses = 2 if already_repeated else int(repeated)
            if (
                self._prior_uses(action) + local_uses
                >= MAX_INTERMEDIATE_USES
            ):
                continue
            if repeated and already_repeated:
                continue
            actions.append(action)
        return actions

    def result(self, state, action):
        if action == self.target_action:
            elapsed_ms = state.elapsed_ms + self.target_post_ms
        else:
            elapsed_ms = state.elapsed_ms + round(
                positions.get_duration(action) * 1000
            )

        action_bit = self.action_bits.get(action, 0)
        repeated = bool(state.used_mask & action_bit)
        required_bit = self.required_action_bits.get(action, 0)
        return _State(
            last_action=action,
            previous_action=state.last_action,
            elapsed_ms=elapsed_ms,
            used_mask=state.used_mask | action_bit,
            repeated_mask=(
                state.repeated_mask | action_bit
                if repeated
                else state.repeated_mask
            ),
            required_mask=state.required_mask | required_bit,
        )

    def goal_test(self, state):
        return (
            state.last_action == self.target_action
            and state.required_mask == self.complete_required_mask
            and state.elapsed_ms <= self.upper_elapsed_ms
        )

    def path_cost(self, cost, state, action, next_state):
        if action == self.target_action:
            timing_error = abs(self.target_ms - next_state.elapsed_ms) / 1000.0
            return cost + timing_error * 8.0

        action_bit = self.action_bits[action]
        prior_uses = self._prior_uses(action)
        repeated = bool(state.used_mask & action_bit)
        edge_cost = abs(
            positions.get_energy(action) - self.target_energy
        ) * 0.35
        if repeated:
            edge_cost += DIVERSITY_REPEAT_PENALTY
        edge_cost += GLOBAL_REUSE_PENALTY * prior_uses
        return cost + edge_cost

    def heuristic(self, node):
        if node.state.last_action == self.target_action:
            return 0.0
        remaining_ms = (
            self.target_ms
            - self.target_post_ms
            - node.state.elapsed_ms
        )
        return abs(remaining_ms) / 1000.0 * 8.0

    def _prior_uses(self, action):
        if isinstance(self.global_used_intermediates, dict):
            return self.global_used_intermediates.get(action, 0)
        return int(action in self.global_used_intermediates)

    def solve(self):
        """Return the chosen segment, or raise if no valid path exists."""
        solution_node = astar_search(self, h=self.heuristic)
        if solution_node is None:
            raise ValueError(
                "Nessuna sequenza valida per il segmento verso %s."
                % self.target_action
            )

        solution = list(self.prefix) + solution_node.solution()
        newly_used = {}
        for action in solution[:-1]:
            if positions.ACTIONS[action]["type"] in ("intermediate", "crg"):
                newly_used[action] = newly_used.get(action, 0) + 1
        return solution, newly_used
