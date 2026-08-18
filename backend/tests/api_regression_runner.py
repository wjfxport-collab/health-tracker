#!/usr/bin/env python3
"""
HealthPulse — Automated JSON REST API Regression Test Runner
Exercises all REST API endpoints over HTTP/HTTPS including the Plugin DevKit & Camera Log component.
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
        print(f" {icon} {BOLD}{name:<45}{RESET} [{status_code}] {timing} {details}")

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

        # 2. Plugin Discovery
        status, data, ms = self._request("GET", "/api/plugins", auth=False)
        plugin_ids = [p["id"] for p in data.get("plugins", [])]
        self.log_result("GET /api/plugins (DevKit Manifest Discovery)", status == 200 and "camera_log" in plugin_ids and "weight" in plugin_ids, status, ms)

        # 3. Register New User
        status, data, ms = self._request("POST", "/api/auth/register", {
            "username": self.test_username,
            "password": self.test_password
        }, auth=False)
        self.token = data.get("token")
        self.log_result("POST /api/auth/register (New User)", status == 201 and bool(self.token), status, ms)

        # 4. Duplicate User Registration Conflict
        status, data, ms = self._request("POST", "/api/auth/register", {
            "username": self.test_username,
            "password": self.test_password
        }, auth=False)
        self.log_result("POST /api/auth/register (409 Conflict check)", status == 409, status, ms)

        # 5. User Login
        status, data, ms = self._request("POST", "/api/auth/login", {
            "username": self.test_username,
            "password": self.test_password
        }, auth=False)
        self.token = data.get("token")
        self.log_result("POST /api/auth/login (JWT Generation)", status == 200 and bool(self.token), status, ms)

        # 6. Auth Profile
        status, data, ms = self._request("GET", "/api/auth/me")
        self.log_result("GET /api/auth/me (User Profile)", status == 200 and data.get("user", {}).get("username") == self.test_username, status, ms)

        # 7. WebAuthn Registration Options Challenge
        status, data, ms = self._request("POST", "/api/auth/webauthn/register/options")
        self.log_result("POST /api/auth/webauthn/register/options", status == 200 and "challenge" in data.get("options", {}), status, ms)

        # 8. Dynamic Camera & Lens Session Logging (DevKit Addin)
        status, data, ms = self._request("POST", "/api/metrics/camera_log/entries", {
            "date": "2026-08-18",
            "payload": {
                "camera_body": "Sony A7 IV",
                "lens": "FE 24-70mm f/2.8 GM II",
                "timedate_of_use": "2026-08-18T15:30",
                "focal_length": 50,
                "aperture": "f/2.8",
                "iso": 400,
                "shutter_speed": "1/500s",
                "comment": "Golden hour outdoor shoot"
            },
            "notes": "Outdoor location"
        })
        camera_entry_id = data.get("entry", {}).get("id")
        self.log_result("POST /api/metrics/camera_log/entries (Gear Addin)", status == 201 and data.get("entry", {}).get("payload", {}).get("camera_body") == "Sony A7 IV", status, ms)

        # 9. Dynamic Camera Stats
        status, data, ms = self._request("GET", "/api/metrics/camera_log/stats")
        self.log_result("GET /api/metrics/camera_log/stats (Equipment Stats)", status == 200 and data.get("stats", {}).get("top_camera") == "Sony A7 IV", status, ms)

        # 10. Legacy & Dynamic Weight/Steps Entry
        test_date = "2026-08-18"
        status, data, ms = self._request("POST", "/api/entries", {
            "date": test_date,
            "weight": 176.5,
            "steps": 11500,
            "notes": "Automated regression run"
        })
        entry_id = data.get("entry", {}).get("id")
        self.log_result("POST /api/entries (Upsert Weight/Steps)", status == 201 and data.get("entry", {}).get("weight") == 176.5, status, ms)

        # 11. Unified Metrics Summary
        status, data, ms = self._request("GET", "/api/metrics/summary")
        summary = data.get("summary", {})
        self.log_result("GET /api/metrics/summary (Multi-Plugin Summary)", status == 200 and "camera_log" in summary and "weight" in summary, status, ms)

        # 12. Goals & Fernet Encryption Check
        status, data, ms = self._request("POST", "/api/goals", {
            "daily_steps_goal": 13000,
            "target_weight": 162.0,
            "starting_weight": 185.0,
            "weight_unit": "lbs",
            "gemini_api_key": "AIzaSyRegressionRunnerSampleKey"
        })
        self.log_result("POST /api/goals (Settings & Fernet Encryption)", status == 200 and data.get("goals", {}).get("has_gemini_api_key") is True, status, ms)

        # 13. Scale Upload Job Polling
        status, data, ms = self._request("GET", "/api/upload-scale-photo/status")
        self.log_result("GET /api/upload-scale-photo/status", status == 200 and "jobs" in data, status, ms)

        # 14. Delete Entry Cleanup
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
