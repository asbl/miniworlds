#!/bin/sh
# Root-owned application helper; works even when /tmp is mounted noexec.
# Credentials are supplied only through the child process environment.
case "$1" in
  *sername*) printf '%s\n' "${MW_GIT_USER:-x-access-token}" ;;
  *) printf '%s\n' "$MW_GIT_TOKEN" ;;
esac
