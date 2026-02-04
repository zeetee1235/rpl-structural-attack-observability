# Cooja Log Format (printf) and CSV Schema

This spec defines a minimal, structured log format for extracting exposure, routing, and performance
metrics. All logs are single-line key/value pairs so the parser can be strict and fast.

## Log format rules

- Prefix every line with `OBS` to make parsing cheap.
- Use `key=value` pairs separated by spaces.
- Required keys: `ts` (sim time in ms), `node` (node id), `ev` (event type).
- Optional keys: `seq`, `src`, `dst`, `parent`, `rank`, `rssi`, `delay_ms`, `count`, `role`.

## Event types (printf)

### Packet events

```
OBS ts=123456 node=2 ev=DATA_TX seq=101 dst=1
OBS ts=123789 node=6 ev=DATA_RX seq=101 src=2
OBS ts=123790 node=6 ev=DATA_FWD seq=101 dst=1
OBS ts=123791 node=6 ev=DATA_DROP seq=101 src=2 reason=attack
OBS ts=124000 node=1 ev=ROOT_RX seq=101 src=2
```

### Delay events (end-to-end, measured at root)

```
OBS ts=124000 node=1 ev=DELAY seq=101 src=2 delay_ms=211
```

### Routing/parent events

```
OBS ts=120000 node=4 ev=PARENT parent=2 rank=256
OBS ts=120000 node=4 ev=RANK rank=256
```

### Neighbor/link events (optional)

```
OBS ts=120500 node=4 ev=NEIGHBOR neighbor=7 rssi=-83
```

### Attack summary (periodic at attacker)

```
OBS ts=1800000 node=6 ev=ATTACK_STATS recv=240 fwd=48 drop=192
```

### Control overhead (optional)

```
OBS ts=121000 node=3 ev=DIO_TX count=1
OBS ts=121100 node=3 ev=DAO_TX count=1
```

## CSV schema to extract

### `topology_edges.csv`

Physical/logical adjacency from neighbor logs.

| column | type | description |
| --- | --- | --- |
| source | string/int | node id (u) |
| target | string/int | node id (v) |
| weight | float | link weight (e.g., RSSI-derived) |

### `routing_paths.csv`

Per window routing paths.

| column | type | description |
| --- | --- | --- |
| time_window | string | window id (e.g., `t1`) |
| node_id | string/int | source node |
| path | string | `nodeA>nodeB>root` |

### `performance_metrics.csv`

Per node performance summary.

| column | type | description |
| --- | --- | --- |
| time_window | string | window id |
| node_id | string/int | node id |
| pdr | float | packet delivery ratio (0-1) |
| delay_ms | float | mean end-to-end delay (ms) |
| jitter_ms | float | optional, std dev of delay (ms) |
| tx_count | int | data packets sent |
| rx_count | int | data packets received (root only) |
| drop_count | int | data packets dropped |
| parent_churn | int | number of parent changes |
| dio_tx | int | DIO count (optional) |
| dao_tx | int | DAO count (optional) |
| attack_rate | float | configured attack rate (0-1) |
| scenario | string | scenario label |

### `attack_exposure.csv`

Ground-truth exposure based on attacker counters.

| column | type | description |
| --- | --- | --- |
| time_window | string | window id |
| attacker_id | string/int | attacker node id |
| recv_data | int | attacker received data packets |
| fwd_data | int | attacker forwarded data packets |
| drop_data | int | attacker dropped data packets |
| root_rx_total | int | total data packets received at root |
| exposure | float | `recv_data / root_rx_total` |

## Notes

- `exposure` from routing paths is a model proxy; `attack_exposure.csv` is the measured ground truth.
- If you do not emit neighbor logs, `topology_edges.csv` can be constructed from the static Cooja
  coordinates instead (use a simple distance threshold).
