#!/bin/sh
set -ef
cd "$(dirname "$0")/../.."

IMAGE_VERSION="${IMAGE_VERSION:-v0.0.4}"

set -a
BUILDAH_FORMAT="${BUILDAH_FORMAT:-docker}"
BUILDAH_ISOLATION="${BUILDAH_ISOLATION:-chroot}"
BUILDAH_NETWORK="${BUILDAH_NETWORK:-host}"
set +a

base="docker.io/rockdrilla/j2subst:base-v1"
img="docker.io/rockdrilla/j2subst:${IMAGE_VERSION}$2"

buildah bud \
  -f docker/Dockerfile \
  -t "${img}" \
  --pull=missing --no-cache \
  --ignorefile=docker/.dockerignore \
  --build-arg "BASE_IMAGE=${base}" \
  --build-arg "IMAGE_VERSION=${IMAGE_VERSION}" \
