# Sub-Libraries

**miniworlds** can be extended with optional sub-libraries that each add a focused domain on top of the core engine.
Install each library independently; only bring in what your project needs.

| Library | pip package | Description |
|---|---|---|
| [miniworlds-robot](robot/index) | `miniworlds-robot` | Grid-based robot world for teaching algorithmic thinking |
| [miniworlds-data](data/index) | `miniworlds-data` | Visual data structures (list, stack, queue, tree, graph) |
| [miniworlds-physics](physics/index) | `miniworlds-physics` | Physics simulation via pymunk |
| [miniworlds-turtle](turtle/index) | `miniworlds-turtle` | Compatible re-implementation of Python's `turtle` module |

```{toctree}
---
maxdepth: 2
hidden: true
---
robot/index
data/index
physics/index
turtle/index
```
