#!/bin/sh
set -ef

apt-env.sh apt-get purge -y --allow-remove-essential "$@"
exec apt-env.sh apt-get autopurge -y
