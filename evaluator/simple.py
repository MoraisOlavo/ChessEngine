from position.base import BLACK, Position, WHITE

from evaluator.base import Evaluator, MATE_SCORE


class PieceCountEvaluator(Evaluator):
    """
    Evaluator that assigns one point per piece on the board.

    White pieces add one point each and black pieces subtract one point each.
    Terminal positions override the material score: checkmate is worth
    +/- MATE_SCORE (from White's perspective) and stalemate is worth 0.
    """

    def evaluate(self, position: Position) -> float:
        if position.is_checkmate():
            return float(-MATE_SCORE if position.get_color() == WHITE else MATE_SCORE)
        if position.is_stalemate():
            return 0.0
        score = 0
        for piece, count in position.get_piece_counts().items():
            score += count if piece > 0 else -count
        return float(score)
