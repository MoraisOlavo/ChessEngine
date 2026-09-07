from abc import ABC, abstractmethod

from evaluator.base import Evaluator
from position.base import Move, Position


class Engine(ABC):
    """
    Interface for chess engines.

    An engine chooses the best move for the side to move in a given position,
    using an evaluator to score positions.
    """

    def __init__(self, evaluator: Evaluator):
        self.evaluator = evaluator

    @abstractmethod
    def find_best_move(self, position: Position) -> tuple[Move, float]:
        """
        Finds the best move for the side to move in the given position.

        Args:
            position: The chess position to search.

        Returns:
            tuple[Move, float]: The best move and its score, following the
            evaluator convention (positive favors White, negative favors Black).

        Raises:
            ValueError: If the position has no legal moves (the game is over).
        """
        pass
