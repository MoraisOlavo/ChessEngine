import unicodedata

from position.base import (
    BLACK,
    BISHOP,
    EMPTY,
    KING,
    KNIGHT,
    Move,
    PAWN,
    Position,
    QUEEN,
    ROOK,
    WHITE,
)


class MatrixPosition(Position):
    """
    8x8 matrix-based implementation of a chess Position.

    Matrix indexing convention:
    - Row 0 represents Rank 1 (bottom of the board, White starting back-rank).
    - Row 1 represents Rank 2 (White starting pawn rank).
    - Row 6 represents Rank 7 (Black starting pawn rank).
    - Row 7 represents Rank 8 (top of the board, Black starting back-rank).
    - Column 0 to 7 represents Files 'a' to 'h'.
    """

    def __init__(
        self,
        board: list[list[int]] | None = None,
        active_color: str = WHITE,
        castling_rights: str = "KQkq",
        en_passant_square: tuple[int, int] | None = None,
        halfmove_clock: int = 0,
        fullmove_number: int = 1,
        history: list[str] | None = None
    ):
        if board is None:
            self.board = [[EMPTY] * 8 for _ in range(8)]
        else:
            self.board = board

        self.active_color = active_color
        self.castling_rights = castling_rights
        self.en_passant_square = en_passant_square
        self.halfmove_clock = halfmove_clock
        self.fullmove_number = fullmove_number
        self.history = history if history is not None else []

    @classmethod
    def initial_position(cls) -> "MatrixPosition":
        """
        Constructs and returns the standard starting chess position.
        Row 0 is White back-rank (Rank 1), Row 7 is Black back-rank (Rank 8).
        """
        starting_board = [
            [ROOK, KNIGHT, BISHOP, QUEEN, KING, BISHOP, KNIGHT, ROOK],
            [PAWN] * 8,
            [EMPTY] * 8,
            [EMPTY] * 8,
            [EMPTY] * 8,
            [EMPTY] * 8,
            [-PAWN] * 8,
            [-ROOK, -KNIGHT, -BISHOP, -QUEEN, -KING, -BISHOP, -KNIGHT, -ROOK]
        ]
        return cls(
            board=starting_board,
            active_color=WHITE,
            castling_rights="KQkq",
            en_passant_square=None,
            halfmove_clock=0,
            fullmove_number=1,
            history=[]
        )

    # =========================================================================
    # String Formatting
    # =========================================================================

    @staticmethod
    def to_algebraic_square(r: int, c: int) -> str:
        """Converts (r, c) matrix coordinates to algebraic notation like 'e4'."""
        file_char = chr(ord('a') + c)
        rank_num = r + 1
        return f"{file_char}{rank_num}"

    @staticmethod
    def _display_width(char: str) -> int:
        """Returns the terminal display width of a character (1 or 2 columns)."""
        eaw = unicodedata.east_asian_width(char)
        return 2 if eaw in ("W", "F") else 1

    @classmethod
    def _padded_cell(cls, symbol: str) -> str:
        """
        Returns the symbol centered in a 3-column-wide cell interior.

        Keeps the total interior width (padding + symbol) at 3 display columns so
        it matches the '───' border segment, preserving grid alignment while
        centering the piece within its square.
        """
        width = cls._display_width(symbol)
        remaining = 3 - width
        left = remaining // 2
        right = remaining - left
        return " " * left + symbol + " " * right

    def __str__(self) -> str:
        """
        Renders a Unicode box-grid representation of the position.
        Uses U+3000 (Ideographic Full-Width Space) for empty squares to match the
        display width of wide Unicode chess piece symbols in terminal fonts.
        """
        UL, UR, LL, LR = "\u250c", "\u2510", "\u2514", "\u2518"
        HBAR, VBAR = "\u2500", "\u2502"
        NT, ST, WT, ET, PLUS = "\u252c", "\u2534", "\u251c", "\u2524", "\u253c"
        H3 = HBAR * 3

        topline = f"   {UL}" + (H3 + NT) * 7 + H3 + UR
        midline = f"   {WT}" + (H3 + PLUS) * 7 + H3 + ET
        botline = f"   {LL}" + (H3 + ST) * 7 + H3 + LR

        piece_symbols = {
            EMPTY: " ",
            PAWN: "\u2659", KNIGHT: "\u2658", BISHOP: "\u2657",
            ROOK: "\u2656", QUEEN: "\u2655", KING: "\u2654",
            -PAWN: "\u265f", -KNIGHT: "\u265e", -BISHOP: "\u265d",
            -ROOK: "\u265c", -QUEEN: "\u265b", -KING: "\u265a"
        }

        lines = ["     a   b   c   d   e   f   g   h", topline]

        for r in range(7, -1, -1):
            rank_num = r + 1
            row_cells = "".join(
                f"{self._padded_cell(piece_symbols[self.board[r][c]])}{VBAR}"
                for c in range(8)
            )
            lines.append(f" {rank_num} {VBAR}{row_cells} {rank_num}")
            if r > 0:
                lines.append(midline)

        lines.append(botline)
        lines.append("     a   b   c   d   e   f   g   h")
        lines.append("")

        active_name = "White ('w')" if self.active_color == WHITE else "Black ('b')"
        ep_name = (
            self.to_algebraic_square(*self.en_passant_square)
            if self.en_passant_square else "None"
        )

        metadata = (
            f"Turn: {active_name} | Castling: {self.castling_rights} | "
            f"En Passant: {ep_name} | Halfmove: {self.halfmove_clock} | "
            f"Fullmove: {self.fullmove_number}"
        )
        lines.append(metadata)
        return "\n".join(lines)

    # =========================================================================
    # Board Utility Helpers
    # =========================================================================

    @staticmethod
    def _in_bounds(r: int, c: int) -> bool:
        """Checks if coordinates (r, c) fall within the 8x8 board bounds."""
        return 0 <= r < 8 and 0 <= c < 8

    def _is_friendly(self, r: int, c: int, color: str) -> bool:
        """Checks if square (r, c) is in bounds and contains a piece belonging to color."""
        if not self._in_bounds(r, c):
            return False
        piece = self.board[r][c]
        if piece == EMPTY:
            return False
        return piece > 0 if color == WHITE else piece < 0

    def _position_key(self) -> str:
        """
        Returns a string key uniquely identifying this position for repetition detection.

        Includes board state, active color, castling rights, and the en passant square
        (only when an en passant capture is actually possible, per FIDE rules).
        """
        board_str = "/".join(
            ",".join(str(self.board[r][c]) for c in range(8)) for r in range(8)
        )

        effective_ep = None
        if self.en_passant_square is not None:
            ep_r, ep_c = self.en_passant_square
            pawn_val = PAWN if self.active_color == WHITE else -PAWN
            capture_from_row = ep_r - 1 if self.active_color == WHITE else ep_r + 1
            for dc in (-1, 1):
                cc = ep_c + dc
                if (self._in_bounds(capture_from_row, cc)
                        and self.board[capture_from_row][cc] == pawn_val):
                    effective_ep = self.en_passant_square
                    break

        ep_str = (
            f"{effective_ep[0]},{effective_ep[1]}" if effective_ep else "-"
        )

        return f"{board_str} {self.active_color} {self.castling_rights} {ep_str}"

    # =========================================================================
    # Movement Pattern Helpers
    # =========================================================================

    @classmethod
    def _get_knight_targets(cls, r: int, c: int) -> list[tuple[int, int]]:
        """Returns all in-bounds L-step target squares for a Knight at (r, c)."""
        offsets = [
            (-2, -1), (-2, 1), (-1, -2), (-1, 2),
            (1, -2), (1, 2), (2, -1), (2, 1)
        ]
        return [
            (r + dr, c + dc) for dr, dc in offsets
            if cls._in_bounds(r + dr, c + dc)
        ]

    @classmethod
    def _get_king_targets(cls, r: int, c: int) -> list[tuple[int, int]]:
        """Returns all in-bounds 8-adjacent target squares for a King at (r, c)."""
        offsets = [
            (-1, -1), (-1, 0), (-1, 1),
            (0, -1),           (0, 1),
            (1, -1),  (1, 0),  (1, 1)
        ]
        return [
            (r + dr, c + dc) for dr, dc in offsets
            if cls._in_bounds(r + dr, c + dc)
        ]

    @classmethod
    def _get_pawn_attack_squares(
        cls, r: int, c: int, pawn_color: str
    ) -> list[tuple[int, int]]:
        """Returns the in-bounds diagonal attack squares for a pawn of pawn_color at (r, c)."""
        pawn_row = r + 1 if pawn_color == WHITE else r - 1
        return [
            (pawn_row, c + dc) for dc in (-1, 1)
            if cls._in_bounds(pawn_row, c + dc)
        ]

    def _get_ray_targets(
        self, r: int, c: int, directions: list[tuple[int, int]]
    ) -> list[tuple[int, int]]:
        """
        Performs ray-casting along directional vectors (dr, dc) from (r, c).
        Returns all empty squares along the ray plus the first occupied blocking square.
        """
        targets = []
        for dr, dc in directions:
            tr, tc = r + dr, c + dc
            while self._in_bounds(tr, tc):
                targets.append((tr, tc))
                if self.board[tr][tc] != EMPTY:
                    break
                tr += dr
                tc += dc
        return targets

    # =========================================================================
    # Check Detection
    # =========================================================================

    def find_king(self, color: str) -> tuple[int, int] | None:
        """Finds the coordinates (row, col) of the King of the specified color."""
        target_king = KING if color == WHITE else -KING
        for r in range(8):
            for c in range(8):
                if self.board[r][c] == target_king:
                    return (r, c)
        return None

    def is_square_attacked(self, row: int, col: int, attacker_color: str) -> bool:
        """
        Determines if square (row, col) is under attack by any piece of attacker_color.
        """
        attacker_sign = 1 if attacker_color == WHITE else -1

        for r, c in self._get_knight_targets(row, col):
            if self.board[r][c] == attacker_sign * KNIGHT:
                return True

        defender_color = BLACK if attacker_color == WHITE else WHITE
        for r, c in self._get_pawn_attack_squares(row, col, defender_color):
            if self.board[r][c] == attacker_sign * PAWN:
                return True

        for r, c in self._get_king_targets(row, col):
            if self.board[r][c] == attacker_sign * KING:
                return True

        straight_dirs = [(-1, 0), (1, 0), (0, -1), (0, 1)]
        for r, c in self._get_ray_targets(row, col, straight_dirs):
            piece = self.board[r][c]
            if piece == attacker_sign * ROOK or piece == attacker_sign * QUEEN:
                return True

        diagonal_dirs = [(-1, -1), (-1, 1), (1, -1), (1, 1)]
        for r, c in self._get_ray_targets(row, col, diagonal_dirs):
            piece = self.board[r][c]
            if piece == attacker_sign * BISHOP or piece == attacker_sign * QUEEN:
                return True

        return False

    def _is_king_attacked(self, color: str) -> bool:
        """Checks whether the king of the given color is under attack."""
        king_pos = self.find_king(color)
        if king_pos is None:
            return True
        opponent = BLACK if color == WHITE else WHITE
        return self.is_square_attacked(king_pos[0], king_pos[1], opponent)

    def is_in_check(self) -> bool:
        """Determines whether the active player's King is currently in check."""
        return self._is_king_attacked(self.active_color)

    def get_color(self) -> str:
        """Returns the color of the side to move (WHITE or BLACK)."""
        return self.active_color

    # =========================================================================
    # Position Validation
    # =========================================================================

    def is_valid(self) -> bool:
        """
        Determines whether the position is structurally and legally valid.
        """
        if len(self.board) != 8 or any(len(row) != 8 for row in self.board):
            return False

        if self.active_color not in (WHITE, BLACK):
            return False

        white_king_count = 0
        black_king_count = 0

        for r in range(8):
            for c in range(8):
                val = self.board[r][c]
                if not isinstance(val, int) or not (-6 <= val <= 6):
                    return False
                if val == KING:
                    white_king_count += 1
                elif val == -KING:
                    black_king_count += 1

                if (r == 0 or r == 7) and abs(val) == PAWN:
                    return False

        if white_king_count != 1 or black_king_count != 1:
            return False

        if self.en_passant_square is not None:
            ep_row, ep_col = self.en_passant_square
            if not self._in_bounds(ep_row, ep_col):
                return False
            expected_ep_row = 5 if self.active_color == WHITE else 2
            if ep_row != expected_ep_row:
                return False

        opponent_color = BLACK if self.active_color == WHITE else WHITE
        if self._is_king_attacked(opponent_color):
            return False

        return True

    # =========================================================================
    # Piece Queries
    # =========================================================================

    def get_piece_counts(self) -> dict[int, int]:
        """
        Returns the number of pieces on the board keyed by signed piece constant.

        Positive keys count white pieces, negative keys count black pieces.
        Empty squares are not included.
        """
        counts: dict[int, int] = {}
        for row in self.board:
            for piece in row:
                if piece != EMPTY:
                    counts[piece] = counts.get(piece, 0) + 1
        return counts

    # =========================================================================
    # Make Move
    # =========================================================================

    def make_move(
        self,
        from_sq: tuple[int, int],
        to_sq: tuple[int, int],
        promotion_piece: int | None = None,
        is_en_passant: bool = False,
        en_passant_target: tuple[int, int] | None = None,
        is_castling: tuple[tuple[int, int], tuple[int, int]] | None = None
    ) -> tuple["MatrixPosition", Move]:
        """
        Creates the MatrixPosition resulting from applying a move, paired with
        the Move that generated it.
        """
        r1, c1 = from_sq
        r2, c2 = to_sq
        moving_piece = self.board[r1][c1]
        sign = 1 if self.active_color == WHITE else -1

        new_board = [row[:] for row in self.board]

        new_board[r1][c1] = EMPTY
        if promotion_piece is not None:
            new_board[r2][c2] = sign * promotion_piece
        else:
            new_board[r2][c2] = moving_piece

        if is_en_passant:
            new_board[r1][c2] = EMPTY

        if is_castling is not None:
            rook_from, rook_to = is_castling
            rf, cf = rook_from
            rt, ct = rook_to
            rook_piece = new_board[rf][cf]
            new_board[rf][cf] = EMPTY
            new_board[rt][ct] = rook_piece

        new_castling = self.castling_rights
        if moving_piece == KING:
            new_castling = new_castling.replace("K", "").replace("Q", "")
        elif moving_piece == -KING:
            new_castling = new_castling.replace("k", "").replace("q", "")

        if (r1, c1) == (0, 0) or (r2, c2) == (0, 0):
            new_castling = new_castling.replace("Q", "")
        if (r1, c1) == (0, 7) or (r2, c2) == (0, 7):
            new_castling = new_castling.replace("K", "")
        if (r1, c1) == (7, 0) or (r2, c2) == (7, 0):
            new_castling = new_castling.replace("q", "")
        if (r1, c1) == (7, 7) or (r2, c2) == (7, 7):
            new_castling = new_castling.replace("k", "")

        if not new_castling:
            new_castling = "-"

        next_active_color = BLACK if self.active_color == WHITE else WHITE
        is_capture = (self.board[r2][c2] != EMPTY) or is_en_passant
        is_pawn_move = abs(moving_piece) == PAWN

        next_halfmove = (
            0 if (is_pawn_move or is_capture) else self.halfmove_clock + 1
        )
        next_fullmove = (
            self.fullmove_number + 1 if self.active_color == BLACK
            else self.fullmove_number
        )

        new_history = self.history + [self._position_key()]

        move = Move(
            from_sq=from_sq,
            to_sq=to_sq,
            promotion_piece=promotion_piece,
            is_en_passant=is_en_passant,
            is_castling=is_castling
        )

        return (
            MatrixPosition(
                board=new_board,
                active_color=next_active_color,
                castling_rights=new_castling,
                en_passant_square=en_passant_target,
                halfmove_clock=next_halfmove,
                fullmove_number=next_fullmove,
                history=new_history
            ),
            move
        )

    # =========================================================================
    # Pseudo-Legal Move Generation
    # =========================================================================

    def _generate_pawn_positions_and_moves(
        self, r: int, c: int
    ) -> list[tuple["MatrixPosition", Move]]:
        """Generates all pseudo-legal (position, move) pairs for a pawn at (r, c)."""
        positions_and_moves: list[tuple["MatrixPosition", Move]] = []
        direction = 1 if self.active_color == WHITE else -1
        start_row = 1 if self.active_color == WHITE else 6
        promotion_row = 7 if self.active_color == WHITE else 0

        next_r = r + direction
        if self._in_bounds(next_r, c) and self.board[next_r][c] == EMPTY:
            if next_r == promotion_row:
                for piece in (QUEEN, ROOK, BISHOP, KNIGHT):
                    positions_and_moves.append(self.make_move(
                        (r, c), (next_r, c), promotion_piece=piece
                    ))
            else:
                positions_and_moves.append(self.make_move((r, c), (next_r, c)))

            double_r = r + 2 * direction
            if r == start_row and self.board[double_r][c] == EMPTY:
                ep_target = (r + direction, c)
                positions_and_moves.append(self.make_move(
                    (r, c), (double_r, c), en_passant_target=ep_target
                ))

        for pawn_r, cap_c in self._get_pawn_attack_squares(r, c, self.active_color):
            target_piece = self.board[pawn_r][cap_c]
            is_opponent = (
                target_piece < 0 if self.active_color == WHITE
                else target_piece > 0
            )
            is_ep = (self.en_passant_square == (pawn_r, cap_c))

            if is_opponent or is_ep:
                if pawn_r == promotion_row:
                    for piece in (QUEEN, ROOK, BISHOP, KNIGHT):
                        positions_and_moves.append(self.make_move(
                            (r, c), (pawn_r, cap_c),
                            promotion_piece=piece, is_en_passant=is_ep
                        ))
                else:
                    positions_and_moves.append(self.make_move(
                        (r, c), (pawn_r, cap_c), is_en_passant=is_ep
                    ))

        return positions_and_moves

    def _generate_piece_positions_and_moves(
        self, r: int, c: int
    ) -> list[tuple["MatrixPosition", Move]]:
        """Generates all pseudo-legal (position, move) pairs for a non-pawn piece at (r, c)."""
        positions_and_moves: list[tuple["MatrixPosition", Move]] = []
        piece_type = abs(self.board[r][c])

        if piece_type == KNIGHT:
            for tr, tc in self._get_knight_targets(r, c):
                if not self._is_friendly(tr, tc, self.active_color):
                    positions_and_moves.append(self.make_move((r, c), (tr, tc)))

        elif piece_type in (BISHOP, ROOK, QUEEN):
            directions = []
            if piece_type in (BISHOP, QUEEN):
                directions.extend([(-1, -1), (-1, 1), (1, -1), (1, 1)])
            if piece_type in (ROOK, QUEEN):
                directions.extend([(-1, 0), (1, 0), (0, -1), (0, 1)])

            for tr, tc in self._get_ray_targets(r, c, directions):
                if not self._is_friendly(tr, tc, self.active_color):
                    positions_and_moves.append(self.make_move((r, c), (tr, tc)))

        elif piece_type == KING:
            for tr, tc in self._get_king_targets(r, c):
                if not self._is_friendly(tr, tc, self.active_color):
                    positions_and_moves.append(self.make_move((r, c), (tr, tc)))

            opponent_color = BLACK if self.active_color == WHITE else WHITE
            if self.active_color == WHITE:
                if ("K" in self.castling_rights
                        and self.board[0][5] == EMPTY
                        and self.board[0][6] == EMPTY):
                    if not any(
                        self.is_square_attacked(0, col, opponent_color)
                        for col in (4, 5, 6)
                    ):
                        positions_and_moves.append(self.make_move(
                            (0, 4), (0, 6), is_castling=((0, 7), (0, 5))
                        ))
                if ("Q" in self.castling_rights
                        and self.board[0][1] == EMPTY
                        and self.board[0][2] == EMPTY
                        and self.board[0][3] == EMPTY):
                    if not any(
                        self.is_square_attacked(0, col, opponent_color)
                        for col in (4, 3, 2)
                    ):
                        positions_and_moves.append(self.make_move(
                            (0, 4), (0, 2), is_castling=((0, 0), (0, 3))
                        ))
            else:
                if ("k" in self.castling_rights
                        and self.board[7][5] == EMPTY
                        and self.board[7][6] == EMPTY):
                    if not any(
                        self.is_square_attacked(7, col, opponent_color)
                        for col in (4, 5, 6)
                    ):
                        positions_and_moves.append(self.make_move(
                            (7, 4), (7, 6), is_castling=((7, 7), (7, 5))
                        ))
                if ("q" in self.castling_rights
                        and self.board[7][1] == EMPTY
                        and self.board[7][2] == EMPTY
                        and self.board[7][3] == EMPTY):
                    if not any(
                        self.is_square_attacked(7, col, opponent_color)
                        for col in (4, 3, 2)
                    ):
                        positions_and_moves.append(self.make_move(
                            (7, 4), (7, 2), is_castling=((7, 0), (7, 3))
                        ))

        return positions_and_moves

    def _generate_pseudo_legal_positions_and_moves(
        self
    ) -> list[tuple["MatrixPosition", Move]]:
        """Generates all pseudo-legal (position, move) pairs for the active player."""
        positions_and_moves: list[tuple["MatrixPosition", Move]] = []

        for r in range(8):
            for c in range(8):
                piece = self.board[r][c]
                if piece == EMPTY:
                    continue
                if not self._is_friendly(r, c, self.active_color):
                    continue

                if abs(piece) == PAWN:
                    positions_and_moves.extend(
                        self._generate_pawn_positions_and_moves(r, c)
                    )
                else:
                    positions_and_moves.extend(
                        self._generate_piece_positions_and_moves(r, c)
                    )

        return positions_and_moves

    # =========================================================================
    # Legal Move Generation
    # =========================================================================

    def get_legal_positions_and_moves(self) -> list[tuple[Position, Move]]:
        """Generates all legal (position, move) pairs reachable from the current position."""
        pseudo_legal = self._generate_pseudo_legal_positions_and_moves()
        return [
            (pos, move) for pos, move in pseudo_legal
            if not pos._is_king_attacked(self.active_color)
        ]

    # =========================================================================
    # Game Termination Detection
    # =========================================================================

    def is_checkmate(self) -> bool:
        """Returns True if the active player is in checkmate."""
        return self.is_in_check() and len(self.get_legal_positions_and_moves()) == 0

    def is_stalemate(self) -> bool:
        """Returns True if the active player is in stalemate."""
        return (
            not self.is_in_check()
            and len(self.get_legal_positions_and_moves()) == 0
        )

    def is_dead_position(self) -> bool:
        """Returns True if the position is a dead position (insufficient material)."""
        white_non_king = []
        black_non_king = []

        for r in range(8):
            for c in range(8):
                piece = self.board[r][c]
                if piece == EMPTY or abs(piece) == KING:
                    continue
                if piece > 0:
                    white_non_king.append((piece, r, c))
                else:
                    black_non_king.append((-piece, r, c))

        total = len(white_non_king) + len(black_non_king)

        if total == 0:
            return True

        if total == 1:
            piece_type = (
                white_non_king[0][0] if white_non_king else black_non_king[0][0]
            )
            if piece_type in (KNIGHT, BISHOP):
                return True

        all_non_king = white_non_king + black_non_king
        if all(p == BISHOP for p, _, _ in all_non_king):
            square_colors = set((r + c) % 2 for _, r, c in all_non_king)
            if len(square_colors) == 1:
                return True

        return False

    def is_fifty_move_draw(self) -> bool:
        """Returns True if a draw can be claimed under the fifty-move rule."""
        return self.halfmove_clock >= 100

    def is_seventy_five_move_draw(self) -> bool:
        """Returns True if the game is automatically drawn under the 75-move rule."""
        return self.halfmove_clock >= 150 and not self.is_checkmate()

    def is_threefold_repetition(self) -> bool:
        """Returns True if the current position has occurred at least 3 times."""
        current_key = self._position_key()
        return self.history.count(current_key) >= 2

    def is_fivefold_repetition(self) -> bool:
        """Returns True if the current position has occurred at least 5 times."""
        current_key = self._position_key()
        return self.history.count(current_key) >= 4

    def is_draw(self) -> bool:
        """Returns True if the position is drawn by any automatic rule."""
        return (
            self.is_stalemate()
            or self.is_dead_position()
            or self.is_fivefold_repetition()
            or self.is_seventy_five_move_draw()
        )


if __name__ == "__main__":
    import sys
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    pos = MatrixPosition.initial_position()
    print("=== Initial Position ===")
    print(pos)

    legal = pos.get_legal_positions_and_moves()
    print(f"\n=== Legal Moves for White ({len(legal)}) ===\n")
    for i, (child, move) in enumerate(legal, 1):
        origin = pos.to_algebraic_square(*move.from_sq)
        destination = pos.to_algebraic_square(*move.to_sq)
        print(f"--- Move {i}: {origin} -> {destination} ---")
        print(child)
