# TreeWorld and TreeNode

`TreeWorld` visualizes a binary tree.
Nodes are placed via a level-order layout computed automatically by the world;
edges are drawn as lines between parent and child nodes.

## Building the tree

```python
from miniworlds_data import TreeWorld

world = TreeWorld()
root = world.set_root(5)
left  = world.add_left(root, 3)
right = world.add_right(root, 8)
world.add_left(left, 1)
world.add_right(left, 4)
world.run()
```

## TreeWorld operations

| Method | Description |
|---|---|
| `set_root(value)` | Create and return the root node. Can only be called once. |
| `add_left(parent, value)` | Add a left child to `parent`; return the new node. |
| `add_right(parent, value)` | Add a right child to `parent`; return the new node. |
| `highlight(node, state)` | Highlight a node with a named state. States: `default`, `visited`, `current`, `root`. |
| `highlight_edge(parent, child, visited)` | Color the edge between `parent` and `child`. |
| `reset_colors()` | Reset all nodes and edges to their default colors. |
| `inorder()` | Return nodes in in-order sequence. |
| `preorder()` | Return nodes in pre-order sequence. |
| `postorder()` | Return nodes in post-order sequence. |
| `root` | The root `TreeNode` (property, `None` if not yet set). |
| `nodes` | List of all `TreeNode` instances (property). |

## TreeNode attributes

| Attribute | Description |
|---|---|
| `value` | The stored value. |
| `left` | Left child `TreeNode` or `None`. |
| `right` | Right child `TreeNode` or `None`. |
| `state` | Current highlight state string. |
| `set_state(state)` | Change the highlight state and update the color. |

## API Reference

```{eval-rst}
.. autoclass:: miniworlds_data.tree_world.TreeWorld
   :members:
   :no-private-members:

.. autoclass:: miniworlds_data.tree_world.TreeNode
   :members:
   :no-private-members:
```
