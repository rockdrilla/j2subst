#!/bin/sh
set -ef
cd "$(dirname "$0")/../.."

set -a
BUILDAH_FORMAT="${BUILDAH_FORMAT:-docker}"
BUILDAH_ISOLATION="${BUILDAH_ISOLATION:-chroot}"
BUILDAH_NETWORK="${BUILDAH_NETWORK:-host}"
set +a

PYTHONTAG="${PYTHONTAG:-3.13.8-slim-trixie}"

grab_site_packages() {
	podman run \
	  --pull=always --rm \
	  --entrypoint='[]' \
	  --user=nobody:nogroup \
	  -e LANG=C.UTF-8 \
	  -e LC_ALL=C.UTF-8 \
	  -e MALLOC_ARENA_MAX=2 \
	  -e PYTHONUNBUFFERED=1 \
	  -e PYTHONDONTWRITEBYTECODE=1 \
	"$1" \
	python3 -c 'import site;print(site.getsitepackages()[0])'
}

PYTHON_SITE_PACKAGES=$(grab_site_packages "docker.io/python:${PYTHONTAG}")
[ -n "${PYTHON_SITE_PACKAGES:?}" ]

base="docker.io/rockdrilla/j2subst:base-v1"

buildah bud \
  -f docker/Dockerfile.base \
  -t "${base}" \
  --pull=missing --no-cache \
  --build-arg "PYTHONTAG=${PYTHONTAG}" \
  --env "PYTHON_SITE_PACKAGES=${PYTHON_SITE_PACKAGES}" \
  --unsetenv GPG_KEY \
  --unsetenv PYTHON_SHA256 \


c=$(buildah from --pull=never "${base}") || true
if [ -z "$c" ] ; then
	buildah rmi -f "${base}"
	exit 1
fi
buildah config --created-by /usr/local/share/Dockerfile.base "$c"
buildah commit --rm --squash "$c" "${base}"
