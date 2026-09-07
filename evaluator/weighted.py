from position.base import (
    BLACK,
    BISHOP,
    KING,
    KNIGHT,
    PAWN,
    Position,
    QUEEN,
    ROOK,
    WHITE,
)

from evaluator.base import Evaluator, MATE_SCORE


class MaterialEvaluator(Evaluator):
    """
    Evaluator based on classical material values.

    Pawn 1, knight and bishop 3, rook 5, queen 9. The king is worth zero
    since both sides always have exactly one. Terminal positions override
    the material score: checkmate is worth +/- MATE_SCORE (from White's
    perspective) and stalemate is worth 0.
    """

    PIECE_VALUES = {
        PAWN: 1,
        KNIGHT: 3,
        BISHOP: 3,
        ROOK: 5,
        QUEEN: 9,
        KING: 0,
    }

    def evaluate(self, position: Position) -> float:
        if position.is_checkmate():
            return float(-MATE_SCORE if position.get_color() == WHITE else MATE_SCORE)
        if position.is_stalemate():
            return 0.0
        score = 0
        for piece, count in position.get_piece_counts().items():
            sign = 1 if piece > 0 else -1
            score += self.PIECE_VALUES[abs(piece)] * sign * count
        return float(score)
