"""
Tests for special move support: castling, en passant and promotion.

Guarantees that all special moves are correctly generated and evaluated.
The classic perft from the initial position never exercises castling
(impossible within 4 plies) or promotions, so standard reference positions
from the Chess Programming Wiki are used instead:

    Kiwipete    ("Position 2"): 48 / 2039 / 97862
    Position 3:                  14 / 191 / 2812 / 43238
    Position 4:                  6 / 264 / 9467 / 422333
    Position 5:                  44 / 1486 / 62379

Run with: python3 -m tests.test_special_moves
"""

from position.base import (
    BLACK,
    BISHOP,
    EMPTY,
    KING,
    KNIGHT,
    PAWN,
    QUEEN,
    ROOK,
    WHITE,
)
from position.matrix import MatrixPosition
from evaluator.weighted import MaterialEvaluator
from engine.minimax import MiniMaxEngine


def make_board(pieces: dict[tuple[int, int], int]) -> list[list[int]]:
    board = [[EMPTY] * 8 for _ in range(8)]
    for (row, col), piece in pieces.items():
        board[row][col] = piece
    return board


def make_position(
    board: list[list[int]],
    active_color: str = WHITE,
    castling_rights: str = "KQkq",
    en_passant_square: tuple[int, int] | None = None
) -> MatrixPosition:
    return MatrixPosition(
        board=board,
        active_color=active_color,
        castling_rights=castling_rights,
        en_passant_square=en_passant_square,
        halfmove_clock=0,
        fullmove_number=1,
        history=[]
    )


def perft(position: MatrixPosition, depth: int) -> int:
    if depth == 0:
        return 1
    total = 0
    for child, _ in position.get_legal_positions_and_moves():
        total += perft(child, depth - 1)
    return total


def find_moves(
    position: MatrixPosition,
    from_sq: tuple[int, int],
    to_sq: tuple[int, int]
) -> list:
    return [
        move for _, move in position.get_legal_positions_and_moves()
        if move.from_sq == from_sq and move.to_sq == to_sq
    ]


def get_child(position: MatrixPosition, from_sq: tuple[int, int], to_sq: tuple[int, int]):
    for child, move in position.get_legal_positions_and_moves():
        if move.from_sq == from_sq and move.to_sq == to_sq:
            return child
    return None


# Reference positions (FEN rows reversed: row 0 = rank 1, row 7 = rank 8)

KIWIPEDE_PIECES = {
    (7, 0): -ROOK, (7, 4): -KING, (7, 7): -ROOK,
    (6, 0): -PAWN, (6, 2): -PAWN, (6, 3): -PAWN,
    (6, 4): -QUEEN, (6, 5): -PAWN, (6, 6): -BISHOP,
    (5, 0): -BISHOP, (5, 1): -KNIGHT, (5, 4): -PAWN,
    (5, 5): -KNIGHT, (5, 6): -PAWN,
    (4, 3): PAWN, (4, 4): KNIGHT,
    (3, 1): -PAWN, (3, 4): PAWN,
    (2, 2): KNIGHT, (2, 5): QUEEN, (2, 7): -PAWN,
    (1, 0): PAWN, (1, 1): PAWN, (1, 2): PAWN, (1, 3): BISHOP,
    (1, 4): BISHOP, (1, 5): PAWN, (1, 6): PAWN, (1, 7): PAWN,
    (0, 0): ROOK, (0, 4): KING, (0, 7): ROOK,
}

POSITION_3_PIECES = {
    (6, 2): -PAWN,
    (5, 3): -PAWN,
    (4, 0): KING, (4, 1): PAWN, (4, 7): -ROOK,
    (3, 1): ROOK, (3, 5): -PAWN, (3, 7): -KING,
    (1, 4): PAWN, (1, 6): PAWN,
}

POSITION_4_PIECES = {
    (7, 0): -ROOK, (7, 4): -KING, (7, 7): -ROOK,
    (6, 0): PAWN, (6, 1): -PAWN, (6, 2): -PAWN, (6, 3): -PAWN,
    (6, 5): -PAWN, (6, 6): -PAWN, (6, 7): -PAWN,
    (5, 1): -BISHOP, (5, 5): -KNIGHT, (5, 6): -BISHOP, (5, 7): KNIGHT,
    (4, 0): -KNIGHT, (4, 1): PAWN,
    (3, 0): BISHOP, (3, 1): BISHOP, (3, 2): PAWN, (3, 4): PAWN,
    (2, 0): -QUEEN, (2, 5): KNIGHT,
    (1, 0): PAWN, (1, 1): -PAWN, (1, 3): PAWN, (1, 6): PAWN, (1, 7): PAWN,
    (0, 0): ROOK, (0, 3): QUEEN, (0, 5): ROOK, (0, 6): KING,
}

POSITION_5_PIECES = {
    (7, 0): -ROOK, (7, 1): -KNIGHT, (7, 2): -BISHOP,
    (7, 3): -QUEEN, (7, 5): -KING, (7, 7): -ROOK,
    (6, 0): -PAWN, (6, 1): -PAWN, (6, 3): PAWN, (6, 4): -BISHOP,
    (6, 5): -PAWN, (6, 6): -PAWN, (6, 7): -PAWN,
    (5, 2): -PAWN,
    (3, 2): BISHOP,
    (1, 0): PAWN, (1, 1): PAWN, (1, 2): PAWN, (1, 4): KNIGHT,
    (1, 5): -KNIGHT, (1, 6): PAWN, (1, 7): PAWN,
    (0, 0): ROOK, (0, 1): KNIGHT, (0, 2): BISHOP, (0, 3): QUEEN,
    (0, 4): KING, (0, 7): ROOK,
}


def run_perft_suite() -> bool:
    all_ok = True
    suite = [
        (
            "Kiwipete",
            make_position(make_board(KIWIPEDE_PIECES), castling_rights="KQkq"),
            [48, 2039, 97862],
        ),
        (
            "Position 3 (en passant study)",
            make_position(make_board(POSITION_3_PIECES), castling_rights="-"),
            [14, 191, 2812, 43238],
        ),
        (
            "Position 4 (promotions, black to castle)",
            make_position(make_board(POSITION_4_PIECES), castling_rights="kq"),
            [6, 264, 9467, 422333],
        ),
        (
            "Position 5 (white promotion available)",
            make_position(make_board(POSITION_5_PIECES), castling_rights="KQ"),
            [44, 1486, 62379],
        ),
    ]

    print("=== Perft over special-move reference positions ===")
    for name, position, expected_counts in suite:
        for depth, expected in enumerate(expected_counts, start=1):
            actual = perft(position, depth)
            ok = actual == expected
            mark = "PASS" if ok else "FAIL"
            print(f"[{mark}] {name} perft({depth}) = {actual:,} (expected {expected:,})")
            all_ok = ok and all_ok
    return all_ok


def run_castling_checks() -> bool:
    all_ok = True
    kiwipete = make_position(make_board(KIWIPEDE_PIECES), castling_rights="KQkq")

    white_kingside = find_moves(kiwipete, (0, 4), (0, 6))
    ok = (
        len(white_kingside) == 1
        and white_kingside[0].is_castling == ((0, 7), (0, 5))
    )
    print(f"[{'PASS' if ok else 'FAIL'}] White O-O generated with rook relocation data")
    all_ok = ok and all_ok

    child = get_child(kiwipete, (0, 4), (0, 6))
    ok = (
        child is not None
        and child.board[0][6] == KING
        and child.board[0][5] == ROOK
        and child.board[0][4] == EMPTY
        and child.board[0][7] == EMPTY
        and child.castling_rights == "kq"
    )
    print(f"[{'PASS' if ok else 'FAIL'}] White O-O board result and rights update")
    all_ok = ok and all_ok

    white_queenside = find_moves(kiwipete, (0, 4), (0, 2))
    ok = (
        len(white_queenside) == 1
        and white_queenside[0].is_castling == ((0, 0), (0, 3))
    )
    print(f"[{'PASS' if ok else 'FAIL'}] White O-O-O generated")
    all_ok = ok and all_ok

    after_a3, _ = kiwipete.make_move((1, 0), (2, 0))
    black_kingside = find_moves(after_a3, (7, 4), (7, 6))
    ok = (
        len(black_kingside) == 1
        and black_kingside[0].is_castling == ((7, 7), (7, 5))
    )
    print(f"[{'PASS' if ok else 'FAIL'}] Black O-O generated for the engine's side")
    all_ok = ok and all_ok

    black_queenside = find_moves(after_a3, (7, 4), (7, 2))
    ok = (
        len(black_queenside) == 1
        and black_queenside[0].is_castling == ((7, 0), (7, 3))
    )
    print(f"[{'PASS' if ok else 'FAIL'}] Black O-O-O generated for the engine's side")
    all_ok = ok and all_ok

    return all_ok


def run_en_passant_checks() -> bool:
    all_ok = True

    ep_position = make_position(
        make_board({
            (0, 0): KING,
            (4, 4): PAWN,
            (4, 3): -PAWN,
            (7, 7): -KING,
        }),
        active_color=WHITE,
        castling_rights="-",
        en_passant_square=(5, 3),
    )
    ep_moves = find_moves(ep_position, (4, 4), (5, 3))
    ok = len(ep_moves) == 1 and ep_moves[0].is_en_passant
    print(f"[{'PASS' if ok else 'FAIL'}] En passant capture generated")
    all_ok = ok and all_ok

    child = get_child(ep_position, (4, 4), (5, 3))
    ok = (
        child is not None
        and child.board[4][3] == EMPTY
        and child.board[5][3] == PAWN
        and child.board[4][4] == EMPTY
    )
    print(f"[{'PASS' if ok else 'FAIL'}] En passant removes the captured pawn")
    all_ok = ok and all_ok

    pinned_position = make_position(
        make_board({
            (4, 7): KING,
            (4, 4): PAWN,
            (4, 0): -ROOK,
            (4, 3): -PAWN,
            (0, 0): -KING,
        }),
        active_color=WHITE,
        castling_rights="-",
        en_passant_square=(5, 3),
    )
    ep_moves = find_moves(pinned_position, (4, 4), (5, 3))
    pushes = find_moves(pinned_position, (4, 4), (5, 4))
    ok = len(ep_moves) == 0 and len(pushes) == 1
    print(
        f"[{'PASS' if ok else 'FAIL'}] En passant forbidden when it exposes "
        "the king (rank pin); e6 push stays legal"
    )
    all_ok = ok and all_ok

    return all_ok


def run_promotion_checks() -> bool:
    all_ok = True
    position_5 = make_position(make_board(POSITION_5_PIECES), castling_rights="KQ")

    promos = find_moves(position_5, (6, 3), (7, 2))
    promo_pieces = {move.promotion_piece for move in promos}
    ok = (
        len(promos) == 4
        and promo_pieces == {QUEEN, ROOK, BISHOP, KNIGHT}
    )
    print(f"[{'PASS' if ok else 'FAIL'}] All 4 promotion pieces generated on capture")
    all_ok = ok and all_ok

    queen_child = None
    for child, move in position_5.get_legal_positions_and_moves():
        if (
            move.from_sq == (6, 3) and move.to_sq == (7, 2)
            and move.promotion_piece == QUEEN
        ):
            queen_child = child
    ok = (
        queen_child is not None
        and queen_child.board[7][2] == QUEEN
        and queen_child.board[6][3] == EMPTY
        and queen_child.board[7][3] == -QUEEN
    )
    print(f"[{'PASS' if ok else 'FAIL'}] Promotion replaces the pawn correctly")
    all_ok = ok and all_ok

    move, score = MiniMaxEngine(MaterialEvaluator(), max_depth=1).find_best_move(
        position_5
    )
    ok = (
        move.from_sq == (6, 3)
        and move.to_sq == (7, 2)
        and move.promotion_piece == QUEEN
        and score == 11.0
    )
    print(
        f"[{'PASS' if ok else 'FAIL'}] Engine prefers queen promotion "
        "(d7xc8=Q, score +11.0)"
    )
    if not ok:
        print(f"  got ({move.from_sq}, {move.to_sq}) promo={move.promotion_piece} score {score}")
    all_ok = ok and all_ok

    return all_ok


def main() -> None:
    all_ok = True

    all_ok = run_perft_suite() and all_ok
    print()
    all_ok = run_castling_checks() and all_ok
    print()
    all_ok = run_en_passant_checks() and all_ok
    print()
    all_ok = run_promotion_checks() and all_ok

    print(f"\n=== Overall result: {'PASS' if all_ok else 'FAIL'} ===")


if __name__ == "__main__":
    main()
