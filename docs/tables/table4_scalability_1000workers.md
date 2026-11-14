# Table 4: Scalability Extension Experiments (Up to 1,000 Workers & 2,500 Tasks)

| Problem Tier | Workers | Tasks | Algorithm | Status | Active Shifts | Coverage % | Runtime (s) | Tractability |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| Small | 25 | 60 | Greedy Allocator | FEASIBLE | 15 | 100.0% | 0.0009 | Tractable |
| Small | 25 | 60 | ALNS Metaheuristic | FEASIBLE | 12 | 100.0% | 0.0226 | Tractable |
| Small | 25 | 60 | Exact MILP | FEASIBLE | 10 | 100.0% | 15.0545 | Bounded Incumbent |
| Medium | 100 | 250 | Greedy Allocator | FEASIBLE | 45 | 100.0% | 0.0170 | Tractable |
| Medium | 100 | 250 | ALNS Metaheuristic | FEASIBLE | 41 | 100.0% | 0.4099 | Tractable |
| Medium | 100 | 250 | Exact MILP | FEASIBLE | 85 | 90.0% | 15.8582 | Bounded Incumbent |
| Large | 500 | 1200 | Greedy Allocator | FEASIBLE | 209 | 100.0% | 0.2601 | Tractable |
| Large | 500 | 1200 | ALNS Metaheuristic | FEASIBLE | 184 | 100.0% | 4.0988 | Tractable |
| Large | 500 | 1200 | Exact MILP | TIME_LIMIT_EXCEEDED | 0 | 0.0% | 30.0000 | Intractable Cutoff |
| Very-Large | 1000 | 2500 | Greedy Allocator | FEASIBLE | 441 | 100.0% | 1.2949 | Tractable |
| Very-Large | 1000 | 2500 | ALNS Metaheuristic | FEASIBLE | 381 | 100.0% | 25.0047 | Bounded Incumbent |
| Very-Large | 1000 | 2500 | Exact MILP | TIME_LIMIT_EXCEEDED | 0 | 0.0% | 30.0000 | Intractable Cutoff |
