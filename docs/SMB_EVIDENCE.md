# SMB evidence boundary

A successful GitHub CI run proves repository behavior, not Windows SMB availability on DBC. A successful DBC SMB closeout requires runtime evidence generated on that host. `storage-report.json` and `SMB_VERIFY.log` are the evidence boundary for the storage tier; do not mark SMB production-verified until those files were produced by the real DBC runtime.
