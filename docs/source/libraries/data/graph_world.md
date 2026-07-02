# GraphWorld, GraphNode, GraphEdge

`GraphWorld` visualizes an undirected graph.
Nodes are placed at explicit pixel positions; edges are drawn as lines between them.
The world is well-suited for BFS, DFS, Dijkstra and other graph traversal tasks.

## Building the graph

```python
from miniworlds_data import GraphWorld

world = GraphWorld(width=700, height=500)
a = world.add_node("A", position=(100, 100))
b = world.add_node("B", position=(300, 100))
c = world.add_node("C", position=(200, 300))
world.connect(a, b)
world.connect(a, c)
world.connect(b, c)
world.set_start(a)
world.set_target(c)
world.run()
```

## GraphWorld operations

| Method | Description |
|---|---|
| `add_node(name, value, position)` | Add a node with a unique name and optional display value and position; return the `GraphNode`. |
| `get_node(name)` | Return the node with the given name. |
| `connect(source, target)` | Connect two nodes with an undirected edge; return the `GraphEdge`. |
| `neighbors(node)` | Return the list of neighboring `GraphNode` objects. |
| `set_start(node)` | Mark a node as the search origin (red). |
| `set_target(node)` | Mark a node as the search goal (blue). |
| `highlight(node, state, color)` | Highlight a node with a named state or explicit color. |
| `highlight_edge(source, target, state, color)` | Highlight the edge between two nodes. |
| `reset_colors()` | Reset all nodes and edges to their default/start/target colors. |
| `path_edges(path)` | Highlight the edges along a sequence of node names or instances as a path. |
| `nodes` | List of all `GraphNode` instances (property). |
| `edges` | List of all `GraphEdge` instances (property). |

Node states: `default`, `visited`, `current`, `frontier`, `start`, `target`, `path`.

Edge states: `default`, `visited`, `path`.

## GraphNode attributes

| Attribute | Description |
|---|---|
| `name` | Unique identifier string. |
| `value` | Displayed value. |
| `state` | Current highlight state string. |
| `set_state(state, color)` | Change the highlight state. |

## GraphEdge attributes

| Attribute | Description |
|---|---|
| `source` | Source `GraphNode`. |
| `target` | Target `GraphNode`. |
| `set_state(state, color)` | Change the edge color. |
| `refresh()` | Recompute the line endpoints from the current node positions. |

## API Reference

```{eval-rst}
.. py:class:: miniworlds_data.graph_world.GraphWorld(*, width=600, height=400, node_radius=22, background=(250, 250, 250, 255))

   Visualizes an undirected graph. The table above lists the public graph
   operations intended for traversal and pathfinding examples.

.. py:class:: miniworlds_data.graph_world.GraphNode

   Node actor used by :class:`GraphWorld`.

.. py:class:: miniworlds_data.graph_world.GraphEdge

   Edge actor used by :class:`GraphWorld`.
```
