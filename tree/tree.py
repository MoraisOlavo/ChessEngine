from position.base import Move, Position

class Node():
    """
    Represents a node in the search tree.

    Attributes:
        position (Position): The chess position at this node.
        parent (Node): The parent node in the tree.
        children (list[Node]): The children nodes of this node.
        move (Move): The move that led to this node.
        score (float): The score of this node.
    """

    def __init__(
        self,
        position: Position,
        parent: "Node | None" = None,
        children: "list[Node] | None" = None,
        move: Move | None = None,
        score: float = 0
    ):
        self.position = position
        self.parent = parent
        self.children = children if children is not None else []
        self.move = move
        self.score = score

    def create_tree(self, max_depth: int) -> "Node":
        if max_depth <= 0:
            return self

        positions_and_moves = self.position.get_legal_positions_and_moves()
        for position, move in positions_and_moves:
            child_node = Node(position=position, parent=self, move=move)
            self.children.append(child_node)
            child_node.create_tree(max_depth - 1)
        
        return self
        
        