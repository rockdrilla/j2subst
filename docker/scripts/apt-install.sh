#!/bin/sh
set -ef

find_fresh_ts() {
	{
		find "$@" -exec stat -c '%Y' '{}' '+' 2>/dev/null || :
		# duck and cover!
		echo 1
	} | sort -rn | head -n 1
}

_apt_update() {
	# update package lists; may fail sometimes,
	# e.g. soon-to-release channels like Debian "bullseye" @ 22.04.2021

	# (wannabe) smart package list update
	ts_sources=$(find_fresh_ts /etc/apt/ -follow -regextype egrep -regex '.+\.(list|sources)$' -type f)
	ts_lists=$(find_fresh_ts /var/lib/apt/lists/ -maxdepth 1 -regextype egrep -regex '.+_Packages(\.(bz2|gz|lz[4o]|xz|zstd?))?$' -type f)
	if [ ${ts_sources} -gt ${ts_lists} ] ; then
		apt-env.sh apt-get update
	fi
}

_dpkg_avail_hack() {
	: "${DPKG_ADMINDIR:=/var/lib/dpkg}"
	VERSION_CODENAME=$(. /etc/os-release ; printf '%s' "${VERSION_CODENAME}") || :
	f="${DPKG_ADMINDIR}/available"
	# if ${VERSION_CODENAME} is empty then we're on Debian sid or so :)
	case "${VERSION_CODENAME}" in
	stretch | buster | bionic | focal )
		# ref: https://unix.stackexchange.com/a/271387/49297
		if [ -s "$f" ] ; then
			return
		fi
		/usr/lib/dpkg/methods/apt/update "${DPKG_ADMINDIR}" apt apt
	;;
	* )
		touch "$f"
	;;
	esac
}

_apt_update
_dpkg_avail_hack
exec apt-env.sh apt-get install -y --no-install-recommends --no-install-suggests "$@"
