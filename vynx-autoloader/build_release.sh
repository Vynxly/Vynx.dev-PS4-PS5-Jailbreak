#!/usr/bin/env bash
set -euo pipefail

VERSION="$(BUILD_TYPE=stable python3 tools/gen_version.py --print)"
IMAGE_NAME="vynx-ps5-autoloader-sdk"
OUTPUT_ELF="vynx-autoloader-installer_v${VERSION}.elf"
OUTPUT_HOST="vynx-autoloader-host_v${VERSION}.py"

if ! docker image inspect "$IMAGE_NAME" >/dev/null 2>&1; then
  docker build -t "$IMAGE_NAME" -f Dockerfile.sdk .
fi

docker run --rm -u "$(id -u):$(id -g)" \
  -e BUILD_TYPE=stable \
  -e FORCE_EXPLOIT="${FORCE_EXPLOIT:-auto}" \
  -v "$(pwd):/src" -w /src "$IMAGE_NAME" make clean all

mv vynx-autoloader-installer.elf "$OUTPUT_ELF"
BUILD_TYPE=stable make host HOST_PAYLOAD="$OUTPUT_ELF"
mv vynx-autoloader-host.py "$OUTPUT_HOST"

mkdir -p release
cp README.md THIRD_PARTY_NOTICES.md .START-HOST.bat release/
cp LICENSE release/
mkdir -p release/licenses
cp licenses/* release/licenses/
mkdir -p release/assets
cp assets/icon0.png assets/param.json release/assets/
mv "$OUTPUT_ELF" "$OUTPUT_HOST" release/
echo "Built release/$OUTPUT_ELF and release/$OUTPUT_HOST"
