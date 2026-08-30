"""Explicit agent lifecycle states (AGENTS.md §4.4, §11)."""
from __future__ import annotations

import enum


class AgentState(enum.StrEnum):
    RECEIVED = "received"
    CLASSIFYING = "classifying"
    PLANNING = "planning"
    EXECUTING = "executing"
    OBSERVING = "observing"
    VERIFYING = "verifying"
    COMPLETED = "completed"
    FAILED = "failed"


# Allowed transitions guard against uncontrolled loops and invalid jumps.
_ALLOWED: dict[AgentState, set[AgentState]] = {
    AgentState.RECEIVED: {AgentState.CLASSIFYING, AgentState.FAILED},
    AgentState.CLASSIFYING: {AgentState.PLANNING, AgentState.FAILED},
    AgentState.PLANNING: {AgentState.EXECUTING, AgentState.FAILED},
    AgentState.EXECUTING: {
        AgentState.OBSERVING,
        AgentState.VERIFYING,
        AgentState.FAILED,
    },
    AgentState.OBSERVING: {
        AgentState.EXECUTING,
        AgentState.VERIFYING,
        AgentState.FAILED,
        AgentState.PLANNING,
    },
    AgentState.VERIFYING: {AgentState.COMPLETED, AgentState.OBSERVING, AgentState.FAILED},
    AgentState.COMPLETED: set(),
    AgentState.FAILED: set(),
}


class IllegalTransitionError(Exception):
    pass


class StateMachine:
    """Tracks agent state with validated transitions."""

    def __init__(self, initial: AgentState = AgentState.RECEIVED) -> None:
        self._state = initial

    @property
    def state(self) -> AgentState:
        return self._state

    def can_transition(self, target: AgentState) -> bool:
        return target in _ALLOWED[self._state]

    def transition(self, target: AgentState) -> AgentState:
        if self._state == target:
            return self._state
        if not self.can_transition(target):
            raise IllegalTransitionError(
                f"Illegal transition: {self._state} -> {target}"
            )
        self._state = target
        return self._state

    def is_terminal(self) -> bool:
        return self._state in (AgentState.COMPLETED, AgentState.FAILED)
