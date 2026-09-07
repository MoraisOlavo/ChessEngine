"""
Teste da árvore de busca (Node.create_tree) a partir da posição inicial.

Compara a contagem de nós por nível com os valores oficiais de perft,
verifica a estrutura da árvore e mede tempo e memória.

Executar com: python3 -m tests.test_tree
"""

import gc
import time
import tracemalloc

from position.base import PAWN
from position.matrix import MatrixPosition
from tree.tree import Node

PERFT_REFERENCE = {1: 20, 2: 400, 3: 8_902, 4: 197_281}
TOTAL_NODES_DEPTH_5 = 5_072_213  # 20 + 400 + 8902 + 197281 + 4865609


def count_by_level(root: Node) -> dict[int, int]:
    counts = {}
    frontier = [root]
    level = 0
    while frontier:
        counts[level] = len(frontier)
        next_frontier = []
        for node in frontier:
            next_frontier.extend(node.children)
        frontier = next_frontier
        level += 1
    return counts


def derived_ep_target(parent_position, move) -> tuple[int, int] | None:
    """Deriva o en passant target de um pulo duplo de peão (o que o gerador passa ao make_move)."""
    piece = parent_position.board[move.from_sq[0]][move.from_sq[1]]
    if abs(piece) == PAWN and abs(move.to_sq[0] - move.from_sq[0]) == 2:
        return ((move.from_sq[0] + move.to_sq[0]) // 2, move.from_sq[1])
    return None


def check_structure(root: Node, max_depth: int, sample_every: int) -> list[str]:
    failures = []
    sampled = 0
    frontier = [(root, 0)]
    while frontier:
        node, depth = frontier.pop()
        move_keys = set()
        for child in node.children:
            if child.parent is not node:
                failures.append(f"depth {depth}: child.parent nao aponta para o pai")
            key = (child.move.from_sq, child.move.to_sq, child.move.promotion_piece)
            if key in move_keys:
                failures.append(f"depth {depth}: lance duplicado entre irmaos: {key}")
            move_keys.add(key)
            if child.position.get_color() == node.position.get_color():
                failures.append(f"depth {depth}: active_color nao alternou")
            if depth == max_depth and node.children:
                failures.append(f"depth {max_depth}: folha da fronteira tem filhos")
            sampled += 1
            if sampled % sample_every == 0:
                ep_target = derived_ep_target(node.position, child.move)
                reproduced, _ = node.position.make_move(
                    child.move.from_sq,
                    child.move.to_sq,
                    child.move.promotion_piece,
                    child.move.is_en_passant,
                    ep_target,
                    child.move.is_castling,
                )
                if reproduced.board != child.position.board:
                    failures.append(
                        f"depth {depth}: make_move({child.move.from_sq} -> {child.move.to_sq}) "
                        f"nao reproduz o board do filho"
                    )
            frontier.append((child, depth + 1))
    return failures


def run_depth(depth: int, sample_every: int) -> bool:
    root = Node(position=MatrixPosition.initial_position())

    t0 = time.perf_counter()
    root.create_tree(depth)
    build_s = time.perf_counter() - t0

    t0 = time.perf_counter()
    counts = count_by_level(root)
    traversal_s = time.perf_counter() - t0

    failures = check_structure(root, depth, sample_every)

    counts_ok = all(counts.get(lv) == PERFT_REFERENCE[lv] for lv in range(1, depth + 1))
    status = "PASS" if counts_ok and not failures else "FAIL"

    total = sum(counts.values())
    print(f"[{status}] Depth {depth}: {total:,} nos no total | build {build_s:.3f}s | "
          f"travessia {traversal_s:.3f}s | {total / build_s:,.0f} nos/s")

    for lv in range(1, depth + 1):
        expected = PERFT_REFERENCE[lv]
        actual = counts.get(lv)
        mark = "PASS" if actual == expected else "FAIL"
        print(f"  [{mark}] nivel {lv}: {actual:,} nos (esperado {expected:,})")

    if failures:
        print(f"  [FAIL] {len(failures)} falha(s) estrutural(is) (amostra 1/{sample_every}):")
        for f in failures[:5]:
            print(f"    - {f}")
    else:
        print(f"  [PASS] estrutura ok (parent, duplicatas, cores, ep/board em amostra 1/{sample_every})")

    del root
    gc.collect()
    return counts_ok and not failures


def main() -> None:
    print("=== Teste da arvore de busca (perft a partir da posicao inicial) ===\n")

    all_ok = True
    for depth in (1, 2, 3):
        all_ok = run_depth(depth, sample_every=1) and all_ok
        print()

    print("--- Depth 4 ---")
    all_ok = run_depth(4, sample_every=50) and all_ok

    tracemalloc.start()
    root = Node(position=MatrixPosition.initial_position())
    root.create_tree(4)
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    del root
    gc.collect()

    print(f"\n  pico de memoria da arvore (depth 4): {peak / 1e6:,.0f} MB")
    print(f"  previsao depth 5 (~{TOTAL_NODES_DEPTH_5:,} nos): "
          f"{peak * TOTAL_NODES_DEPTH_5 / 206_604 / 1e9:,.1f} GB")

    print(f"\n=== Resultado geral: {'PASS' if all_ok else 'FAIL'} ===")


if __name__ == "__main__":
    main()
