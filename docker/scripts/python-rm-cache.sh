#!/bin/sh
set -f
for i ; do
	[ -n "$i" ] || continue
	[ -d "$i" ] || continue
	find "$i/" -name __pycache__ -exec rm -rf {} +
	find "$i/" ! -type d -name '*.py[cdo]' -exec rm -f {} +
done
exit 0
