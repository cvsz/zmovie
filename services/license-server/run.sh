#!/usr/bin/env bash
# Start the ZeaZ License Server with its restricted environment file.
# No secrets in this file. Env file: /etc/zmovie-cinema/license-admin.env (0600).
set -Eeuo pipefail
cd "$(dirname "$0")"
set -a
# shellcheck disable=SC1091
source /etc/zmovie-cinema/license-admin.env
set +a
exec /usr/bin/python3 server.py
