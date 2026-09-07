from abc import ABC, abstractmethod

# Piece Encodings
# Positive integers for White pieces, negative for Black pieces, 0 for empty squares.
EMPTY = 0
PAWN = 1
KNIGHT = 2
BISHOP = 3
ROOK = 4
QUEEN = 5
KING = 6

# Color constants
WHITE = 'w'
BLACK = 'b'


class Move:
    """
    Represents a chess move: origin square, destination square and special flags.

    Attributes:
        from_sq: Origin square as (row, col).
        to_sq: Destination square as (row, col).
        promotion_piece: Piece type promoted to (positive constant), or None.
        is_en_passant: True if this move is an en passant capture.
        is_castling: (rook_from, rook_to) squares if this move is castling, else None.
    """

    def __init__(
        self,
        from_sq: tuple[int, int],
        to_sq: tuple[int, int],
        promotion_piece: int | None = None,
        is_en_passant: bool = False,
        is_castling: tuple[tuple[int, int], tuple[int, int]] | None = None
    ):
        self.from_sq = from_sq
        self.to_sq = to_sq
        self.promotion_piece = promotion_piece
        self.is_en_passant = is_en_passant
        self.is_castling = is_castling


class Position(ABC):
    """
    Abstract interface representing a complete chess board position.

    A position encompasses the full game state: piece placement, active turn,
    castling availability, en passant target square, move counts, and position
    history for repetition detection.
    """

    @abstractmethod
    def is_valid(self) -> bool:
        """
        Determines whether the current position is legally and structurally valid.

        Returns:
            bool: True if the position meets all chess validity rules, False otherwise.
        """
        pass

    @abstractmethod
    def is_in_check(self) -> bool:
        """
        Determines whether the active player's King is currently under attack.

        Returns:
            bool: True if the side to move is in check, False otherwise.
        """
        pass

    @abstractmethod
    def get_color(self) -> str:
        """
        Returns the color of the side to move.

        Returns:
            str: WHITE ('w') or BLACK ('b').
        """
        pass

    @abstractmethod
    def make_move(
        self,
        from_sq: tuple[int, int],
        to_sq: tuple[int, int],
        promotion_piece: int | None = None,
        is_en_passant: bool = False,
        en_passant_target: tuple[int, int] | None = None,
        is_castling: tuple[tuple[int, int], tuple[int, int]] | None = None
    ) -> tuple["Position", "Move"]:
        """
        Applies a move and returns the resulting position paired with the Move made.

        Returns:
            tuple[Position, Move]: The successor position and the move that led to it.
        """
        pass

    @abstractmethod
    def get_legal_positions_and_moves(self) -> list[tuple["Position", "Move"]]:
        """
        Generates all legal (position, move) pairs reachable from this position.

        Returns:
            list[tuple[Position, Move]]: Legal successor positions paired with
            the move that generated each of them.
        """
        pass

    @abstractmethod
    def is_checkmate(self) -> bool:
        """Returns True if the active player is in checkmate (in check, no legal moves)."""
        pass

    @abstractmethod
    def is_stalemate(self) -> bool:
        """Returns True if the active player is not in check and has no legal moves."""
        pass

    @abstractmethod
    def get_piece_counts(self) -> dict[int, int]:
        """
        Returns the number of pieces on the board keyed by signed piece constant.

        Keys are the implementation's piece encodings (positive for white
        pieces, negative for black pieces), values are the piece counts.
        Empty squares are not included.
        """
        pass
