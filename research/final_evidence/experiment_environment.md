# Experimental Environment & Benchmarking Specifications

- **Operating System:** Windows 11 Enterprise (Build 26100)
- **Host Architecture:** x86_64 Multi-Core Processor
- **Python Runtime:** Python 3.13 / 3.11 Virtual Environment (`backend/.venv`)
- **Optimization Solvers:** 
  - **HiGHS 1.9.0** via PuLP 4.2.0 (Branch-and-Cut, Simplex, Interior Point)
  - **ALNS Metaheuristic:** Adaptive Large Neighbourhood Search (Ordivanta native)
  - **Greedy Heuristic:** Earliest-Start-Time Interval Packing Baseline
- **Web Platform:** Next.js 16.4.2, React 19.0.0, TypeScript 5.x, Tailwind CSS 4.0
- **Memory Profiling:**
  - **Python Heap Allocations:** `tracemalloc`
  - **Process Working Set (RSS):** `psutil.Process().memory_info().rss`
- **Solver Time Limits:**
  - Small / Medium (25w, 100w): 15 seconds
  - Large (500w): 30 seconds
  - Very-Large (1,000w): 60 seconds
  - Note: Wall-clock runtime records total execution (model construction + solver execution).
