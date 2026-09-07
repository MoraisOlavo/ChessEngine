"""
Core game orchestration, independent of any user interface.

The Game class wraps a chess Position and manages the flow of a game:
listing legal moves, matching a requested move and applying it, and
detecting the game result. It is deliberately UI-agnostic so the same
class can back a terminal game today and a web server later.

Run the terminal version with: python3 -m game.terminal
"""

from position.base import Move, Position
from position.matrix import MatrixPosition

STATUS_IN_PROGRESS = "in_progress"
STATUS_CHECKMATE = "checkmate"
STATUS_STALEMATE = "stalemate"
STATUS_DRAW = "draw"


def same_move(a: Move, b: Move) -> bool:
    """Compares two moves by all of their defining attributes."""
    return (
        a.from_sq == b.from_sq
        and a.to_sq == b.to_sq
        and a.promotion_piece == b.promotion_piece
        and a.is_en_passant == b.is_en_passant
        and a.is_castling == b.is_castling
    )


class Game:
    """
    Manages the state of a chess game independently of any user interface.

    Attributes:
        position: The current chess Position (MatrixPosition by default).
    """

    def __init__(self, position: Position | None = None):
        self.position = (
            position if position is not None else MatrixPosition.initial_position()
        )
        self._legal = self.position.get_legal_positions_and_moves()

    def legal_moves(self) -> list[Move]:
        """Returns all legal moves in the current position."""
        return [move for _, move in self._legal]

    def find_moves(
        self, from_sq: tuple[int, int], to_sq: tuple[int, int]
    ) -> list[Move]:
        """
        Returns the legal moves matching an origin/destination request.

        Returns 0 moves if the request is illegal, 1 for a normal move and
        4 for an under-specified promotion (one per promotion piece).
        """
        return [
            move for _, move in self._legal
            if move.from_sq == from_sq and move.to_sq == to_sq
        ]

    def apply(self, move: Move) -> Position:
        """
        Applies a legal move, advancing the game to the resulting position.

        The successor position is taken directly from the move generator,
        which guarantees all special move effects (castling rook relocation,
        en passant pawn removal, promotion piece placement) are applied
        exactly as generated.

        Raises:
            ValueError: If the move is not legal in the current position.
        """
        for child, candidate in self._legal:
            if same_move(candidate, move):
                self.position = child
                self._legal = child.get_legal_positions_and_moves()
                return child
        raise ValueError(
            f"Move is not legal in the current position: "
            f"{move.from_sq} -> {move.to_sq}"
        )

    def status(self) -> str:
        """Returns the game status: in_progress, checkmate, stalemate or draw."""
        if self.position.is_checkmate():
            return STATUS_CHECKMATE
        if self.position.is_stalemate():
            return STATUS_STALEMATE
        if self.position.is_draw():
            return STATUS_DRAW
        return STATUS_IN_PROGRESS
