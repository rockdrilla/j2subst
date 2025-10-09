#!/bin/sh
set -ef
: "${1:?}"
d=$(printf '%s' "/run/j2subst/dpkg-divert/$1" | tr -s '/')
mkdir -p "${d%/*}"
dpkg-divert --divert "$d" --rename "$1" 2>/dev/null
rm -f "$d"
