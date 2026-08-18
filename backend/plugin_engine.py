"""
HealthPulse — Plugin & Metric Component Engine
Discovers, validates, and calculates statistics for manifest-driven metric components.
"""

import os
import json
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Any, Optional, Tuple

PLUGINS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "plugins"))

class PluginEngine:
    def __init__(self, plugins_dir: str = PLUGINS_DIR):
        self.plugins_dir = plugins_dir
        self._manifest_cache: Dict[str, Dict[str, Any]] = {}
        self.reload_plugins()

    def reload_plugins(self) -> Dict[str, Dict[str, Any]]:
        """Scan plugins directory and load all valid manifest.json files."""
        self._manifest_cache.clear()
        if not os.path.exists(self.plugins_dir):
            return self._manifest_cache

        for entry in os.listdir(self.plugins_dir):
            plugin_path = os.path.join(self.plugins_dir, entry)
            manifest_file = os.path.join(plugin_path, "manifest.json")
            if os.path.isdir(plugin_path) and os.path.isfile(manifest_file):
                try:
                    with open(manifest_file, "r", encoding="utf-8") as f:
                        manifest = json.load(f)
                    
                    is_valid, err = self.validate_manifest_structure(manifest)
                    if is_valid:
                        plugin_id = manifest["id"]
                        self._manifest_cache[plugin_id] = manifest
                    else:
                        print(f"[PluginEngine Warning]: Invalid manifest at {manifest_file}: {err}")
                except Exception as e:
                    print(f"[PluginEngine Error]: Failed loading {manifest_file}: {e}")

        return self._manifest_cache

    def validate_manifest_structure(self, manifest: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """Ensure manifest contains required metadata and field definitions."""
        required_keys = ["id", "name", "version", "category", "fields"]
        for k in required_keys:
            if k not in manifest:
                return False, f"Missing required root field: '{k}'"

        if not isinstance(manifest["fields"], list) or len(manifest["fields"]) == 0:
            return False, "'fields' must be a non-empty list"

        for field in manifest["fields"]:
            if not isinstance(field, dict) or "id" not in field or "label" not in field or "type" not in field:
                return False, f"Invalid field definition in fields: {field}"

        return True, None

    def get_plugin(self, plugin_id: str) -> Optional[Dict[str, Any]]:
        return self._manifest_cache.get(plugin_id)

    def get_all_plugins(self) -> List[Dict[str, Any]]:
        return list(self._manifest_cache.values())

    def validate_payload(self, plugin_id: str, payload: Dict[str, Any]) -> Tuple[bool, Optional[str], Dict[str, Any]]:
        """
        Validate incoming user payload against plugin manifest field requirements.
        Returns (is_valid, error_msg, cleaned_payload)
        """
        manifest = self.get_plugin(plugin_id)
        if not manifest:
            return False, f"Unknown metric component plugin: '{plugin_id}'", {}

        cleaned = {}
        for field in manifest["fields"]:
            fid = field["id"]
            ftype = field["type"]
            freq = field.get("required", False)
            flabel = field.get("label", fid)

            val = payload.get(fid)

            if freq and (val is None or val == ""):
                return False, f"Field '{flabel}' is required.", {}

            if val is not None and val != "":
                if ftype in ("number", "float"):
                    try:
                        val = float(val)
                        if "min" in field and val < field["min"]:
                            return False, f"Field '{flabel}' must be >= {field['min']}.", {}
                        if "max" in field and val > field["max"]:
                            return False, f"Field '{flabel}' must be <= {field['max']}.", {}
                    except (ValueError, TypeError):
                        return False, f"Field '{flabel}' must be a valid number.", {}

                elif ftype in ("integer", "int"):
                    try:
                        val = int(val)
                        if "min" in field and val < field["min"]:
                            return False, f"Field '{flabel}' must be >= {field['min']}.", {}
                        if "max" in field and val > field["max"]:
                            return False, f"Field '{flabel}' must be <= {field['max']}.", {}
                    except (ValueError, TypeError):
                        return False, f"Field '{flabel}' must be a valid integer.", {}

                elif ftype == "select":
                    options = field.get("options", [])
                    if options and val not in options and val != "Other":
                        # Allow custom write-in if options doesn't contain it
                        pass

                cleaned[fid] = val
            else:
                cleaned[fid] = None

        return True, None, cleaned

    def compute_stats(self, plugin_id: str, entries: List[Dict[str, Any]], user_goals: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Calculate dynamic stats and aggregations for any metric based on its manifest.
        """
        manifest = self.get_plugin(plugin_id)
        if not manifest:
            return {"total_entries": len(entries)}

        card_type = manifest.get("visualizations", {}).get("cardType", "metric_progress")

        if card_type == "log_summary" or manifest.get("category") == "equipment":
            return self._compute_log_summary_stats(manifest, entries)
        else:
            return self._compute_numeric_stats(manifest, entries, user_goals)

    def _compute_numeric_stats(self, manifest: Dict[str, Any], entries: List[Dict[str, Any]], user_goals: Dict[str, Any] = None) -> Dict[str, Any]:
        """Compute analytics for numeric metrics (Weight, Steps, etc.)"""
        primary_field = manifest["fields"][0]["id"]
        unit = manifest["fields"][0].get("unit", "")

        if not entries:
            return {
                "metric_id": manifest["id"],
                "name": manifest["name"],
                "total_entries": 0,
                "latest_value": None,
                "unit": unit,
                "avg_7d": 0,
                "avg_30d": 0,
                "best_value": 0,
                "total_sum": 0,
                "streak": 0
            }

        sorted_desc = sorted(entries, key=lambda x: x["date"], reverse=True)
        valid_entries = [e for e in sorted_desc if e.get("payload", {}).get(primary_field) is not None]

        latest_val = valid_entries[0]["payload"][primary_field] if valid_entries else None

        values = [float(e["payload"][primary_field]) for e in valid_entries]
        total_sum = sum(values)
        best_val = max(values) if values else 0

        # Date windows
        today = datetime.now()
        d7 = (today - timedelta(days=7)).strftime("%Y-%m-%d")
        d30 = (today - timedelta(days=30)).strftime("%Y-%m-%d")

        entries_7d = [float(e["payload"][primary_field]) for e in valid_entries if e["date"] >= d7]
        avg_7d = round(sum(entries_7d) / len(entries_7d), 1) if entries_7d else 0

        entries_30d = [float(e["payload"][primary_field]) for e in valid_entries if e["date"] >= d30]
        avg_30d = round(sum(entries_30d) / len(entries_30d), 1) if entries_30d else 0

        # Goal progress & Streak
        target_goal = (user_goals or {}).get(f"{manifest['id']}_target") or manifest.get("goals", {}).get("defaultTarget")
        streak = 0
        if target_goal is not None:
            for e in valid_entries:
                v = float(e["payload"][primary_field])
                if v >= float(target_goal):
                    streak += 1
                else:
                    break

        return {
            "metric_id": manifest["id"],
            "name": manifest["name"],
            "total_entries": len(valid_entries),
            "latest_value": latest_val,
            "unit": unit,
            "avg_7d": avg_7d,
            "avg_30d": avg_30d,
            "best_value": best_val,
            "total_sum": round(total_sum, 1),
            "streak": streak,
            "target_goal": target_goal
        }

    def _compute_log_summary_stats(self, manifest: Dict[str, Any], entries: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Compute equipment session analytics (Camera & Lens Gear Log)"""
        sorted_desc = sorted(entries, key=lambda x: x.get("payload", {}).get("timedate_of_use") or x["date"], reverse=True)
        total_sessions = len(entries)
        latest_session = sorted_desc[0]["payload"] if sorted_desc else None

        camera_counts = {}
        lens_counts = {}

        for e in entries:
            p = e.get("payload", {})
            cam = p.get("camera_body")
            lens = p.get("lens")
            if cam:
                camera_counts[cam] = camera_counts.get(cam, 0) + 1
            if lens:
                lens_counts[lens] = lens_counts.get(lens, 0) + 1

        top_camera = max(camera_counts.items(), key=lambda x: x[1])[0] if camera_counts else "None"
        top_lens = max(lens_counts.items(), key=lambda x: x[1])[0] if lens_counts else "None"

        return {
            "metric_id": manifest["id"],
            "name": manifest["name"],
            "category": "equipment",
            "total_sessions": total_sessions,
            "latest_session": latest_session,
            "top_camera": top_camera,
            "top_lens": top_lens,
            "camera_counts": camera_counts,
            "lens_counts": lens_counts,
            "recent_sessions": [e["payload"] for e in sorted_desc[:5]]
        }

# Global Plugin Engine Singleton
plugin_engine = PluginEngine()
