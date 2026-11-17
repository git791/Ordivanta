# Ordivanta Final Research Reproduction Guide

To independently reproduce all computational benchmarks, validation suites, and publication artifacts:

### 1. Execute Authentic Solver Runs (Direct C++ HiGHS Redirection)
```powershell
# Solves Small, Medium, Large (500w), Very-Large (1,000w), MATSP (150w), and Recovery MILP
backend\.venv\Scripts\python.exe backend\scripts\run_authentic_solver_experiments.py
```

### 2. Capture Live Web Application Screenshots
```powershell
# Starts backend & frontend and captures full-resolution screenshots via headless Chrome
backend\.venv\Scripts\python.exe backend\scripts\capture_live_screenshots.py
```

### 3. Generate Final Research Evidence Package & 10 Publication Figures
```powershell
# Rebuilds figures, tables, scenarios, and verifies authentic logs
backend\.venv\Scripts\python.exe backend\scripts\generate_final_research_package.py
```

### 4. Run Backend Verification Tests
```powershell
# Run unit and domain validator tests
backend\.venv\Scripts\pytest.exe backend\tests -q --ignore=backend/tests/test_api_routes.py
```

### 5. Verify Frontend TypeScript Compilation
```powershell
# Type check Next.js application
pnpm --prefix frontend exec tsc --noEmit
```
