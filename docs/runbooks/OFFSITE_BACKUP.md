# Runbook — Encrypted Off-Host Backup

Status: mechanism VERIFIED end to end. Actual off-host replication is
BLOCKED: no operator-approved destination exists on this host.

## 1. Current state (verified 2026-09-25, host `core.zeaz.dev`)

```text
Local verified backups: OK
  /opt/backups/wordpress/zmovie-cinema-*.sql.gz   (daily, integrity checked)
  /var/backups/zmovie/zmovie-*.db                 (SQLite online backup)
DR snapshots:           /opt/backups/dr/<TS>/      (scripts/backup-dr.sh)
Off-host destination:   NONE
  /mnt/zmovie-storage does not exist on this host
  Cloudflare R2 holds Terraform state only and is not an approved backup target
```

Classification: mechanism `IMPLEMENTED_NOT_VERIFIED` for replication,
`BLOCKED` for actual off-host copies.

## 2. One-time operator setup

```bash
# 1) passphrase (never on a command line, never in Git)
sudo install -d -m 700 /etc/zmovie
sudo sh -c 'umask 077; openssl rand -base64 48 > /etc/zmovie/offsite.key'
sudo chmod 600 /etc/zmovie/offsite.key

# 2) approved destination, only if one exists and is approved
sudo install -m 600 /dev/null /etc/zmovie/offsite.env
sudo sh -c 'printf "ZMOVIE_OFFSITE_DEST=/approved/mount/zmovie-backups\nZMOVIE_OFFSITE_RETENTION=14\n" > /etc/zmovie/offsite.env'
```

Store the passphrase separately from the host (independent secured backup).
Without it the archive is unrecoverable.

## 3. Run

```bash
sudo bash scripts/backup-offsite.sh                     # build, verify, stage
ZMOVIE_OFFSITE_DRYRUN=1 sudo bash scripts/backup-offsite.sh  # no writes
```

Behavior:

1. refuses to run unless root, key file exists and is mode 600;
2. packs the newest DR snapshot plus the newest WordPress and SQLite backups;
3. writes `MANIFEST.sha256` (excluding itself);
4. encrypts with `openssl enc -aes-256-cbc -pbkdf2 -iter 600000`, passphrase
   read via `-pass file:` so it never appears in `ps` or shell history;
5. **decrypts the result and re-verifies the manifest** on every run;
6. prunes staged archives beyond the retention count;
7. replicates only when `ZMOVIE_OFFSITE_DEST` is set and already present on
   the host, otherwise it reports BLOCKED and keeps the verified archive
   staged. It never invents a destination.

Schedule (only after a destination is approved):

```bash
sudo crontab -e   # 30 3 * * * <zmovie-repo>/scripts/backup-offsite.sh >> /var/log/zmovie-offsite.log 2>&1
```

## 4. Verify

```bash
sudo ls -l /var/backups/zmovie/offsite/
sudo sha256sum -c /var/backups/zmovie/offsite/zmovie-dr-<TS>.tar.gz.sha256
```

## 5. Restore

```bash
sudo openssl enc -d -aes-256-cbc -pbkdf2 -iter 600000 \
  -in zmovie-dr-<TS>.tar.gz -out payload.tar -pass file:/etc/zmovie/offsite.key
sudo tar -xzf payload.tar -C /tmp/restore-check
cd /tmp/restore-check/payload && sha256sum -c MANIFEST.sha256
```

Restore into an isolated location first. Never overwrite production during a
verification restore.

## 6. Known limitations

- Local staging is on the same host, so it does not by itself protect against
  host loss. Only a configured destination does.
- The archive is encrypted at rest with a passphrase-based KDF; a lost
  passphrase means unrecoverable data.
- Alerting on replication failure is log-based (no MTA on this host), matching
  the existing monitoring approach.
