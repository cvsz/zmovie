#!/usr/bin/env bash
set -Eeuo pipefail

INSTALL_DIR="${ZMOVIE_INSTALL_DIR:-/opt/zmovie}"
DATA_DIR="${ZMOVIE_DATA_DIR:-/var/lib/zmovie}"
CONFIG_DIR="${ZMOVIE_CONFIG_DIR:-/etc/zmovie}"
ENV_FILE="${ZMOVIE_ENV:-${CONFIG_DIR}/zmovie.env}"
SERVICE_USER="${ZMOVIE_SERVICE_USER:-zmovie}"
BACKUP_DIR="${ZMOVIE_BACKUP_DIR:-/var/backups/zmovie}"
PYTHON_BIN="${INSTALL_DIR}/.venv/bin/python"

[[ ${EUID} -eq 0 ]] || { echo "install-resilient-runtime.sh requires root" >&2; exit 2; }
[[ -x "$PYTHON_BIN" ]] || { echo "zMovie Python runtime missing: $PYTHON_BIN" >&2; exit 2; }
[[ -f "$ENV_FILE" ]] || { echo "zMovie environment missing: $ENV_FILE" >&2; exit 2; }

install -d -o "$SERVICE_USER" -g "$SERVICE_USER" -m 0750 \
  "$DATA_DIR" "$DATA_DIR/models" "$DATA_DIR/evidence" "$BACKUP_DIR"

supplementary=""
for group in render video; do
  if getent group "$group" >/dev/null 2>&1; then
    usermod -a -G "$group" "$SERVICE_USER"
    supplementary+=" $group"
  fi
done
supplementary="${supplementary# }"

cat >/etc/systemd/system/zmovie-worker.service <<EOF
[Unit]
Description=zMovie Durable Production Worker
After=network-online.target zmovie.service
Wants=network-online.target

[Service]
Type=simple
User=${SERVICE_USER}
Group=${SERVICE_USER}
${supplementary:+SupplementaryGroups=${supplementary}}
WorkingDirectory=${INSTALL_DIR}
EnvironmentFile=${ENV_FILE}
Environment=ZMOVIE_DATA_DIR=${DATA_DIR}
Environment=ZMOVIE_BACKUP_DIR=${BACKUP_DIR}
Environment=ZMOVIE_EVIDENCE_ROOT=${DATA_DIR}/evidence
ExecStart=${PYTHON_BIN} -m zmovie_platform.worker
Restart=always
RestartSec=5
TimeoutStopSec=90
UMask=0027
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ProtectKernelTunables=true
ProtectKernelModules=true
ProtectKernelLogs=true
ProtectControlGroups=true
RestrictSUIDSGID=true
LockPersonality=true
RestrictRealtime=true
CapabilityBoundingSet=
AmbientCapabilities=
ReadWritePaths=${DATA_DIR} ${BACKUP_DIR}

[Install]
WantedBy=multi-user.target
EOF

cat >/etc/systemd/system/zmovie-watchdog.service <<EOF
[Unit]
Description=zMovie Health Watchdog
After=zmovie.service zmovie-worker.service

[Service]
Type=oneshot
User=${SERVICE_USER}
Group=${SERVICE_USER}
WorkingDirectory=${INSTALL_DIR}
EnvironmentFile=${ENV_FILE}
Environment=ZMOVIE_DATA_DIR=${DATA_DIR}
ExecStart=${PYTHON_BIN} -m zmovie_platform.runtime_ops watchdog-run
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=${DATA_DIR}
EOF

cat >/etc/systemd/system/zmovie-watchdog.timer <<'EOF'
[Unit]
Description=Run zMovie watchdog periodically

[Timer]
OnBootSec=5min
OnUnitActiveSec=5min
AccuracySec=30s
Persistent=true

[Install]
WantedBy=timers.target
EOF

cat >/etc/systemd/system/zmovie-backup.service <<EOF
[Unit]
Description=zMovie Verified SQLite Backup
After=zmovie.service

[Service]
Type=oneshot
User=${SERVICE_USER}
Group=${SERVICE_USER}
WorkingDirectory=${INSTALL_DIR}
EnvironmentFile=${ENV_FILE}
Environment=ZMOVIE_DATA_DIR=${DATA_DIR}
Environment=ZMOVIE_BACKUP_DIR=${BACKUP_DIR}
ExecStart=${PYTHON_BIN} -m zmovie_platform.runtime_ops backup
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=${DATA_DIR} ${BACKUP_DIR}
EOF

cat >/etc/systemd/system/zmovie-backup.timer <<'EOF'
[Unit]
Description=Run zMovie verified daily backup

[Timer]
OnCalendar=*-*-* 03:15:00
Persistent=true
RandomizedDelaySec=300

[Install]
WantedBy=timers.target
EOF

systemctl daemon-reload
systemctl enable --now zmovie-worker.service
systemctl enable --now zmovie-watchdog.timer
systemctl enable --now zmovie-backup.timer
systemctl restart zmovie-worker.service

systemctl is-active --quiet zmovie-worker.service
systemctl is-active --quiet zmovie-watchdog.timer
systemctl is-active --quiet zmovie-backup.timer
