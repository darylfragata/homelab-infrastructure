#!/bin/bash
set -e  # Exit immediately if a command exits with a non-zero status

# Own log file; invoked on demand via aws ssm send-command, safe to re-run.
exec > /var/log/mount-data-volume.log 2>&1

# Nitro instances attach EBS volumes as raw NVMe disks (e.g. /dev/nvme1n1),
# not under the requested device name - there's no udev rule on stock Ubuntu
# to symlink it back. Identify the data volume as "the whole disk that isn't
# the root disk" instead of guessing a device name.
DATA_MOUNT="/mnt/ado-data"
ROOT_DISK=$(lsblk -dno PKNAME "$(findmnt -no SOURCE /)")
DATA_DEVICE=""
for i in $(seq 1 30); do
  DATA_DEVICE=$(lsblk -dno NAME,TYPE | awk -v root="$ROOT_DISK" '$2 == "disk" && $1 != root { print "/dev/" $1; exit }')
  [ -n "$DATA_DEVICE" ] && break
  sleep 2
done

if [ -z "$DATA_DEVICE" ]; then
  echo "ERROR: no data volume disk found (only the root disk, $ROOT_DISK) - is aws_volume_attachment.data attached to this instance?" >&2
  exit 1
fi

# Only format if the device has no existing filesystem - keeps this safe to
# re-run and avoids wiping data on an already-provisioned volume.
if ! blkid "$DATA_DEVICE" >/dev/null 2>&1; then
  mkfs.ext4 "$DATA_DEVICE"
fi

mkdir -p "$DATA_MOUNT"
if ! mountpoint -q "$DATA_MOUNT"; then
  mount "$DATA_DEVICE" "$DATA_MOUNT"
fi

# Persist across reboots - nofail so a slow/missing attachment never blocks boot.
DATA_UUID=$(blkid -s UUID -o value "$DATA_DEVICE")
if ! grep -q "$DATA_UUID" /etc/fstab; then
  echo "UUID=$DATA_UUID $DATA_MOUNT ext4 defaults,nofail 0 2" >> /etc/fstab
fi

mkdir -p "$DATA_MOUNT/azagent" "$DATA_MOUNT/tfvars"
chown -R "ubuntu:ubuntu" "$DATA_MOUNT"

# Symlink the agent's working directory and tfvars dir onto the data volume.
# Run this before configure_agent on a fresh instance so azagent doesn't
# exist yet. If a path already exists as a real directory (e.g. azagent from
# a prior configure_agent run before this volume existed), migrate its
# contents first so nothing is lost.
for path in azagent tfvars; do
  target="/home/ubuntu/$path"
  dest="$DATA_MOUNT/$path"
  if [ -d "$target" ] && [ ! -L "$target" ]; then
    shopt -s dotglob nullglob
    mv "$target"/* "$dest"/ 2>/dev/null || true
    shopt -u dotglob nullglob
    rmdir "$target" # fails loudly (set -e) if anything was left behind
  fi
  if [ ! -e "$target" ]; then
    ln -sfn "$dest" "$target"
  fi
  chown -h "ubuntu:ubuntu" "$target"
done

echo "Data volume mounted at $DATA_MOUNT ($DATA_DEVICE, UUID=$DATA_UUID)"
