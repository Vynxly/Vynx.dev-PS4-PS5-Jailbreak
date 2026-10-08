#!/usr/bin/env bash
set -euo pipefail

VERSION="$(BUILD_TYPE=stable python3 tools/gen_version.py --print)"
IMAGE_NAME="vynx-ps5-autoloader-sdk"
OUTPUT_ELF="vynx-autoloader-installer_v${VERSION}.elf"
OUTPUT_HOST="vynx-autoloader-host_v${VERSION}.py"
RELEASE_DIR="${RELEASE_DIR:-release-v${VERSION}}"

if [[ -n "${PS5_PAYLOAD_SDK:-}" ]]; then
  BUILD_TYPE=stable FORCE_EXPLOIT="${FORCE_EXPLOIT:-auto}" make clean all \
    SDK="$PS5_PAYLOAD_SDK" CC="$PS5_PAYLOAD_SDK/bin/prospero-clang" \
    STRIP="$PS5_PAYLOAD_SDK/bin/prospero-strip"
else
  if ! docker image inspect "$IMAGE_NAME" >/dev/null 2>&1; then
    docker build -t "$IMAGE_NAME" -f Dockerfile.sdk .
  fi
  docker run --rm -u "$(id -u):$(id -g)" \
    -e BUILD_TYPE=stable \
    -e FORCE_EXPLOIT="${FORCE_EXPLOIT:-auto}" \
    -v "$(pwd):/src" -w /src "$IMAGE_NAME" make clean all
fi

mv vynx-autoloader-installer.elf "$OUTPUT_ELF"
BUILD_TYPE=stable make host HOST_PAYLOAD="$OUTPUT_ELF"
mv vynx-autoloader-host.py "$OUTPUT_HOST"

mkdir -p "$RELEASE_DIR"
cp README.md CHANGELOG.md THIRD_PARTY_NOTICES.md .START-HOST.bat "$RELEASE_DIR/"
cp LICENSE "$RELEASE_DIR/"
mkdir -p "$RELEASE_DIR/licenses"
cp licenses/* "$RELEASE_DIR/licenses/"
mkdir -p "$RELEASE_DIR/assets"
cp assets/icon0.png assets/param.json "$RELEASE_DIR/assets/"
mv "$OUTPUT_ELF" "$OUTPUT_HOST" "$RELEASE_DIR/"
echo "Built $RELEASE_DIR/$OUTPUT_ELF and $RELEASE_DIR/$OUTPUT_HOST"
