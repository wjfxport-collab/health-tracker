#!/usr/bin/env bash
# ==============================================================================
# HealthPulse Component DevKit CLI
# Scaffolds, validates, lists, and packages metric & equipment tracking addins.
# ==============================================================================

set -e

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PLUGINS_DIR="$PROJECT_DIR/plugins"

# Colors
GREEN="\033[92m"
RED="\033[91m"
CYAN="\033[96m"
YELLOW="\033[93m"
BOLD="\033[1m"
RESET="\033[0m"

usage() {
  echo -e "${CYAN}${BOLD}HealthPulse Component DevKit CLI${RESET}"
  echo -e "Usage: ./devkit.sh [command] [options]\n"
  echo "Commands:"
  echo "  list                     List all currently installed plugin components"
  echo "  create [options]         Scaffold a new component package"
  echo "  validate <path>          Validate a plugin manifest against specification"
  echo "  install <path>           Install a component package into plugins/"
  echo ""
  echo "Options for 'create':"
  echo "  --id <id>                Unique component identifier (e.g. blood_pressure)"
  echo "  --name <name>            Display name (e.g. 'Blood Pressure')"
  echo "  --category <category>    Category (e.g. health, activity, equipment)"
  echo "  --icon <icon>            Lucide React icon name (e.g. HeartPulse, Droplets)"
  echo "  --color <hex>            Theme color (e.g. '#ef4444')"
  exit 1
}

cmd_list() {
  echo -e "\n${CYAN}${BOLD}Installed HealthPulse Component Addins:${RESET}\n"
  printf " %-16s %-28s %-16s %-12s\n" "ID" "NAME" "CATEGORY" "VERSION"
  printf " %-16s %-28s %-16s %-12s\n" "----------------" "----------------------------" "----------------" "------------"

  for manifest in "$PLUGINS_DIR"/*/manifest.json; do
    if [ -f "$manifest" ]; then
      id=$(grep -o '"id": *"[^"]*"' "$manifest" | head -1 | cut -d'"' -f4)
      name=$(grep -o '"name": *"[^"]*"' "$manifest" | head -1 | cut -d'"' -f4)
      category=$(grep -o '"category": *"[^"]*"' "$manifest" | head -1 | cut -d'"' -f4)
      version=$(grep -o '"version": *"[^"]*"' "$manifest" | head -1 | cut -d'"' -f4)
      printf " ${GREEN}%-16s${RESET} %-28s %-16s %-12s\n" "$id" "$name" "$category" "$version"
    fi
  done
  echo ""
}

cmd_validate() {
  target="$1"
  if [ -z "$target" ]; then
    echo -e "${RED}Error: Please specify the plugin folder or manifest.json to validate.${RESET}"
    exit 1
  fi

  if [ -d "$target" ]; then
    manifest="$target/manifest.json"
  else
    manifest="$target"
  fi

  if [ ! -f "$manifest" ]; then
    echo -e "${RED}Error: manifest.json not found at $manifest${RESET}"
    exit 1
  fi

  echo -e "${CYAN}Validating $manifest...${RESET}"

  # Validate JSON syntax with python
  python3 -c "
import json, sys
try:
    with open('$manifest', 'r') as f:
        data = json.load(f)
    required = ['id', 'name', 'version', 'category', 'fields']
    for req in required:
        if req not in data:
            print(f'Missing required root key: {req}', file=sys.stderr)
            sys.exit(1)
    if not isinstance(data['fields'], list) or len(data['fields']) == 0:
        print('fields must be a non-empty array', file=sys.stderr)
        sys.exit(1)
    for field in data['fields']:
        if 'id' not in field or 'label' not in field or 'type' not in field:
            print(f'Invalid field definition: {field}', file=sys.stderr)
            sys.exit(1)
    print('Manifest is 100% valid and compliant!')
except Exception as e:
    print(f'Validation failed: {e}', file=sys.stderr)
    sys.exit(1)
"
  echo -e "${GREEN}✔ Plugin manifest validation passed!${RESET}\n"
}

cmd_create() {
  ID=""
  NAME=""
  CATEGORY="health"
  ICON="Activity"
  COLOR="#059669"

  while [[ "$#" -gt 0 ]]; do
    case $1 in
      --id) ID="$2"; shift ;;
      --name) NAME="$2"; shift ;;
      --category) CATEGORY="$2"; shift ;;
      --icon) ICON="$2"; shift ;;
      --color) COLOR="$2"; shift ;;
      *) echo "Unknown parameter: $1"; exit 1 ;;
    esac
    shift
  done

  if [ -z "$ID" ] || [ -z "$NAME" ]; then
    echo -e "${RED}Error: --id and --name are required.${RESET}"
    usage
  fi

  TARGET_DIR="$PLUGINS_DIR/$ID"
  if [ -d "$TARGET_DIR" ]; then
    echo -e "${RED}Error: Component '$ID' already exists at $TARGET_DIR${RESET}"
    exit 1
  fi

  mkdir -p "$TARGET_DIR"

  cat <<EOF > "$TARGET_DIR/manifest.json"
{
  "id": "$ID",
  "name": "$NAME",
  "version": "1.0.0",
  "category": "$CATEGORY",
  "icon": "$ICON",
  "color": "$COLOR",
  "description": "Custom $NAME tracking addin component",
  "fields": [
    {
      "id": "value",
      "label": "$NAME Value",
      "type": "number",
      "required": true,
      "placeholder": "Enter value"
    },
    {
      "id": "notes",
      "label": "Session Notes",
      "type": "textarea",
      "required": false,
      "placeholder": "Optional notes or details..."
    }
  ],
  "visualizations": {
    "cardType": "metric_progress",
    "aggregations": ["latest", "7d_avg", "total_count"]
  }
}
EOF

  echo -e "${GREEN}✔ Scaffolding complete for component '$NAME' at:${RESET}"
  echo -e "  $TARGET_DIR/manifest.json"
  echo -e "\nRun ${CYAN}./devkit.sh validate $TARGET_DIR${RESET} to test the manifest."
}

cmd_install() {
  SRC="$1"
  if [ -z "$SRC" ] || [ ! -d "$SRC" ]; then
    echo -e "${RED}Error: Please specify a valid component folder to install.${RESET}"
    exit 1
  fi

  cmd_validate "$SRC"
  PLUGIN_NAME=$(basename "$SRC")
  DEST="$PLUGINS_DIR/$PLUGIN_NAME"

  if [ "$SRC" != "$DEST" ]; then
    cp -r "$SRC" "$DEST"
    echo -e "${GREEN}✔ Installed '$PLUGIN_NAME' into $DEST${RESET}"
  else
    echo -e "${GREEN}✔ Component already present in plugins directory.${RESET}"
  fi
}

case "$1" in
  list) cmd_list ;;
  validate) shift; cmd_validate "$@" ;;
  create) shift; cmd_create "$@" ;;
  install) shift; cmd_install "$@" ;;
  *) usage ;;
esac
