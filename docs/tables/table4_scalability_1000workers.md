# Table 4: Scalability Extension Experiments (Up to 1,000 Workers & 2,500 Tasks)

| Problem Tier | Seed / Mode | Workers | Tasks | Algorithm | Status | Active Shifts | Coverage % | Runtime (s) | Tractability |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| Small | 101 | 25 | 60 | Exact MILP | OPTIMAL | 9 | 100.0% | 7.6952 | Tractable (<10s) |
| Small | aggregate_10_seeds | 25 | 60 | Greedy Allocator | PARTIAL | 14.5 | 99.8% | 0.0010 | Tractable (<10s) |
| Small | aggregate_10_seeds | 25 | 60 | ALNS Metaheuristic | PARTIAL | 12.7 | 99.8% | 0.0314 | Tractable (<10s) |
| Medium | 101 | 100 | 250 | Exact MILP | FEASIBLE | 81 | 89.6% | 16.5106 | Bounded Incumbent |
| Medium | aggregate_10_seeds | 100 | 250 | Greedy Allocator | FEASIBLE | 46.9 | 100.0% | 0.0114 | Tractable (<10s) |
| Medium | aggregate_10_seeds | 100 | 250 | ALNS Metaheuristic | FEASIBLE | 39.8 | 100.0% | 0.7435 | Tractable (<10s) |
| Large | 101 | 500 | 1200 | Exact MILP | NOT_RUN_RESOURCE_LIMIT | 0 | 0.0% | 0.0000 | Safety Resource Boundary |
| Large | aggregate_10_seeds | 500 | 1200 | Greedy Allocator | FEASIBLE | 211.7 | 100.0% | 0.2771 | Tractable (<10s) |
| Large | aggregate_10_seeds | 500 | 1200 | ALNS Metaheuristic | FEASIBLE | 181.4 | 100.0% | 9.9692 | Tractable (<10s) |
| Very-Large | 101 | 1000 | 2500 | Exact MILP | NOT_RUN_RESOURCE_LIMIT | 0 | 0.0% | 0.0000 | Safety Resource Boundary |
| Very-Large | aggregate_10_seeds | 1000 | 2500 | Greedy Allocator | FEASIBLE | 451.1 | 100.0% | 1.3377 | Tractable (<10s) |
| Very-Large | aggregate_10_seeds | 1000 | 2500 | ALNS Metaheuristic | FEASIBLE | 417.3 | 100.0% | 10.0050 | Bounded Incumbent |
