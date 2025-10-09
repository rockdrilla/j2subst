#!/bin/sh
set -f

## apt
find /var/cache/apt/ ! -type d ! -name 'lock' -delete
find /var/lib/apt/ ! -type d -wholename '/var/lib/apt/listchanges*' -delete
find /var/lib/apt/lists/ ! -type d ! -name 'lock' -delete
find /var/log/ ! -type d -wholename '/var/log/apt/*' -delete
find /var/log/ ! -type d -wholename '/var/log/aptitude*' -delete

## dpkg
: "${DPKG_ADMINDIR:=/var/lib/dpkg}"
truncate -s 0 "${DPKG_ADMINDIR}/available"
find "${DPKG_ADMINDIR}/" ! -type d -wholename "${DPKG_ADMINDIR}/*-old" -delete
find /var/log/ ! -type d -wholename '/var/log/alternatives.log' -delete
find /var/log/ ! -type d -wholename '/var/log/dpkg.log' -delete

## DONT DO THIS AT HOME!
find "${DPKG_ADMINDIR}/" ! -type d -wholename "${DPKG_ADMINDIR}/info/*.symbols" -delete

## debconf
find /var/cache/debconf/ ! -type d -wholename '/var/cache/debconf/*-old' -delete

__t=$(mktemp) ; : "${__t:?}"
debconf_trim_i18n() {
	mawk 'BEGIN { m = 0; }
	$0 == "" { print; }
	/^[^[:space:]]/ {
	    if ($1 ~ "\.[Uu][Tt][Ff]-?8:") {
	        m = 1;
	        next;
	    }
	    m = 0;
	    print $0;
	}
	/^[[:space:]]/ {
	    if (m == 1) next;
	    print $0;
	}' < "$1" > "${__t}"
	cat < "${__t}" > "$1"
}

debconf_trim_i18n /var/cache/debconf/templates.dat
while read -r tmpl ; do
	[ -n "${tmpl}" ] || continue
	[ -s "${tmpl}" ] || continue
	debconf_trim_i18n "${tmpl}"
done <<EOF
$(find "${DPKG_ADMINDIR}/info/" -type f -name '*.templates' | sort -V)
EOF
rm -f "${__t}" ; unset __t

## misc
rm -f /var/cache/ldconfig/aux-cache

exit 0
