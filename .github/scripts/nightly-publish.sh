#!/usr/bin/env bash
# Publish the freshly built archives to the single persistent "nightly" release, all-or-nothing as far as
# GitHub allows it: the previous nightly stays published until the new archives are fully uploaded.
#
# Steps (any error stops the script with a failure, see each function):
#   1. preflight:       validate the environment and the two local archives (integrity, expected content),
#                       read the current assets. Nothing is modified on GitHub before this succeeds.
#   2. uploadAssets:    upload the new archives next to the old ones; on failure, remove what was uploaded
#                       so that the previous nightly is left intact.
#   3. deleteOldAssets: remove the previous archives.
#   4. updateNotes:     rewrite the release notes (commit, archives, AliceVision / QtAliceVision nightlies).
#   5. verifyRelease:   check the final state: exactly the two new archives, fully uploaded, with the local
#                       sizes, and notes listing them and the commit.
#
# A failure after step 2 cannot be rolled back, but leaves a state that the hourly nightly check
# (.github/scripts/nightly-check.sh) detects: duplicate archives (error, run the workflow manually), or notes
# not matching the archives (rebuild).
#
# Environment: GH_TOKEN, GITHUB_REPOSITORY, GITHUB_SHA, BUILD_LABEL, SHORT_SHA,
#              AV_LINUX, AV_WINDOWS, QTAV_LINUX, QTAV_WINDOWS (may be empty: "unknown" in the notes),
#              DIST_DIR (folder of the downloaded build artifacts, default "dist").
# Requires: gh, jq, tar, unzip (preinstalled on the GitHub-hosted Ubuntu runners).
set -euo pipefail

DIST_DIR="${DIST_DIR:-dist}"

# Set by preflight
REPO=""
LINUX_NAME=""
WINDOWS_NAME=""
LINUX_FILE=""
WINDOWS_FILE=""
# Names of the assets of the release before publication, one per line
OLD_ASSETS=""

# ──────────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────────

# Stop the publication with a GitHub error annotation and a failed run.
# Arguments: $1 - message.
fail() {
  echo "::error title=Nightly publication::$1"
  exit 1
}

# Print the JSON of the "nightly" release of the repository.
# Output: the release JSON on stdout.
# Returns: 0 on success, 2 if the release does not exist (HTTP 404), 1 on any other error or if the answer
#          is not a release object with an "assets" array.
fetchRelease() {
  local errFile json
  errFile=$(mktemp)
  if ! json=$(gh api "repos/${REPO}/releases/tags/nightly" 2> "$errFile"); then
    if grep -q "HTTP 404" "$errFile"; then
      rm -f "$errFile"
      return 2
    fi
    cat "$errFile" >&2
    rm -f "$errFile"
    return 1
  fi
  rm -f "$errFile"
  jq -e 'type == "object" and (.assets | type == "array")' > /dev/null 2>&1 <<< "$json" || return 1
  printf '%s\n' "$json"
}

# Check whether a name is in a newline-separated list.
# Arguments: $1 - list, $2 - name.
# Returns: 0 if listed, 1 otherwise.
inList() {
  grep -qxF -- "$2" <<< "$1"
}

# Check a local archive: present, non-empty, readable to the end, with a single top-level folder named
# after the archive and containing the GUI executable.
# Arguments: $1 - archive path,
#            $2 - expected top-level folder,
#            $3 - path of the GUI executable inside the archive.
# Exits: fail on any problem.
checkArchive() {
  local listing topLevel
  [ -s "$1" ] || fail "Archive missing or empty: $1"
  case "$1" in
    *.tar.gz) listing=$(tar -tzf "$1") || fail "Corrupt archive: $1" ;;
    *.zip)    unzip -tq "$1" > /dev/null || fail "Corrupt archive: $1"
              listing=$(unzip -Z1 "$1") || fail "Cannot list archive: $1" ;;
    *)        fail "Unexpected archive type: $1" ;;
  esac
  topLevel=$(cut -d/ -f1 <<< "$listing" | sort -u)
  [ "$topLevel" = "$2" ] || fail "Unexpected top-level content in $1: ${topLevel//$'\n'/ }"
  inList "$listing" "$3" || fail "$3 missing from $1"
}

# ──────────────────────────────────────────────────────────────────────────────
# Steps
# ──────────────────────────────────────────────────────────────────────────────

# Validate the environment and the local archives, create the release if it does not exist yet, and record
# its current assets. Nothing existing is modified on GitHub by this step.
# Globals modified: REPO, LINUX_NAME, WINDOWS_NAME, LINUX_FILE, WINDOWS_FILE, OLD_ASSETS.
# Exits: fail on any problem.
preflight() {
  local release rc
  REPO="${GITHUB_REPOSITORY:-}"
  [ -n "$REPO" ] || fail "GITHUB_REPOSITORY is not set"
  [[ "${GITHUB_SHA:-}" =~ ^[0-9a-f]{40}$ ]] || fail "Invalid GITHUB_SHA '${GITHUB_SHA:-}'"
  [[ "${SHORT_SHA:-}" =~ ^[0-9a-f]{7,}$ && "$GITHUB_SHA" == "$SHORT_SHA"* ]] || fail "Invalid SHORT_SHA '${SHORT_SHA:-}'"
  # The label ends up in asset names: only allow safe characters
  [[ "${BUILD_LABEL:-}" =~ ^[A-Za-z0-9._-]+$ ]] || fail "Invalid BUILD_LABEL '${BUILD_LABEL:-}'"

  LINUX_NAME="Meshroom-${BUILD_LABEL}-linux.tar.gz"
  WINDOWS_NAME="Meshroom-${BUILD_LABEL}-windows.zip"
  LINUX_FILE="${DIST_DIR}/binary-linux/${LINUX_NAME}"
  WINDOWS_FILE="${DIST_DIR}/binary-windows/${WINDOWS_NAME}"
  checkArchive "$LINUX_FILE" "Meshroom-${BUILD_LABEL}-linux" "Meshroom-${BUILD_LABEL}-linux/Meshroom"
  checkArchive "$WINDOWS_FILE" "Meshroom-${BUILD_LABEL}-windows" "Meshroom-${BUILD_LABEL}-windows/Meshroom.exe"
  echo "Archives checked: ${LINUX_NAME}, ${WINDOWS_NAME}"

  release=$(fetchRelease) && rc=0 || rc=$?
  if [ $rc -eq 2 ]; then
    echo "Creating the nightly release"
    gh release create nightly --repo "$REPO" --title "Nightly build (develop)" \
      --notes "_(first build)_" --prerelease || fail "Cannot create the nightly release"
    release=$(fetchRelease) || fail "Cannot read the nightly release after creating it"
  elif [ $rc -ne 0 ]; then
    fail "Cannot read the nightly release"
  fi
  OLD_ASSETS=$(jq -r '.assets[].name' <<< "$release") || fail "Cannot list the assets of the nightly release"
  echo "Current assets: ${OLD_ASSETS:-none}" | tr '\n' ' '
  echo
}

# Remove the new archives uploaded by a failed uploadAssets, unless they replaced assets of the same name
# (those cannot be restored: the nightly check then sees a missing archive and rebuilds).
# Globals read: LINUX_NAME, WINDOWS_NAME, OLD_ASSETS.
rollbackUpload() {
  local name
  for name in "$LINUX_NAME" "$WINDOWS_NAME"; do
    if ! inList "$OLD_ASSETS" "$name"; then
      echo "Rollback: removing ${name}"
      gh release delete-asset nightly "$name" --repo "$REPO" --yes \
        || echo "::warning title=Nightly publication::Rollback: cannot remove ${name} (not uploaded?)"
    fi
  done
}

# Upload the two new archives next to the previous ones. An asset with the same name (rebuild of the same
# commit the same day, e.g. for a new AliceVision nightly) is replaced (--clobber).
# Exits: fail after rollbackUpload if the upload fails.
uploadAssets() {
  echo "Uploading ${LINUX_NAME} and ${WINDOWS_NAME}"
  if ! gh release upload nightly --repo "$REPO" --clobber "$LINUX_FILE" "$WINDOWS_FILE"; then
    rollbackUpload
    fail "Upload failed: the previous nightly is left in place"
  fi
}

# Remove the previous archives: every recorded asset that is not one of the two new archives.
# Globals read: OLD_ASSETS, LINUX_NAME, WINDOWS_NAME.
# Exits: fail if a removal fails (the nightly check then sees duplicate archives and reports an error).
deleteOldAssets() {
  local name
  while IFS= read -r name; do
    [ -n "$name" ] || continue
    if [ "$name" != "$LINUX_NAME" ] && [ "$name" != "$WINDOWS_NAME" ]; then
      echo "Removing previous asset: ${name}"
      gh release delete-asset nightly "$name" --repo "$REPO" --yes || fail "Cannot remove the previous asset ${name}"
    fi
  done <<< "$OLD_ASSETS"
}

# Rewrite the release notes. The nightly check relies on them: the commit link (/commit/<sha>) and the
# archive names in `backticks`.
# Exits: fail if the update fails (the nightly check then sees notes not matching the archives and rebuilds).
updateNotes() {
  local notesFile
  notesFile=$(mktemp)
  cat > "$notesFile" << EOF
> [!WARNING]
> **Automated nightly build** from the \`develop\` branch. May be unstable.

| | |
|---|---|
| Date   | $(date -u '+%Y-%m-%d %H:%M UTC') |
| Commit | [${SHORT_SHA}](https://github.com/${REPO}/commit/${GITHUB_SHA}) |
| **Windows** | \`${WINDOWS_NAME}\` |
| **Linux** | \`${LINUX_NAME}\` |

### Dependencies

The binaries embed the Python interpreter of the AliceVision nightly below. A new AliceVision or QtAliceVision nightly triggers a rebuild.

| | Linux | Windows |
|---|---|---|
| AliceVision | \`${AV_LINUX:-unknown}\` | \`${AV_WINDOWS:-unknown}\` |
| QtAliceVision | \`${QTAV_LINUX:-unknown}\` | \`${QTAV_WINDOWS:-unknown}\` |
EOF
  gh release edit nightly --repo "$REPO" --notes-file "$notesFile" || fail "Cannot update the release notes"
  rm -f "$notesFile"
}

# Check the published state: exactly the two new archives, fully uploaded, with the sizes of the local
# files, and notes listing the commit and both archives.
# Exits: fail on any mismatch.
verifyRelease() {
  local release names name file expected actual notes
  release=$(fetchRelease) || fail "Cannot read the nightly release for verification"
  names=$(jq -r '.assets[].name' <<< "$release" | sort)
  [ "$names" = "$(printf '%s\n' "$LINUX_NAME" "$WINDOWS_NAME" | sort)" ] \
    || fail "Unexpected assets after publication: ${names//$'\n'/ }"
  for file in "$LINUX_FILE" "$WINDOWS_FILE"; do
    name=$(basename "$file")
    expected=$(stat -c %s "$file")
    actual=$(jq -r --arg n "$name" '.assets[] | select(.name == $n) | "\(.state) \(.size)"' <<< "$release")
    [ "$actual" = "uploaded ${expected}" ] || fail "${name}: expected 'uploaded ${expected}', got '${actual}'"
  done
  notes=$(jq -r '.body // ""' <<< "$release")
  grep -qF "/commit/${GITHUB_SHA}" <<< "$notes" || fail "The release notes do not contain the commit"
  grep -qF "\`${LINUX_NAME}\`" <<< "$notes" && grep -qF "\`${WINDOWS_NAME}\`" <<< "$notes" \
    || fail "The release notes do not list the new archives"
  echo "Nightly published: ${LINUX_NAME}, ${WINDOWS_NAME} (${GITHUB_SHA})"
}

main() {
  preflight
  uploadAssets
  deleteOldAssets
  updateNotes
  verifyRelease
}

main "$@"
