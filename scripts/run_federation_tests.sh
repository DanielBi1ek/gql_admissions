#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

GQL_URL="${GQL_URL:-http://localhost:33001/api/gql}"
OAUTH_URL="${OAUTH_URL:-http://localhost:33001/oauth/login3}"
PYTEST_BIN="${PYTEST_BIN:-$ROOT_DIR/.venv/bin/pytest}"

MODE="${1:-integration}"

die() { echo "error: $*" >&2; exit 2; }

if [[ ! -x "$PYTEST_BIN" ]]; then
  die "pytest not found/executable: $PYTEST_BIN"
fi

export TEST_TARGET=federation

# Hardcoded accounts (password == email).
# Intentionally override any existing env, so runs are deterministic.
TEST_USERNAME="Estera.Luckova@world.com"
TEST_PASSWORD="$TEST_USERNAME"

TEST_ADMIN_USERNAME="Valentin.Krenek@world.com"
TEST_ADMIN_PASSWORD="$TEST_ADMIN_USERNAME"

TEST_OTHER_USERNAME="Oliver.Hortik@world.com"
TEST_OTHER_PASSWORD="$TEST_OTHER_USERNAME"

export TEST_USERNAME TEST_PASSWORD
export TEST_ADMIN_USERNAME TEST_ADMIN_PASSWORD
export TEST_OTHER_USERNAME TEST_OTHER_PASSWORD

export GQL_URL
export OAUTH_URL

echo "GQL_URL=$GQL_URL"
echo "OAUTH_URL=$OAUTH_URL"
echo "TEST_USERNAME=$TEST_USERNAME"
echo "TEST_ADMIN_USERNAME=$TEST_ADMIN_USERNAME"
echo "TEST_OTHER_USERNAME=$TEST_OTHER_USERNAME"

case "$MODE" in
  integration)
    exec "$PYTEST_BIN" tests/test_integration_queries.py -m integration -v
    ;;
  all)
    # This will attempt to run the whole suite with schema.execute patched to call federation.
    # Many tests were originally unit tests and may not be compatible with live data.
    exec "$PYTEST_BIN" tests -v
    ;;
  *)
    die "usage: $0 [integration|all]"
    ;;
esac
