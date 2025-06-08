#!/usr/bin/env bash
# Ensure cache dir is writable, then exec the main CMD
set -e

mkdir -p /tmp/gitingest
chown -R "$(id -u):$(id -g)" /tmp/gitingest

exec "$@"
