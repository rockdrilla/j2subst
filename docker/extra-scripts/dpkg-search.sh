#!/bin/sh
set -ef
: "${1:?}"

if dpkg-query --search "$1" ; then
	exit 0
fi

case "$1" in
*\** | *\?* )
	env printf '%s does not support globs: %q\n' "${0##*/}" "$1" >&2
	exit 1
;;
esac

while read -r f ; do
	[ -n "$f" ] || continue
	dpkg-query --search "$f" || continue
	exit 0
done <<EOF
$(set +e ; find / -xdev -follow -samefile "$1" 2>/dev/null | grep -Fxv -e "$1")
EOF

exit 1
