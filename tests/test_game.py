"""
Tests for the game package (Game orchestration, special moves included).

Run with: python3 -m tests.test_game
"""

from position.base import BLACK, EMPTY, KING, PAWN, QUEEN, ROOK, WHITE
from position.matrix import MatrixPosition
from game.game import Game, STATUS_CHECKMATE, STATUS_IN_PROGRESS, STATUS_STALEMATE

from tests.test_special_moves import (
    KIWIPEDE_PIECES,
    POSITION_5_PIECES,
    make_board,
    make_position,
)
from tests.test_engine import play_moves


def run_case(description: str, ok: bool) -> bool:
    mark = "PASS" if ok else "FAIL"
    print(f"[{mark}] {description}")
    return ok


def main() -> None:
    print("=== Game tests ===")
    all_ok = True

    game = Game()
    all_ok = run_case(
        "Initial game has 20 legal moves and is in progress",
        len(game.legal_moves()) == 20
        and game.status() == STATUS_IN_PROGRESS
        and game.position.get_color() == WHITE,
    ) and all_ok

    matches = game.find_moves((1, 4), (3, 4))
    ok = len(matches) == 1
    child = game.apply(matches[0]) if ok else None
    ok = (
        ok
        and game.position.get_color() == BLACK
        and game.position.board[3][4] == PAWN
        and game.position.board[1][4] == EMPTY
        and game.position.en_passant_square == (2, 4)
    )
    print(f"[{'PASS' if ok else 'FAIL'}] e2-e4 applies with en passant target set")
    all_ok = ok and all_ok

    illegal = game.find_moves((1, 4), (3, 4))
    ok = len(illegal) == 0
    print(f"[{'PASS' if ok else 'FAIL'}] Illegal request matches no move")
    all_ok = ok and all_ok

    fools_mate = play_moves(MatrixPosition.initial_position(), [
        ((1, 5), (2, 5)),
        ((6, 4), (4, 4)),
        ((1, 6), (3, 6)),
        ((7, 3), (3, 7)),
    ])
    all_ok = run_case(
        "Fool's mate position reports checkmate",
        Game(fools_mate).status() == STATUS_CHECKMATE,
    ) and all_ok

    stalemate = make_position(make_board({
        (7, 7): -KING,
        (6, 5): QUEEN,
        (5, 6): KING,
    }), active_color=BLACK)
    all_ok = run_case(
        "Sparse position reports stalemate",
        Game(stalemate).status() == STATUS_STALEMATE,
    ) and all_ok

    promo_game = Game(make_position(make_board(POSITION_5_PIECES), castling_rights="KQ"))
    promos = promo_game.find_moves((6, 3), (7, 2))
    queen_move = next(m for m in promos if m.promotion_piece == QUEEN)
    promo_game.apply(queen_move)
    ok = (
        len(promos) == 4
        and promo_game.position.board[7][2] == QUEEN
        and promo_game.position.board[6][3] == EMPTY
    )
    print(f"[{'PASS' if ok else 'FAIL'}] Human promotion applied via Game")
    all_ok = ok and all_ok

    castle_game = Game(make_position(make_board(KIWIPEDE_PIECES), castling_rights="KQkq"))
    castles = castle_game.find_moves((0, 4), (0, 6))
    castle_game.apply(castles[0])
    ok = (
        len(castles) == 1
        and castles[0].is_castling == ((0, 7), (0, 5))
        and castle_game.position.board[0][6] == KING
        and castle_game.position.board[0][5] == ROOK
        and castle_game.position.castling_rights == "kq"
    )
    print(f"[{'PASS' if ok else 'FAIL'}] Human castling applied via Game")
    all_ok = ok and all_ok

    print(f"\n=== Overall result: {'PASS' if all_ok else 'FAIL'} ===")


if __name__ == "__main__":
    main()
