#!/bin/bash
# Development CLI runner - uruchamia CLI bez instalacji globalnej
# Wymaga zainstalowanych dependencies (poetry install)

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export PYTHONPATH="${SCRIPT_DIR}/src:${PYTHONPATH}"

# Sprawdź czy dependencies są zainstalowane
if ! python -c "import pydantic" 2>/dev/null; then
    echo "❌ Błąd: Brakujące dependencies"
    echo "Uruchom: poetry install"
    exit 1
fi

# Uruchom CLI
python -m gitlab_terraform_importer.interfaces.cli.commands "$@"
