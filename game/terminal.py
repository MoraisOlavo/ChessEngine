"""
Terminal chess game: human vs engine, entered with the board's own labels.

The board is displayed through the position's __str__ (Unicode grid with
algebraic rank/file labels) and moves are typed with those same labels:
"<from_square><to_square>", e.g. e2e4. Spaces are ignored and promotions
append the piece letter (e7d8q); if omitted, the program asks for it.
Internally the labels are converted to the (row, col) convention
(row = rank - 1, column a=0 ... h=7).

Special moves are entered naturally: castling as the king's two-square move
(e1g1 / e1c1), en passant as the pawn's diagonal move to the empty square.

Run with: python3 -m game.terminal [--engine alphabeta] [--depth 3]
                                   [--evaluator material] [--color white]
"""

import argparse
import re
import sys
import time

from position.base import BISHOP, BLACK, KNIGHT, QUEEN, ROOK, WHITE
from position.matrix import MatrixPosition
from game.game import (
    Game,
    STATUS_CHECKMATE,
    STATUS_DRAW,
    STATUS_IN_PROGRESS,
    STATUS_STALEMATE,
)

PROMOTION_CHOICES = {"q": QUEEN, "r": ROOK, "b": BISHOP, "n": KNIGHT}
PROMOTION_NAMES = {QUEEN: "queen", ROOK: "rook", BISHOP: "bishop", KNIGHT: "knight"}

MOVE_PATTERN = re.compile(r"([a-h])([1-8])([a-h])([1-8])([qrbn])?")


def square_name(square: tuple[int, int]) -> str:
    """Converts an internal (row, col) square to its displayed label like 'e4'."""
    return MatrixPosition.to_algebraic_square(*square)


def parse_move_request(raw: str):
    """
    Parses a move request like 'e2e4', 'e2 e4' or 'e7d8q'.

    Returns ((from_row, from_col), (to_row, to_col), promotion_letter or None),
    or None if the text does not match the expected format.
    """
    compact = re.sub(r"\s+", "", raw)
    match = MOVE_PATTERN.fullmatch(compact)
    if match is None:
        return None
    from_col = ord(match.group(1)) - ord("a")
    from_row = int(match.group(2)) - 1
    to_col = ord(match.group(3)) - ord("a")
    to_row = int(match.group(4)) - 1
    return (from_row, from_col), (to_row, to_col), match.group(5)


def color_name(color: str) -> str:
    return "White" if color == WHITE else "Black"


def describe_move(move) -> str:
    description = f"{square_name(move.from_sq)}{square_name(move.to_sq)}"
    extras = []
    if move.is_castling is not None:
        extras.append("castling")
    if move.is_en_passant:
        extras.append("en passant")
    if move.promotion_piece is not None:
        extras.append(f"promotes to {PROMOTION_NAMES[move.promotion_piece]}")
    if extras:
        description += " [" + ", ".join(extras) + "]"
    return description


def build_engine(args):
    from evaluator.simple import PieceCountEvaluator
    from evaluator.weighted import MaterialEvaluator
    from engine.alphabeta import AlphaBetaEngine
    from engine.minimax import MiniMaxEngine

    evaluator = (
        MaterialEvaluator() if args.evaluator == "material" else PieceCountEvaluator()
    )
    engine_class = AlphaBetaEngine if args.engine == "alphabeta" else MiniMaxEngine
    return engine_class(evaluator, max_depth=args.depth)


def parse_args():
    parser = argparse.ArgumentParser(description="Play chess against the engine.")
    parser.add_argument(
        "--engine", choices=["minimax", "alphabeta"], default="alphabeta"
    )
    parser.add_argument("--depth", type=int, default=3)
    parser.add_argument(
        "--evaluator", choices=["material", "piece_count"], default="material"
    )
    parser.add_argument("--color", choices=["white", "black"], default="white")
    return parser.parse_args()


def read_human_move(game: Game):
    """
    Reads one move from the terminal.

    Returns a Move, the string "board" (reprint request) or None (quit).
    """
    while True:
        try:
            raw = input(
                f"\n{color_name(game.position.get_color())} to move "
                "(move | legal | board | quit): "
            ).strip().lower()
        except (EOFError, KeyboardInterrupt):
            return None

        if raw in ("quit", "exit", "q"):
            return None
        if raw == "board":
            return "board"
        if raw == "legal":
            moves = game.legal_moves()
            print(f"{len(moves)} legal moves:")
            for move in moves:
                print(f"  {describe_move(move)}")
            continue

        request = parse_move_request(raw)
        if request is None:
            print("Enter a move like e2e4 (promotion: e7d8q). Commands: legal | board | quit")
            continue
        from_sq, to_sq, promotion_letter = request

        matches = game.find_moves(from_sq, to_sq)
        if not matches:
            print("Illegal move. Type 'legal' to list the legal moves.")
            continue
        if len(matches) == 1:
            return matches[0]

        if promotion_letter is None:
            answer = input(
                "Promote to which piece? (q/r/b/n): "
            ).strip().lower()
            chosen = re.search(r"[qrbn]", answer)
            if chosen is None:
                print("No promotion piece chosen; move cancelled.")
                continue
            promotion_letter = chosen.group()
        promotion_piece = PROMOTION_CHOICES[promotion_letter]
        for move in matches:
            if move.promotion_piece == promotion_piece:
                return move
        print("No such promotion move.")


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    args = parse_args()
    engine = build_engine(args)
    game = Game()
    human_color = WHITE if args.color == "white" else BLACK
    engine_color = BLACK if human_color == WHITE else WHITE

    print("=== Chess: human vs engine ===")
    print(f"Engine: {args.engine} | depth {args.depth} | {args.evaluator} evaluator")
    print(f"You play {color_name(human_color)}.")
    print("Move format: <from><to> using the board labels (e.g. e2e4)")
    print("Castling: e1g1 (O-O) or e1c1 (O-O-O) | Promotion: e7d8q (or you'll be asked)")

    while True:
        status = game.status()
        if status != STATUS_IN_PROGRESS:
            print()
            print(game.position)
            if status == STATUS_CHECKMATE:
                winner = (
                    engine_color if game.position.get_color() == human_color
                    else human_color
                )
                print(f"Checkmate! {color_name(winner)} wins.")
            elif status == STATUS_STALEMATE:
                print("Stalemate - draw.")
            else:
                print("Draw.")
            break

        if game.position.get_color() == human_color:
            print()
            print(game.position)
            if game.position.is_in_check():
                print("You are in CHECK!")
            move = read_human_move(game)
            if move is None:
                print("Game abandoned.")
                break
            if move == "board":
                continue
            game.apply(move)
            print(f"You played: {describe_move(move)}")
        else:
            print(f"\n{color_name(engine_color)} (engine) is thinking...")
            start = time.perf_counter()
            move, score = engine.find_best_move(game.position)
            elapsed = time.perf_counter() - start
            game.apply(move)
            print(
                f"Engine played {describe_move(move)} "
                f"(score {score:+.1f}, {elapsed:.2f}s)"
            )


if __name__ == "__main__":
    main()
