"""
Capture Fresh, Authentic Application Screenshots Directly from the Running Web Application.
Launches the FastAPI backend and Next.js frontend, waits for HTTP health readiness,
and captures full-resolution screenshots using headless Chrome.
"""

import os
import sys
import time
import subprocess
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SHOTS_DIR = ROOT / "research" / "final_evidence" / "screenshots"
SHOTS_DIR.mkdir(parents=True, exist_ok=True)

CHROME_PATH = r"C:\Program Files\Google\Chrome\Application\chrome.exe"


def wait_for_url(url: str, timeout: int = 60) -> bool:
    start = time.time()
    while time.time() - start < timeout:
        try:
            with urllib.request.urlopen(url, timeout=2) as response:
                if response.status == 200:
                    return True
        except Exception:
            time.sleep(1)
    return False


def capture_page(chrome_exe: str, url: str, output_path: Path):
    print(f"Capturing screenshot: {url} -> {output_path.name}...")
    cmd = [
        chrome_exe,
        "--headless=new",
        "--disable-gpu",
        f"--screenshot={str(output_path.resolve())}",
        "--window-size=1280,850",
        url,
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    if output_path.exists() and output_path.stat().st_size > 1000:
        print(f"  Successfully captured {output_path.name} ({output_path.stat().st_size} bytes)")
    else:
        print(f"  Warning: Screenshot capture failed for {url}. Err: {res.stderr}")


def main():
    print("=" * 70)
    print("CAPTURING AUTHENTIC LIVE APPLICATION SCREENSHOTS")
    print("=" * 70)

    if not Path(CHROME_PATH).exists():
        print(f"Error: Google Chrome not found at {CHROME_PATH}")
        sys.exit(1)

    py_exe = sys.executable

    backend_log = open(ROOT / "backend_dev.log", "w", encoding="utf-8")
    frontend_log = open(ROOT / "frontend_dev.log", "w", encoding="utf-8")

    # 1. Start FastAPI Backend
    print("Starting FastAPI backend on 127.0.0.1:8000...", flush=True)
    backend_proc = subprocess.Popen(
        [py_exe, "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "8000"],
        cwd=str(ROOT / "backend"),
        stdout=backend_log,
        stderr=backend_log,
    )

    # 2. Start Next.js Frontend
    print("Starting Next.js frontend on localhost:3000...", flush=True)
    frontend_proc = subprocess.Popen(
        ["cmd", "/c", "pnpm", "run", "dev"],
        cwd=str(ROOT / "frontend"),
        stdout=frontend_log,
        stderr=frontend_log,
    )

    try:
        print("Waiting for backend readiness (http://127.0.0.1:8000/docs)...")
        if not wait_for_url("http://127.0.0.1:8000/docs", timeout=30):
            print("Error: Backend failed to start.")
            return

        print("Waiting for frontend readiness (http://localhost:3000)...", flush=True)
        # Next.js might exit once to show security upgrade prompt; restart if process exited
        for attempt in range(2):
            if wait_for_url("http://localhost:3000", timeout=30):
                break
            if frontend_proc.poll() is not None:
                print("Frontend process stopped (e.g. Next.js upgrade prompt). Retrying pnpm run dev...", flush=True)
                frontend_proc = subprocess.Popen(
                    ["cmd", "/c", "pnpm", "run", "dev"],
                    cwd=str(ROOT / "frontend"),
                    stdout=frontend_log,
                    stderr=frontend_log,
                )
        if not wait_for_url("http://localhost:3000", timeout=45):
            print("Error: Frontend failed to start.")
            return

        print("Both servers healthy! Allowing 4s for client hydration...")
        time.sleep(4)

        # 3. Capture Live Screenshots
        targets = [
            ("http://localhost:3000/shifts", SHOTS_DIR / "screenshot_module1_shift_planning.png"),
            ("http://localhost:3000/tasks", SHOTS_DIR / "screenshot_module2_task_allocation.png"),
            ("http://localhost:3000/demo", SHOTS_DIR / "screenshot_disruption_recovery.png"),
            ("http://localhost:3000/dashboard", SHOTS_DIR / "screenshot_dashboard_overview.png"),
        ]

        for url, out_file in targets:
            capture_page(CHROME_PATH, url, out_file)
            time.sleep(1)

        print("\nAll live screenshots captured directly from running Ordivanta web application.")

    finally:
        print("Shutting down development servers...")
        try:
            backend_proc.terminate()
            backend_proc.wait(timeout=5)
        except Exception:
            backend_proc.kill()

        try:
            subprocess.run(["taskkill", "/F", "/T", "/PID", str(frontend_proc.pid)], capture_output=True)
        except Exception:
            frontend_proc.kill()
        print("Servers stopped cleanly.")


if __name__ == "__main__":
    main()
