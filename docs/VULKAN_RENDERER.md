# Vulkan renderer isolation

The hardened web service does not require direct GPU/device access. `zmovie.service` retains `PrivateDevices=true`; production device access belongs to `zmovie-worker.service`.

During native installation, zMovie detects the host `render` and `video` groups. Existing groups are added as supplementary groups for the `zmovie` service user and the worker unit. No group is invented when the host does not provide it. Production models belong under `/var/lib/zmovie/models`, not a user home directory.

## Diagnostics

Run on the production host:

```bash
ip -4 addr show ens33
ls -la /dev/dri
getent group render
getent group video
id zmovie
sudo -u zmovie vulkaninfo --summary
sudo -u zmovie sd-cli --list-devices
sudo zmovie-ctl renderer-doctor
sudo zmovie-ctl vulkan-status
sudo zmovie-ctl sdcpp-status
```

For the documented `dbc` deployment, the application LAN interface is `ens33`; overlay interfaces are not application addressing.

The diagnostic output distinguishes device presence from actual renderer readiness. CPU is a valid real backend when a configured real model generates a valid video, though it may be slow. Missing CUDA is not a production failure by itself.

Do not mark Vulkan runtime verified from CI. Verification requires the commands above in the same host/security context as the production worker.
