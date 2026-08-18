#!/usr/bin/env python3
"""
HealthPulse — Automated JSON REST API Regression Test Runner
Exercises all REST API endpoints over HTTP/HTTPS and generates a structured regression report.
"""

import sys
import time
import json
import argparse
import urllib.request
import urllib.error
from typing import Dict, Any, Tuple

# Terminal color formatting
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
BOLD = "\033[1m"
RESET = "\033[0m"

class APIRegressionRunner:
    def __init__(self, base_url: str = "http://127.0.0.1:5000"):
        self.base_url = base_url.rstrip("/")
        self.token = None
        self.test_username = f"regression_bot_{int(time.time())}"
        self.test_password = "RegressionSecurePass123!"
        self.results = []

    def wait_for_server(self, timeout_sec: int = 10) -> bool:
        """Poll server /api/health until ready or timeout expires."""
        start = time.time()
        print(f"Waiting for backend server at {self.base_url} to become ready...", end="", flush=True)
        while time.time() - start < timeout_sec:
            try:
                req = urllib.request.Request(f"{self.base_url}/api/health", headers={"Accept": "application/json"})
                with urllib.request.urlopen(req, timeout=1) as resp:
                    if resp.status == 200:
                        print(" [Ready]\n")
                        return True
            except Exception:
                time.sleep(0.5)
                print(".", end="", flush=True)
        print(" [Timeout]\n")
        return False

    def log_result(self, name: str, success: bool, status_code: int, duration_ms: float, details: str = ""):
        self.results.append({
            "name": name,
            "success": success,
            "status_code": status_code,
            "duration_ms": round(duration_ms, 2),
            "details": details
        })
        icon = f"{GREEN}✔ PASS{RESET}" if success else f"{RED}✘ FAIL{RESET}"
        timing = f"({duration_ms:.1f}ms)"
        print(f" {icon} {BOLD}{name:<40}{RESET} [{status_code}] {timing} {details}")

    def _request(self, method: str, path: str, body: Dict[str, Any] = None, auth: bool = True) -> Tuple[int, Dict[str, Any], float]:
        url = f"{self.base_url}{path}"
        headers = {"Content-Type": "application/json", "Accept": "application/json"}
        if auth and self.token:
            headers["Authorization"] = f"Bearer {self.token}"

        data = json.dumps(body).encode("utf-8") if body is not None else None
        req = urllib.request.Request(url, data=data, headers=headers, method=method)

        start = time.time()
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                duration_ms = (time.time() - start) * 1000
                res_body = json.loads(resp.read().decode("utf-8"))
                return resp.status, res_body, duration_ms
        except urllib.error.HTTPError as e:
            duration_ms = (time.time() - start) * 1000
            try:
                err_body = json.loads(e.read().decode("utf-8"))
            except Exception:
                err_body = {"error": str(e)}
            return e.code, err_body, duration_ms
        except Exception as e:
            duration_ms = (time.time() - start) * 1000
            return 0, {"error": str(e)}, duration_ms

    def run_all(self) -> bool:
        print(f"\n{CYAN}{BOLD}=================================================================={RESET}")
        print(f"{CYAN}{BOLD}  HealthPulse REST API Regression Suite — Running against {self.base_url}{RESET}")
        print(f"{CYAN}{BOLD}=================================================================={RESET}\n")

        if not self.wait_for_server(timeout_sec=12):
            print(f"{RED}Error: Backend server did not respond at {self.base_url}.{RESET}")
            return False

        # 1. Health check
        status, data, ms = self._request("GET", "/api/health", auth=False)
        self.log_result("GET /api/health (Server Status)", status == 200 and data.get("status") == "ok", status, ms)

        # 2. Register New User
        status, data, ms = self._request("POST", "/api/auth/register", {
            "username": self.test_username,
            "password": self.test_password
        }, auth=False)
        self.token = data.get("token")
        self.log_result("POST /api/auth/register (New User)", status == 201 and bool(self.token), status, ms)

        # 3. Duplicate User Registration Conflict
        status, data, ms = self._request("POST", "/api/auth/register", {
            "username": self.test_username,
            "password": self.test_password
        }, auth=False)
        self.log_result("POST /api/auth/register (409 Conflict check)", status == 409, status, ms)

        # 4. User Login
        status, data, ms = self._request("POST", "/api/auth/login", {
            "username": self.test_username,
            "password": self.test_password
        }, auth=False)
        self.token = data.get("token")
        self.log_result("POST /api/auth/login (JWT Generation)", status == 200 and bool(self.token), status, ms)

        # 5. Auth Profile
        status, data, ms = self._request("GET", "/api/auth/me")
        self.log_result("GET /api/auth/me (User Profile)", status == 200 and data.get("user", {}).get("username") == self.test_username, status, ms)

        # 6. WebAuthn Registration Options Challenge
        status, data, ms = self._request("POST", "/api/auth/webauthn/register/options")
        self.log_result("POST /api/auth/webauthn/register/options", status == 200 and "challenge" in data.get("options", {}), status, ms)

        # 7. Add Entry
        test_date = "2026-08-18"
        status, data, ms = self._request("POST", "/api/entries", {
            "date": test_date,
            "weight": 176.5,
            "steps": 11500,
            "notes": "Automated regression run"
        })
        entry_id = data.get("entry", {}).get("id")
        self.log_result("POST /api/entries (Upsert Entry)", status == 201 and data.get("entry", {}).get("weight") == 176.5, status, ms)

        # 8. Get Entries List
        status, data, ms = self._request("GET", "/api/entries")
        self.log_result("GET /api/entries (List History)", status == 200 and len(data.get("entries", [])) >= 1, status, ms)

        # 9. Update Entry
        if entry_id:
            status, data, ms = self._request("PUT", f"/api/entries/{entry_id}", {
                "date": test_date,
                "weight": 175.8,
                "steps": 12000,
                "notes": "Updated via regression runner"
            })
            self.log_result(f"PUT /api/entries/{entry_id} (Update Entry)", status == 200 and data.get("entry", {}).get("weight") == 175.8, status, ms)

        # 10. Goals & Fernet Encryption Check
        status, data, ms = self._request("POST", "/api/goals", {
            "daily_steps_goal": 13000,
            "target_weight": 162.0,
            "starting_weight": 185.0,
            "weight_unit": "lbs",
            "gemini_api_key": "AIzaSyRegressionRunnerSampleKey"
        })
        self.log_result("POST /api/goals (Settings & Encryption)", status == 200 and data.get("goals", {}).get("has_gemini_api_key") is True, status, ms)

        # 11. Get Stats Calculations
        status, data, ms = self._request("GET", "/api/stats")
        self.log_result("GET /api/stats (Calculated Metrics)", status == 200 and data.get("stats", {}).get("total_days_logged") >= 1, status, ms)

        # 12. Scale Upload Job Polling
        status, data, ms = self._request("GET", "/api/upload-scale-photo/status")
        self.log_result("GET /api/upload-scale-photo/status", status == 200 and "jobs" in data, status, ms)

        # 13. Delete Entry Cleanup
        if entry_id:
            status, data, ms = self._request("DELETE", f"/api/entries/{entry_id}")
            self.log_result(f"DELETE /api/entries/{entry_id} (Cleanup)", status == 200, status, ms)

        # Print Summary
        passed = sum(1 for r in self.results if r["success"])
        total = len(self.results)
        failed = total - passed

        print(f"\n{CYAN}------------------------------------------------------------------{RESET}")
        if failed == 0:
            print(f" {GREEN}{BOLD}🎉 ALL {total} API REGRESSION TESTS PASSED (100% SUCCESS){RESET}")
        else:
            print(f" {RED}{BOLD}❌ {failed} OF {total} TESTS FAILED{RESET}")
        print(f"{CYAN}------------------------------------------------------------------{RESET}\n")

        return failed == 0

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="HealthPulse REST API Regression Runner")
    parser.add_argument("--base-url", default="http://127.0.0.1:5000", help="Base URL of HealthPulse server")
    args = parser.parse_args()

    runner = APIRegressionRunner(base_url=args.base_url)
    success = runner.run_all()
    sys.exit(0 if success else 1)
