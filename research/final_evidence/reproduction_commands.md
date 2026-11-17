# Ordivanta Final Research Reproduction Guide

To independently reproduce all computational benchmarks, validation suites, and publication artifacts:

### 1. Execute All Academic Benchmarks
```powershell
# Run full benchmark pipeline (Module 1, Module 2, Scalability, and Recovery)
backend\.venv\Scripts\python.exe backend\scripts\run_academic_benchmarks.py --suite all
```

### 2. Generate Evidence Package & 10 Publication Figures
```powershell
# Rebuild figures, tables, scenarios, and solver logs
backend\.venv\Scripts\python.exe backend\scripts\generate_final_research_package.py
```

### 3. Run Backend Verification Tests
```powershell
# Run 115 unit and methodology audit tests
backend\.venv\Scripts\pytest.exe backend\tests -q --ignore=backend/tests/test_api_routes.py
```

### 4. Verify Frontend TypeScript Compilation
```powershell
# Type check the Next.js application
pnpm --prefix frontend exec tsc --noEmit
```
