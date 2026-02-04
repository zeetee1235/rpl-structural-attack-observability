# Scenario Coordinate Plans (A-D)

All coordinates are in meters and assume a 2D plane in Cooja with TX range 50 m and interference range 100 m.
Node IDs are fixed for repeatable logging.

Scenario A: Low Exposure (attacker is a leaf, rarely on routes)

Attacker ID: 6
Root ID: 1

| node_id | role | x_m | y_m | notes |
| --- | --- | --- | --- | --- |
| 1 | root | 0 | 0 | DODAG root |
| 2 | sender | 10 | 0 | direct to root |
| 3 | sender | -10 | 0 | direct to root |
| 4 | sender | 0 | 10 | direct to root |
| 5 | sender | 0 | -10 | direct to root |
| 6 | attacker | 45 | 45 | leaf, not on main routes |
| 7 | relay | 20 | 20 | alternate parent candidate |
| 8 | relay | -20 | 20 | alternate parent candidate |
| 9 | relay | 20 | -20 | alternate parent candidate |
| 10 | relay | -20 | -20 | alternate parent candidate |

Scenario B: High Exposure (attacker is a cut-vertex)

Attacker ID: 6
Root ID: 1

| node_id | role | x_m | y_m | notes |
| --- | --- | --- | --- | --- |
| 1 | root | 0 | 0 | DODAG root |
| 6 | attacker | 30 | 0 | mandatory relay |
| 2 | sender | 60 | 0 | only reachable via attacker |
| 3 | sender | 60 | 10 | only reachable via attacker |
| 4 | sender | 60 | -10 | only reachable via attacker |
| 5 | sender | 70 | 0 | only reachable via attacker |
| 7 | sender | 70 | 10 | only reachable via attacker |
| 8 | sender | 70 | -10 | only reachable via attacker |
| 9 | sender | 80 | 0 | edge of attacker range |
| 10 | sender | 80 | 10 | edge of attacker range |

Scenario C: High Path Diversity (multiple parent candidates)

Attacker ID: 6
Root ID: 1

| node_id | role | x_m | y_m | notes |
| --- | --- | --- | --- | --- |
| 1 | root | 0 | 0 | DODAG root |
| 2 | relay | 25 | 15 | parent candidate |
| 3 | relay | 25 | -15 | parent candidate |
| 4 | relay | 50 | 0 | bridge relay |
| 5 | sender | 55 | 15 | has 2-3 parent options |
| 6 | attacker | 40 | 0 | optional parent, not mandatory |
| 7 | sender | 55 | -15 | has 2-3 parent options |
| 8 | sender | 70 | 0 | can switch between relays |
| 9 | sender | 70 | 15 | can switch between relays |
| 10 | sender | 70 | -15 | can switch between relays |

Scenario D: Same APL, Different Centrality (single topology, two attacker placements)

Root ID: 1

Topology coordinates

| node_id | role | x_m | y_m | notes |
| --- | --- | --- | --- | --- |
| 1 | root | 0 | 0 | DODAG root |
| 2 | relay | 25 | 0 | parent candidate |
| 3 | relay | 25 | 20 | parent candidate |
| 4 | relay | 25 | -20 | parent candidate |
| 5 | relay | 50 | 0 | central relay |
| 6 | sender | 70 | 0 | 2-hop to root |
| 7 | sender | 70 | 20 | 2-hop to root |
| 8 | sender | 70 | -20 | 2-hop to root |
| 9 | relay | 50 | 20 | peripheral relay |
| 10 | relay | 50 | -20 | peripheral relay |

Attacker placements for Scenario D

| attacker_id | placement | expected betweenness |
| --- | --- | --- |
| 5 | central | high |
| 9 | peripheral | low |

Notes

Use the same topology coordinates and only swap attacker ID between runs to isolate centrality effects while holding APL roughly constant.
