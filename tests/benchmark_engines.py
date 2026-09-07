"""
Performance benchmark for the engine package.

Measures wall time and evaluator calls (a proxy for the work done) for
MiniMaxEngine and AlphaBetaEngine from the initial position, showing how
much alpha-beta pruning saves at each depth.

Plain minimax only runs up to depth 4: its cost grows roughly with the
branching factor (~20x) per extra ply, reaching hours at depth 6.
AlphaBeta keeps going to higher depths.

Run with: python3 -m tests.benchmark_engines [max_depth]   (default: 4)
"""

import sys
import time

from position.base import Position
from position.matrix import MatrixPosition
from evaluator.base import Evaluator
from evaluator.weighted import MaterialEvaluator
from engine.minimax import MiniMaxEngine
from engine.alphabeta import AlphaBetaEngine

MINIMAX_MAX_DEPTH = 4


class CountingEvaluator(Evaluator):
    """Evaluator wrapper that counts how many positions were scored."""

    def __init__(self, inner: Evaluator):
        self.inner = inner
        self.calls = 0

    def evaluate(self, position: Position) -> float:
        self.calls += 1
        return self.inner.evaluate(position)


def run_one(
    engine_class: type,
    depth: int,
    position: MatrixPosition
) -> tuple[tuple[int, int], float, float, int]:
    """Builds a fresh engine, runs one search and returns move, score, time and eval count."""
    evaluator = CountingEvaluator(MaterialEvaluator())
    engine = engine_class(evaluator, max_depth=depth)

    start = time.perf_counter()
    move, score = engine.find_best_move(position)
    elapsed = time.perf_counter() - start

    return (move.from_sq, move.to_sq), score, elapsed, evaluator.calls


def print_row(
    name: str,
    move: tuple[int, int],
    score: float,
    elapsed: float,
    calls: int
) -> None:
    rate = calls / max(elapsed, 1e-9)
    print(
        f"  {name:<9} move {str(move):<12} score {score:+11.1f} | "
        f"{elapsed:7.2f}s | {calls:>10,} evals | {rate:>9,.0f} evals/s"
    )


def main(max_depth: int) -> None:
    position = MatrixPosition.initial_position()
    print("=== Engine benchmark (initial position, MaterialEvaluator) ===")

    for depth in range(1, min(max_depth, MINIMAX_MAX_DEPTH) + 1):
        minimax = run_one(MiniMaxEngine, depth, position)
        alphabeta = run_one(AlphaBetaEngine, depth, position)

        print(f"\nDepth {depth}")
        print_row("MiniMax", *minimax)
        print_row("AlphaBeta", *alphabeta)

        if minimax[0] != alphabeta[0] or minimax[1] != alphabeta[1]:
            print("  WARNING: engines disagree on the best move or score!")
        else:
            saved = 100 * (1 - alphabeta[3] / minimax[3])
            speedup = minimax[2] / max(alphabeta[2], 1e-9)
            print(
                f"  same result; pruning skipped {saved:.0f}% of the "
                f"evaluations ({speedup:.1f}x faster)"
            )

    for depth in range(MINIMAX_MAX_DEPTH + 1, max_depth + 1):
        alphabeta = run_one(AlphaBetaEngine, depth, position)

        print(
            f"\nDepth {depth} "
            "(AlphaBeta only; plain MiniMax would take hours at this depth)"
        )
        print_row("AlphaBeta", *alphabeta)

    print("\n=== Benchmark done ===")


if __name__ == "__main__":
    try:
        max_depth = int(sys.argv[1]) if len(sys.argv) > 1 else 4
    except ValueError:
        print("Usage: python3 -m tests.benchmark_engines [max_depth]")
        sys.exit(1)
    if max_depth < 1:
        print("max_depth must be at least 1")
        sys.exit(1)
    main(max_depth)
