#!/usr/bin/env bash
# Decide whether the nightly workflow must build. Writes to $GITHUB_OUTPUT:
#   should_build=true|false
#   av_linux, av_windows, qtav_linux, qtav_windows: the AliceVision and QtAliceVision nightly archives
#   seen by this check (empty when unknown), recorded in the notes of the Meshroom nightly.
#
# Scheduled runs build when:
#  - there is no previous nightly (the release is confirmed missing, or lacks one of its archives);
#  - the AliceVision or QtAliceVision nightly changed since the last Meshroom nightly;
#  - daily develop build: no nightly was built yet today (UTC), it is past 05:00 UTC (after the
#    AliceVision nightly at 02:00 and the QtAliceVision one it triggers) and develop changed since
#    the last nightly. A nightly built earlier the same day, for instance for a new AliceVision or
#    QtAliceVision nightly, counts as the daily build: merges made after it wait for the next day.
# They never build while the AliceVision or QtAliceVision nightly is being published, nor while
# the QtAliceVision nightly is not built against the current AliceVision one: it will be rebuilt,
# and building once afterwards bundles consistent binaries.
#
# Manual runs (workflow_dispatch) always build.
#
# Robustness: the default is NOT to build. Any unexpected event, API error, missing value or malformed
# answer leads to should_build=false: a warning when it may be transient (retried next hour), an error
# (failed run) when the state of the Meshroom nightly itself needs a manual fix.
#
# Environment: GH_TOKEN, EVENT_NAME, GITHUB_REPOSITORY, GITHUB_SHA, GITHUB_OUTPUT.
# Requires: gh and jq (both preinstalled on the GitHub-hosted runners).
#
# Structure: main() runs the decision steps in order. Each step either returns (continue) or ends the
# script through skip / warnSkip / fail (no build), and only main() sets SHOULD_BUILD=true, right before
# its successful exit. Decision steps must never run in a subshell ($(...)): their "exit" would only
# leave the subshell.
set -uo pipefail

# ──────────────────────────────────────────────────────────────────────────────
# Configuration
# ──────────────────────────────────────────────────────────────────────────────

AV_REPO="alicevision/AliceVision"
QTAV_REPO="alicevision/QtAliceVision"
# Time of day (UTC) after which the daily develop build may happen
DAILY_CUTOFF="05:00:00"
LINUX_SUFFIX="-linux.tar.gz"
WINDOWS_SUFFIX="-windows.zip"

# ──────────────────────────────────────────────────────────────────────────────
# Global state
# ──────────────────────────────────────────────────────────────────────────────

# Workflow outputs, written by writeOutputs on exit
SHOULD_BUILD=false
AV_LINUX=""
AV_WINDOWS=""
QTAV_LINUX=""
QTAV_WINDOWS=""

# Set by readEvent: "true" for a manual run, "false" for a scheduled one
MANUAL=""
# Set by readDependencies: fetchNightly return codes, and the notes of the QtAliceVision nightly
AV_RC=1
QTAV_RC=1
QTAV_NOTES=""
# Set by readLastNightly: upload date and commit of the last Meshroom nightly (empty when unknown),
# and its release notes
LAST_BUILD=""
LAST_SHA=""
MESHROOM_NOTES=""
# Set by findAsset
ASSET_NAME=""
ASSET_DATE=""
# Comma-separated reasons to build, appended by addReason
REASON=""

# ──────────────────────────────────────────────────────────────────────────────
# Outputs and exits
# ──────────────────────────────────────────────────────────────────────────────

# Write the workflow outputs to $GITHUB_OUTPUT (stdout when unset, for local runs).
# Installed as the EXIT trap, so the outputs are written exactly once whatever the exit path
# (normal end, skip, fail, or an unexpected error), and should_build stays "false" unless main()
# explicitly set SHOULD_BUILD=true.
# Globals read: SHOULD_BUILD, AV_LINUX, AV_WINDOWS, QTAV_LINUX, QTAV_WINDOWS, GITHUB_OUTPUT.
writeOutputs() {
  {
    echo "should_build=${SHOULD_BUILD}"
    echo "av_linux=${AV_LINUX}"
    echo "av_windows=${AV_WINDOWS}"
    echo "qtav_linux=${QTAV_LINUX}"
    echo "qtav_windows=${QTAV_WINDOWS}"
  } >> "${GITHUB_OUTPUT:-/dev/stdout}"
}

# End the script without building, for an expected situation (nothing changed, a dependency
# nightly being published...). The run succeeds.
# Arguments: $1 - message explaining why, printed to the log.
skip() {
  echo "$1. Skipping."
  exit 0
}

# End the script without building, for an abnormal situation that may be transient (API error,
# malformed answer from GitHub, missing dependency release). Emits a GitHub warning annotation;
# the run succeeds and the next hourly check retries.
# Arguments: $1 - message explaining why.
warnSkip() {
  echo "::warning title=Nightly check::$1. Skipping, retrying next hour."
  exit 0
}

# End the script without building, for a situation that will not fix itself (malformed state of the
# Meshroom nightly release, invalid environment). Emits a GitHub error annotation and fails the run,
# rather than rebuilding every hour. A manual run of the workflow rebuilds and republishes the nightly.
# Arguments: $1 - message explaining why.
fail() {
  echo "::error title=Nightly check::$1. Not building: run the Nightly workflow manually to fix it."
  exit 1
}

# Append a reason to build to REASON (comma-separated).
# Arguments: $1 - the reason.
# Globals modified: REASON.
addReason() {
  REASON="${REASON:+$REASON, }$1"
}

# ──────────────────────────────────────────────────────────────────────────────
# GitHub release helpers (no exit: safe to call in a subshell)
# ──────────────────────────────────────────────────────────────────────────────

# Fetch the "nightly" release of a repository as raw JSON (GitHub REST API), and check its structure
# once, so that the extraction helpers below can rely on it.
# Arguments: $1 - repository, "owner/name".
# Output: the release JSON on stdout (only on success); gh error messages on stderr.
# Returns: 0 on success,
#          2 if the release does not exist (HTTP 404),
#          1 on any other error (network, authentication, rate limit) or malformed answer (not JSON, not
#            an object, "assets" not an array, or an asset not an object with a string "name").
fetchNightly() {
  local errFile json rc
  errFile=$(mktemp)
  json=$(gh api "repos/$1/releases/tags/nightly" 2> "$errFile")
  rc=$?
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

# Extract the release notes from a release JSON.
# Arguments: $1 - release JSON (see fetchNightly).
# Output: the notes on stdout, empty when the release has none (null body).
releaseNotes() {
  jq -r 'if .body | type == "string" then .body else "" end' <<< "$1"
}

# Find the single fully uploaded asset whose name ends with a suffix, and validate its name and upload
# date. Assets still being uploaded (state other than "uploaded") are ignored.
# Arguments: $1 - release JSON (see fetchNightly),
#            $2 - name suffix, e.g. "-linux.tar.gz".
# Globals modified: ASSET_NAME, ASSET_DATE: the asset name and upload date (ISO 8601 UTC), both empty
#                   unless found and valid.
# Returns: 0 if found and valid,
#          1 if no asset has this suffix,
#          3 if the answer looks malformed: several matches, unexpected characters in the name (it ends
#            up in the release notes and the workflow outputs), or unexpected date format.
findAsset() {
  local asset count name created
  ASSET_NAME=""
  ASSET_DATE=""
  # The structure (assets are objects with a string name) is checked by fetchNightly
  asset=$(jq -c --arg suffix "$2" '[.assets[] | select(.state == "uploaded" and (.name | endswith($suffix)))]' <<< "$1") || return 3
  count=$(jq 'length' <<< "$asset")
  [ "$count" = "0" ] && return 1
  [ "$count" = "1" ] || return 3
  # "// empty": a missing or null field gives an empty string, rejected by the checks below
  name=$(jq -r '.[0].name // empty' <<< "$asset")
  created=$(jq -r '.[0].created_at // empty' <<< "$asset")
  [[ "$name" =~ ^[A-Za-z0-9._-]+$ ]] && [ "$name" != "$2" ] || return 3
  [[ "$created" =~ ^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z$ ]] || return 3
  ASSET_NAME="$name"
  ASSET_DATE="$created"
}

# Check whether release notes list an archive, written as `name` (Markdown inline code, as in the
# notes of the Meshroom and QtAliceVision nightlies).
# Arguments: $1 - release notes,
#            $2 - archive name.
# Returns: 0 if listed, 1 otherwise.
notesList() {
  grep -qF "\`$2\`" <<< "$1"
}

# Read the "nightly" release of a dependency (AliceVision or QtAliceVision) and store the names of its
# Linux and Windows archives and its notes into the variables named by the caller. The archive names
# stay empty when the release cannot be read or the archive is missing or malformed.
# Arguments: $1 - repository, "owner/name",
#            $2 - name of the variable receiving the Linux archive name,
#            $3 - name of the variable receiving the Windows archive name,
#            $4 - name of the variable receiving the release notes ("" to ignore them).
# Returns: 0 on success, even if an archive is missing (empty name: publication in progress),
#          1 if the release cannot be read (API error or malformed answer, see fetchNightly),
#          2 if the release does not exist,
#          3 if an archive looks malformed (see findAsset): this is not a publication in progress
#            and must not be reported as one.
readDependencyNightly() {
  local release rc linuxRc windowsRc
  release=$(fetchNightly "$1")
  rc=$?
  printf -v "$2" '%s' ""
  printf -v "$3" '%s' ""
  [ $rc -eq 0 ] || return $rc
  findAsset "$release" "$LINUX_SUFFIX"
  linuxRc=$?
  printf -v "$2" '%s' "$ASSET_NAME"
  findAsset "$release" "$WINDOWS_SUFFIX"
  windowsRc=$?
  printf -v "$3" '%s' "$ASSET_NAME"
  if [ -n "$4" ]; then
    printf -v "$4" '%s' "$(releaseNotes "$release")"
  fi
  if [ $linuxRc -eq 3 ] || [ $windowsRc -eq 3 ]; then
    echo "  $1: unexpected archives: $(jq -c '[.assets[] | {name, state, created_at}]' 2> /dev/null <<< "$release")" >&2
    return 3
  fi
  return 0
}

# ──────────────────────────────────────────────────────────────────────────────
# Decision steps (may end the script: never call them in a subshell)
# ──────────────────────────────────────────────────────────────────────────────

# Identify the event that triggered the workflow.
# Globals read: EVENT_NAME.
# Globals modified: MANUAL ("true" for workflow_dispatch, "false" for schedule).
# Exits: skip for any other or missing event (no build).
readEvent() {
  case "${EVENT_NAME:-}" in
    workflow_dispatch) MANUAL=true ;;
    schedule) MANUAL=false ;;
    *) skip "Unexpected event '${EVENT_NAME:-}'" ;;
  esac
}

# Validate the environment provided by GitHub Actions.
# Globals read: GITHUB_SHA (must be a full 40-character commit hash, compared with the commit listed in
#               the notes of the last nightly), GITHUB_REPOSITORY.
# Exits: fail when invalid or missing.
validateEnvironment() {
  if ! [[ "${GITHUB_SHA:-}" =~ ^[0-9a-f]{40}$ ]]; then
    fail "Invalid GITHUB_SHA '${GITHUB_SHA:-}'"
  fi
  if [ -z "${GITHUB_REPOSITORY:-}" ]; then
    fail "GITHUB_REPOSITORY is not set"
  fi
}

# Read the AliceVision and QtAliceVision nightlies and log their archives. Never exits: manual runs
# build even if they cannot be read (the outputs then stay empty and the notes say "unknown").
# Globals modified: AV_LINUX, AV_WINDOWS, AV_RC, QTAV_LINUX, QTAV_WINDOWS, QTAV_NOTES, QTAV_RC.
readDependencies() {
  readDependencyNightly "$AV_REPO" AV_LINUX AV_WINDOWS ""
  AV_RC=$?
  readDependencyNightly "$QTAV_REPO" QTAV_LINUX QTAV_WINDOWS QTAV_NOTES
  QTAV_RC=$?
  echo "AliceVision nightly:   ${AV_LINUX:-?} ${AV_WINDOWS:-?}"
  echo "QtAliceVision nightly: ${QTAV_LINUX:-?} ${QTAV_WINDOWS:-?}"
}

# Turn the readDependencyNightly return code of a dependency into a warning, ending the script, unless
# its release was read and its archives look valid.
# Arguments: $1 - dependency name, for the message ("AliceVision", "QtAliceVision"),
#            $2 - readDependencyNightly return code.
# Exits: warnSkip when the code is not 0.
checkDependencyRead() {
  case $2 in
    0) ;;
    3) warnSkip "Unexpected archives in the $1 nightly release (duplicate, invalid name or date)" ;;
    *) warnSkip "Cannot read the $1 nightly release" ;;
  esac
}

# Check that the AliceVision and QtAliceVision nightlies are usable for a build:
#  - both releases could be read and their archives look valid (otherwise warnSkip, see
#    checkDependencyRead);
#  - both archives of each are present: the nightlies delete their assets before uploading the new
#    ones, so a check during their publication sees 0 or 1 (otherwise skip);
#  - the QtAliceVision nightly is built against the current AliceVision one, as listed in its notes:
#    otherwise it is about to be rebuilt, and building now would pair inconsistent binaries (skip).
# Globals read: AV_RC, QTAV_RC, AV_LINUX, AV_WINDOWS, QTAV_LINUX, QTAV_WINDOWS, QTAV_NOTES.
# Exits: skip or warnSkip when not usable.
checkDependencies() {
  checkDependencyRead "AliceVision" "$AV_RC"
  checkDependencyRead "QtAliceVision" "$QTAV_RC"
  if [ -z "$AV_LINUX" ] || [ -z "$AV_WINDOWS" ]; then
    skip "AliceVision nightly incomplete (being published?)"
  fi
  if [ -z "$QTAV_LINUX" ] || [ -z "$QTAV_WINDOWS" ]; then
    skip "QtAliceVision nightly incomplete (being published?)"
  fi
  if ! notesList "$QTAV_NOTES" "$AV_LINUX" || ! notesList "$QTAV_NOTES" "$AV_WINDOWS"; then
    skip "QtAliceVision nightly not built against the current AliceVision nightly yet"
  fi
}

# Read the last Meshroom nightly: the upload date of its archives (the publishedAt of the release never
# changes, as the release is reused) and its notes, which list its commit and the AliceVision /
# QtAliceVision archives seen when it was built.
# Adds a reason to build when the release is confirmed missing (HTTP 404) or lacks one of its archives:
# runs are queued (concurrency group), so this cannot be a publication in progress.
# Globals read: GITHUB_REPOSITORY.
# Globals modified: LAST_BUILD (earliest upload date of the two archives), LAST_SHA, MESHROOM_NOTES
#                   (all empty when there is no complete previous nightly), REASON.
# Exits: warnSkip when the release cannot be read;
#        fail when its archives look malformed, or its notes do not contain its commit (a published
#        nightly always lists it: failing avoids rebuilding every hour).
readLastNightly() {
  local release rc linuxRc windowsRc linuxDate windowsDate
  release=$(fetchNightly "$GITHUB_REPOSITORY")
  rc=$?
  case $rc in
    0) ;;
    2) addReason "no previous nightly"; return ;;
    *) warnSkip "Cannot read the Meshroom nightly release" ;;
  esac

  findAsset "$release" "$LINUX_SUFFIX"; linuxRc=$?; linuxDate="$ASSET_DATE"
  findAsset "$release" "$WINDOWS_SUFFIX"; windowsRc=$?; windowsDate="$ASSET_DATE"
  if [ $linuxRc -eq 3 ] || [ $windowsRc -eq 3 ]; then
    fail "Unexpected archives in the last nightly: $(jq -c '[.assets[] | {name, state, created_at}]' 2> /dev/null <<< "$release")"
  fi
  if [ -z "$linuxDate" ] || [ -z "$windowsDate" ]; then
    addReason "previous nightly incomplete"
    return
  fi

  # ISO 8601 UTC timestamps in the same format: lexicographic order is chronological order
  if [[ "$linuxDate" < "$windowsDate" ]]; then LAST_BUILD="$linuxDate"; else LAST_BUILD="$windowsDate"; fi
  MESHROOM_NOTES=$(releaseNotes "$release")
  LAST_SHA=$(grep -oE '/commit/[0-9a-f]{40}' <<< "$MESHROOM_NOTES" | head -n1 | cut -d/ -f3)
  [ -n "$LAST_SHA" ] || fail "The notes of the last nightly do not contain its commit (/commit/<sha>)"
}

# Add a reason to build for each AliceVision / QtAliceVision archive not listed in the notes of the last
# Meshroom nightly, i.e. each dependency nightly published since. Does nothing without a complete
# previous nightly (readLastNightly already added a reason then).
# Globals read: LAST_BUILD, MESHROOM_NOTES, AV_LINUX, AV_WINDOWS, QTAV_LINUX, QTAV_WINDOWS.
# Globals modified: REASON.
checkDependencyChanges() {
  local archive
  [ -n "$LAST_BUILD" ] || return 0
  for archive in "$AV_LINUX" "$AV_WINDOWS" "$QTAV_LINUX" "$QTAV_WINDOWS"; do
    if ! notesList "$MESHROOM_NOTES" "$archive"; then
      addReason "new ${archive}"
    fi
  done
}

# Add a reason to build for the daily develop build: the last nightly was built before today (UTC), it is
# past DAILY_CUTOFF (UTC) and develop changed since. A nightly built earlier today, whatever the reason,
# counts as the daily build. Does nothing without a complete previous nightly.
# Globals read: LAST_BUILD, LAST_SHA, GITHUB_SHA, DAILY_CUTOFF.
# Globals modified: REASON.
checkDailyBuild() {
  local now today cutoff
  [ -n "$LAST_BUILD" ] || return 0
  # Same ISO 8601 UTC format as LAST_BUILD, compared lexicographically
  now=$(date -u +%Y-%m-%dT%H:%M:%SZ)
  today=$(date -u +%Y-%m-%dT00:00:00Z)
  cutoff=$(date -u +%Y-%m-%dT${DAILY_CUTOFF}Z)
  if [[ "$LAST_BUILD" < "$today" && "$cutoff" < "$now" && "$LAST_SHA" != "$GITHUB_SHA" ]]; then
    addReason "daily build of develop ${LAST_SHA:0:7} -> ${GITHUB_SHA:0:7}"
  fi
}

# ──────────────────────────────────────────────────────────────────────────────
# Main
# ──────────────────────────────────────────────────────────────────────────────

# Run the decision steps in order and build only if one of them gave a reason. This is the only place
# where SHOULD_BUILD is set to true, right before a successful exit; writeOutputs (EXIT trap) then
# publishes the decision.
main() {
  trap writeOutputs EXIT

  readEvent
  validateEnvironment
  readDependencies

  if [ "$MANUAL" = true ]; then
    echo "Manual run: building."
    SHOULD_BUILD=true
    exit 0
  fi

  checkDependencies
  readLastNightly
  checkDependencyChanges
  checkDailyBuild

  echo "Last nightly: ${LAST_BUILD:-none} (${LAST_SHA:-unknown commit}), develop: ${GITHUB_SHA}"
  [ -n "$REASON" ] || skip "Nothing changed since the last nightly"
  echo "Building: ${REASON}."
  SHOULD_BUILD=true
  exit 0
}

main "$@"
