#!/usr/bin/env bash
# deploy.sh — Pull latest ElixirSauceCo branch and restart Odoo
# Run as the odoo system user, or via sudo by a deploy user.
#
# Usage: bash deploy.sh
# Triggered automatically by GitHub Actions on push to ElixirSauceCo.

set -euo pipefail

ODOO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ODOO_CONF=""
VENV="${ODOO_DIR}/.venv"
BRANCH="ElixirSauceCo"
SERVICE="odoo"

if [ -r "/etc/odoo.conf" ]; then
    ODOO_CONF="/etc/odoo.conf"
elif [ -r "${ODOO_DIR}/odoo.conf" ]; then
    ODOO_CONF="${ODOO_DIR}/odoo.conf"
else
    echo "ERROR: No readable Odoo config found at /etc/odoo.conf or ${ODOO_DIR}/odoo.conf" >&2
    exit 2
fi

echo "==> Deploying branch: ${BRANCH}"

# Git 2.35+ blocks operations in repos with differing ownership unless
# explicitly trusted. In CI/remote deploy contexts this is expected.
git_safe() {
    git -c safe.directory="${ODOO_DIR}" "$@"
}

# Pull latest code
cd "${ODOO_DIR}"
# Fast path: fetch only the target branch tip (no tags/full history walk).
git_safe fetch --no-tags --prune --depth=1 origin "${BRANCH}"
git_safe checkout "${BRANCH}"
git_safe reset --hard FETCH_HEAD

# Update Python dependencies if requirements changed
if git_safe diff --name-only HEAD@{1} HEAD 2>/dev/null | grep -q "requirements.txt"; then
    echo "==> requirements.txt changed — updating packages"
    "${VENV}/bin/pip" install -q -r "${ODOO_DIR}/requirements.txt"
fi

# Apply any pending module updates (add -u <module> if you want selective updates)
echo "==> Updating Odoo modules"
"${VENV}/bin/python" "${ODOO_DIR}/odoo-bin" \
    -c "${ODOO_CONF}" \
    -u google_address_autocomplete \
    --stop-after-init \
    --no-http

# Restart the service
echo "==> Restarting ${SERVICE} service"
sudo systemctl restart "${SERVICE}"

echo "==> Deploy complete"
