DBC SMB quick reference

1. Create /root/.smb-zmovie with username/password/domain; chmod 600.
2. sudo ./scripts/install-smb-storage.sh //WINDOWS-IP/zmovie /mnt/zmovie-storage
3. sudo ./scripts/smb-storage-doctor.sh
4. sudo ./scripts/runtime-closeout-smb.sh --project prj_REAL --provider auto

See docs/SMB_STORAGE.md for the production policy and reboot variant.
