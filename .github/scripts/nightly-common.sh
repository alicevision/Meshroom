#!/usr/bin/env bash
# Helpers shared by nightly-check.sh and nightly-publish.sh (sourced, not run).
# Requires: gh and jq.

# Fetch the "nightly" release of a repository as raw JSON (GitHub REST API), and check its structure
# once, so that the callers can rely on it. No exit and safe under "set -e": can be called in a subshell.
# Arguments: $1 - repository, "owner/name".
# Output: the release JSON on stdout (only on success); gh error messages on stderr.
# Returns: 0 on success,
#          2 if the release does not exist (HTTP 404),
#          1 on any other error (network, authentication, rate limit) or malformed answer (not JSON, not
#            an object, "assets" not an array, or an asset not an object with a string "name").
fetchNightly() {
  local errFile json rc
  errFile=$(mktemp)
  json=$(gh api "repos/$1/releases/tags/nightly" 2> "$errFile") && rc=0 || rc=$?
  if [ $rc -ne 0 ]; then
    if grep -q "HTTP 404" "$errFile"; then
      rm -f "$errFile"
      return 2
    fi
    sed "s|^|  $1: |" "$errFile" >&2
    rm -f "$errFile"
    return 1
  fi
  rm -f "$errFile"
  if ! jq -e 'type == "object" and (.assets | type == "array")
              and (.assets | all(type == "object" and (.name | type == "string")))' > /dev/null 2>&1 <<< "$json"; then
    echo "  $1: unexpected answer for the nightly release" >&2
    return 1
  fi
  printf '%s\n' "$json"
}
