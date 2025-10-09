#!/bin/sh
set -ef

dst_dir=/usr/local/share/ca-certificates

w=$(mktemp -d) ; : "${w:?}"
w_cleanup() {
	[ -z "$w" ] || ls -lA "$w/" >&2
	[ -z "$w" ] || rm -rf "$w"
	unset w
	exit "${1:-0}"
}

def_bundle='/etc/ssl/certs/ca-certificates.crt'

openssl-cert-auto-pem.sh "${def_bundle}" "$w/cacert.pem" "$w/cacert.fp"
[ -s "$w/cacert.pem" ] || w_cleanup 1
[ -s "$w/cacert.fp" ]  || w_cleanup 1

openssl-cert-auto-pem.sh "$1" "$w/certifi.pem" "$w/certifi.fp" "$w/certifi.off"
[ -s "$w/certifi.pem" ] || w_cleanup 1
[ -s "$w/certifi.fp" ]  || w_cleanup 1
[ -s "$w/certifi.off" ] || w_cleanup 1

set +e
grep -Fxnv -f "$w/cacert.fp" "$w/certifi.fp" | cut -d : -f 1 > "$w/diff.ln"
set -e

if [ -s "$w/diff.ln" ] ; then
	terse_fingerprint() { cut -d = -f 2- | tr -cd '[:alnum:]' ; }

	while read -r n ; do
		[ -n "$n" ] || continue

		fp=$(sed -ne "${n}p" "$w/certifi.fp" | terse_fingerprint)
		off=$(sed -ne "${n}p" "$w/certifi.off")
		sed -ne "${off}p" "$w/certifi.pem" > "${dst_dir}/certifi-${fp}.crt"
	done < "$w/diff.ln"
fi

rm -rf "$w" ; unset w

exec update-ca-certificates --fresh
