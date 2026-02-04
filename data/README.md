# Data schemas

This prototype expects three CSV inputs, each with minimal columns.

## `topology_edges.csv`
Describes physical or logical adjacency (static topology).

| column | type | description |
| --- | --- | --- |
| source | string/int | node id (u) |
| target | string/int | node id (v) |
| weight | float | optional link weight (defaults to 1.0) |

## `routing_paths.csv`
Describes routing paths from node to root over time windows.

| column | type | description |
| --- | --- | --- |
| time_window | string | window identifier (e.g., `t1`, `t2`) |
| node_id | string/int | source node |
| path | string | path as `nodeA>nodeB>root` |

## `performance_metrics.csv`
Describes per-node PDR and delay statistics aggregated by window.

| column | type | description |
| --- | --- | --- |
| time_window | string | window identifier |
| node_id | string/int | node id |
| pdr | float | packet delivery ratio (0-1) |
| delay_ms | float | mean end-to-end delay (ms) |
| attack_rate | float | attack rate (0-1) |
| scenario | string | topology/scenario label |
