# Data schemas

This prototype expects three CSV inputs with minimal columns. Additional optional
columns are supported for richer observability analysis.

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

Optional columns (if available):

| column | type | description |
| --- | --- | --- |
| jitter_ms | float | delay std dev (ms) |
| tx_count | int | data packets sent |
| rx_count | int | data packets received |
| drop_count | int | data packets dropped |
| parent_churn | int | number of parent changes |
| dio_tx | int | DIO count |
| dao_tx | int | DAO count |

## `attack_exposure.csv` (optional)
Ground-truth exposure based on attacker counters.

| column | type | description |
| --- | --- | --- |
| time_window | string | window identifier |
| attacker_id | string/int | attacker node id |
| recv_data | int | attacker received data packets |
| fwd_data | int | attacker forwarded data packets |
| drop_data | int | attacker dropped data packets |
| root_rx_total | int | total data packets received at root |
| exposure | float | `recv_data / root_rx_total` |

See `docs/logging_spec.md` for the recommended log format that maps to these CSVs.
