from evaluator.base import Evaluator
from engine.base import Engine
from position.base import Move, Position, WHITE


class MiniMaxEngine(Engine):
    """
    Chess engine that uses the plain minimax algorithm.

    Explores the game tree recursively up to max_depth plies, deriving the
    maximizing/minimizing role of each level from the side to move.
    """

    def __init__(self, evaluator: Evaluator, max_depth: int):
        super().__init__(evaluator)
        if max_depth < 1:
            raise ValueError('max_depth must be at least 1')
        self.max_depth = max_depth

    def find_best_move(self, position: Position) -> tuple[Move, float]:
        """
        Finds the best move for the side to move in the given position.

        Args:
            position: The chess position to search.

        Returns:
            tuple[Move, float]: The best move and its score (from White's
            perspective). Ties are broken by the first best move found.

        Raises:
            ValueError: If the position has no legal moves (the game is over).
        """
        candidates = position.get_legal_positions_and_moves()
        if not candidates:
            raise ValueError('No legal moves found')

        is_white = position.get_color() == WHITE
        winning_score = float('-inf') if is_white else float('inf')
        best_move = None

        for candidate_position, candidate_move in candidates:
            score = self.minimax(candidate_position, self.max_depth - 1)
            if is_white:
                if score > winning_score:
                    winning_score = score
                    best_move = candidate_move
            else:
                if score < winning_score:
                    winning_score = score
                    best_move = candidate_move

        return best_move, winning_score

    def minimax(self, position: Position, depth: int) -> float:
        """
        Scores a position by minimaxing over legal moves up to the given depth.

        Terminal nodes (no legal moves) and leaves (depth 0) are resolved by
        the evaluator, which already handles checkmate, stalemate and material.
        """
        if depth == 0:
            return self.evaluator.evaluate(position)

        candidates = position.get_legal_positions_and_moves()
        if not candidates:
            return self.evaluator.evaluate(position)

        if position.get_color() == WHITE:
            winning_score = float('-inf')
            for child, _ in candidates:
                score = self.minimax(child, depth - 1)
                winning_score = max(winning_score, score)
            return winning_score
        else:
            winning_score = float('inf')
            for child, _ in candidates:
                score = self.minimax(child, depth - 1)
                winning_score = min(winning_score, score)
            return winning_score
