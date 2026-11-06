#!/usr/bin/env bash
# Decide whether the nightly workflow must build, and write to $GITHUB_OUTPUT:
#  - should_build=true|false;
#  - av_assets / qtav_assets: the AliceVision and QtAliceVision nightly archives published at check
#    time (space separated), listed in the release notes so that later checks detect new nightlies.
#
# Build:
#  - manual runs: always (with a warning when the AliceVision/QtAliceVision nightlies are incomplete
#    or inconsistent);
#  - no complete previous nightly (missing release, or its Linux and Windows archives not both present);
#  - a new AliceVision or QtAliceVision nightly (archives differ from the ones listed in the notes of
#    the last nightly). Waits until QtAliceVision is built against the current AliceVision nightly:
#    it rebuilds within a few hours after each AliceVision nightly, and both are only consistent then;
#  - daily develop build: no nightly was built yet today (UTC), it is past 06:00 UTC (after the
#    AliceVision nightly at 02:00 and the daily QtAliceVision nightly at 04:00) and develop changed
#    since the last nightly. A nightly built earlier the same day, for instance for a new
#    AliceVision nightly, counts as the daily build: merges made after it wait for the next day.
#
# Fail safe: anything unexpected (GitHub API error other than a missing release, malformed release
# or notes, invalid environment, any failing command) fails the check with should_build=false:
# no build, retried next hour, and the failed run is visible in the Actions tab.
#
# Environment: GH_TOKEN, EVENT_NAME, GITHUB_REPOSITORY, GITHUB_SHA, GITHUB_OUTPUT.
set -euo pipefail

: "${GITHUB_OUTPUT:?}"
DECIDED=""

# Write the decision to $GITHUB_OUTPUT ($1: true|false)
decide() {
  DECIDED=$1
  echo "should_build=$1" >> "$GITHUB_OUTPUT"
}

# Report an unexpected situation and stop without building
fail() {
  echo "::error title=Nightly check::$1" >&2
  exit 1
}

# Any exit without a decision (error, unexpected data) means no build, and a failed run
onExit() {
  local status=$?
  if [ -z "$DECIDED" ]; then
    echo "Nightly check failed (exit ${status}): not building." >&2
    echo "should_build=false" >> "$GITHUB_OUTPUT"
    [ "$status" -ne 0 ] || exit 1
  fi
}
trap onExit EXIT

[ -n "${EVENT_NAME:-}" ] || fail "EVENT_NAME is not set."
[ -n "${GITHUB_REPOSITORY:-}" ] || fail "GITHUB_REPOSITORY is not set."
[[ "${GITHUB_SHA:-}" =~ ^[0-9a-f]{40}$ ]] || fail "Invalid GITHUB_SHA: '${GITHUB_SHA:-}'."

AV_REPO=alicevision/AliceVision
QTAV_REPO=alicevision/QtAliceVision
# Only the Linux and Windows archives: other assets cannot trigger rebuilds
ARCHIVE_FILTER='select(.name | endswith("-linux.tar.gz") or endswith("-windows.zip"))'

# "gh release view nightly" on the repository $1, with the extra arguments $2...
# Prints nothing when the release does not exist, fails on any other error.
nightlyRelease() {
  local repo=$1 out err
  shift
  err=$(mktemp)
  if out=$(gh release view nightly --repo "$repo" "$@" 2> "$err"); then
    rm -f "$err"
    printf '%s\n' "$out"
  elif grep -q "release not found" "$err"; then
    rm -f "$err"
  else
    # stderr: stdout is captured by the caller
    echo "::error title=Nightly check::Cannot read the nightly release of ${repo}: $(cat "$err")" >&2
    rm -f "$err"
    return 1
  fi
}

AV_ASSETS=$(nightlyRelease "$AV_REPO" --json assets --jq ".assets[] | ${ARCHIVE_FILTER} | .name")
QTAV_ASSETS=$(nightlyRelease "$QTAV_REPO" --json assets --jq ".assets[] | ${ARCHIVE_FILTER} | .name")
# The QtAliceVision notes list the AliceVision archives each of its archives is built against
QTAV_NOTES=$(nightlyRelease "$QTAV_REPO" --json body --jq '.body')

echo "av_assets=$(echo $AV_ASSETS)" >> "$GITHUB_OUTPUT"
echo "qtav_assets=$(echo $QTAV_ASSETS)" >> "$GITHUB_OUTPUT"

# Upstream nightlies not ready to be used:
#  - both archives must be present: the nightlies delete their assets before uploading the new
#    ones, so a check during their publication sees 0 or 1;
#  - QtAliceVision must be built against the current AliceVision nightly (not rebuilt yet, or
#    publishing its notes).
UPSTREAM_ISSUE=""
if [ "$(grep -c . <<< "$AV_ASSETS" || true)" -ne 2 ] || [ "$(grep -c . <<< "$QTAV_ASSETS" || true)" -ne 2 ]; then
  UPSTREAM_ISSUE="AliceVision or QtAliceVision nightly incomplete (being published?): '${AV_ASSETS//$'\n'/ }' / '${QTAV_ASSETS//$'\n'/ }'"
else
  for ASSET in $AV_ASSETS; do
    if ! grep -qF "\`${ASSET}\`" <<< "$QTAV_NOTES"; then
      UPSTREAM_ISSUE="QtAliceVision nightly not built against ${ASSET} yet"
      break
    fi
  done
fi

if [ "$EVENT_NAME" != "schedule" ]; then
  if [ -n "$UPSTREAM_ISSUE" ]; then
    echo "::warning title=Nightly check::${UPSTREAM_ISSUE}. The next scheduled check will rebuild once they are ready."
  fi
  echo "Manual run: building."
  decide true
  exit 0
fi

if [ -n "$UPSTREAM_ISSUE" ]; then
  echo "${UPSTREAM_ISSUE}. Skipping, retrying next hour."
  decide false
  exit 0
fi

# Last nightly, in a single call: first line, upload time of its archives (the publishedAt of the
# release never changes), empty unless both are present; then its release notes, listing its
# commit and the dependency archives.
LAST_NIGHTLY=$(nightlyRelease "$GITHUB_REPOSITORY" --json assets,body \
               --jq "([.assets[] | ${ARCHIVE_FILTER} | .createdAt] | if length == 2 then min else \"\" end), .body")
LAST_BUILD=$(head -n1 <<< "$LAST_NIGHTLY")
NOTES=$(tail -n +2 <<< "$LAST_NIGHTLY")
LAST_SHA=$(grep -oE '/commit/[0-9a-f]{40}' <<< "$NOTES" | head -n1 | cut -d/ -f3 || true)
# Unexpected last nightly: fail (no build) rather than rebuild every hour, as its commit and
# dependencies would never match (notes format changed, or a publication interrupted before the
# notes update: run the workflow manually)
if [ -n "$LAST_BUILD" ]; then
  [[ "$LAST_BUILD" =~ ^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z$ ]] \
    || fail "Unexpected upload time of the last nightly: '${LAST_BUILD}'."
  [ -n "$LAST_SHA" ] || fail "The notes of the last nightly do not contain its commit (/commit/<sha>)."
  grep -q '^### Dependencies' <<< "$NOTES" || fail "The notes of the last nightly do not list its dependencies (### Dependencies)."
fi

REASON=""
if [ -z "$LAST_BUILD" ]; then
  REASON="no complete previous nightly"
fi
for ASSET in $AV_ASSETS $QTAV_ASSETS; do
  if ! grep -qF "\`${ASSET}\`" <<< "$NOTES"; then
    REASON="${REASON:+$REASON, }new ${ASSET}"
  fi
done

# ISO 8601 UTC timestamps in the same format: lexicographic order is chronological order
NOW=$(date -u +%Y-%m-%dT%H:%M:%SZ)
TODAY=$(date -u +%Y-%m-%dT00:00:00Z)
CUTOFF=$(date -u +%Y-%m-%dT06:00:00Z)
if [ -n "$LAST_BUILD" ] && [[ "$LAST_BUILD" < "$TODAY" && "$CUTOFF" < "$NOW" && "$LAST_SHA" != "$GITHUB_SHA" ]]; then
  REASON="${REASON:+$REASON, }daily build of develop ${LAST_SHA:0:8} -> ${GITHUB_SHA:0:8}"
fi

echo "Last nightly: ${LAST_BUILD:-none} (${LAST_SHA:-unknown commit}), develop: ${GITHUB_SHA}"
if [ -n "$REASON" ]; then
  echo "Building: ${REASON}."
  decide true
else
  echo "Nothing changed since the last nightly. Skipping."
  decide false
fi
