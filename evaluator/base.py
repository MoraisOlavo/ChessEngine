from abc import ABC, abstractmethod

from position.base import Position

# Large constant for checkmate instead of float('inf'), so a future search can
# rank faster mates with MATE_SCORE - depth.
MATE_SCORE = 1_000_000


class Evaluator(ABC):
    """
    Abstract interface for evaluating chess positions.

    All evaluations are made from White's perspective: positive scores favor
    White, negative scores favor Black, regardless of whose turn it is.
    """

    @abstractmethod
    def evaluate(self, position: Position) -> float:
        """
        Evaluates the given position from White's perspective.

        Args:
            position: The chess position to evaluate.

        Returns:
            float: Evaluation score (positive favors White, negative favors Black).
        """
        pass
