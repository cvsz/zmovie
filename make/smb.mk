.PHONY: smb-install smb-closeout

SMB_MOUNT ?= /mnt/zmovie-storage
SMB_SHARE ?=
PROJECT ?=
PROVIDER ?= auto

smb-install:
	@test -n "$(SMB_SHARE)" || (echo "Set SMB_SHARE=//WINDOWS-IP/zmovie" >&2; exit 2)
	sudo ./scripts/install-smb-storage.sh "$(SMB_SHARE)" "$(SMB_MOUNT)"

smb-closeout:
	@test -n "$(PROJECT)" || (echo "Set PROJECT=prj_..." >&2; exit 2)
	sudo ZMOVIE_SMB_MOUNT="$(SMB_MOUNT)" ./scripts/runtime-closeout-smb.sh --project "$(PROJECT)" --provider "$(PROVIDER)"
