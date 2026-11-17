# Table 4: Scalability Extension Experiments (Up to 1,000 Workers & 2,500 Tasks)

| Problem Tier | Seed / Mode | Workers | Tasks | Algorithm | Status | Active Shifts | Coverage % | Runtime (s) | Tractability |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| Small | 101 | 25 | 60 | Exact MILP | OPTIMAL | 9 | 100.0% | 6.0520 | Exact Optimal (Proven) |
| Small | aggregate_10_seeds | 25 | 60 | Greedy Allocator | PARTIAL | 14.5 | 99.8% | 0.0033 | Tractable (<10s) |
| Small | aggregate_10_seeds | 25 | 60 | ALNS Metaheuristic | PARTIAL | 12.7 | 99.8% | 0.1366 | Tractable (<10s) |
| Medium | 101 | 100 | 250 | Exact MILP | FEASIBLE | 43 | 100.0% | 15.7700 | Feasible Incumbent (Bounded) |
| Medium | aggregate_10_seeds | 100 | 250 | Greedy Allocator | FEASIBLE | 46.9 | 100.0% | 0.0330 | Feasible Incumbent (Bounded) |
| Medium | aggregate_10_seeds | 100 | 250 | ALNS Metaheuristic | FEASIBLE | 39.8 | 100.0% | 2.5247 | Feasible Incumbent (Bounded) |
| Large | 101 | 500 | 1200 | Exact MILP | FEASIBLE | 207 | 100.0% | 59.8227 | Feasible Incumbent (Bounded) |
| Large | aggregate_10_seeds | 500 | 1200 | Greedy Allocator | FEASIBLE | 211.7 | 100.0% | 1.0619 | Feasible Incumbent (Bounded) |
| Large | aggregate_10_seeds | 500 | 1200 | ALNS Metaheuristic | FEASIBLE | 193.3 | 100.0% | 10.0053 | Feasible Incumbent (Bounded) |
| Very-Large | 101 | 1000 | 2500 | Exact MILP | FEASIBLE | 449 | 100.0% | 324.1503 | Feasible Incumbent (Bounded) |
| Very-Large | aggregate_10_seeds | 1000 | 2500 | Greedy Allocator | FEASIBLE | 451.1 | 100.0% | 4.4018 | Feasible Incumbent (Bounded) |
| Very-Large | aggregate_10_seeds | 1000 | 2500 | ALNS Metaheuristic | FEASIBLE | 442.3 | 100.0% | 10.0185 | Feasible Incumbent (Bounded) |
