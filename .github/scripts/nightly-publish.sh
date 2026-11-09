#!/usr/bin/env bash
# Publish the freshly built archives to the single persistent "nightly" release, all-or-nothing as far as
# GitHub allows it: the previous nightly stays published until the new archives are fully uploaded.
#
# Steps (any error stops the script with a failure, see each function):
#   1. preflight:       validate the environment and the four local archives (integrity, expected content),
#                       read the current assets. Nothing is modified on GitHub before this succeeds.
#   2. uploadAssets:    upload the new archives next to the old ones; on failure, remove what was uploaded
#                       so that the previous nightly is left intact.
#   3. deleteOldAssets: remove the previous archives.
#   4. updateNotes:     rewrite the release notes (commit, archives, AliceVision / QtAliceVision nightlies).
#   5. verifyRelease:   check the final state: exactly the four new archives, fully uploaded, with the local
#                       sizes, and notes listing them and the commit.
#
# The four archives, per platform (Linux, Windows): Meshroom only, and "full" (Meshroom with the AliceVision
# and QtAliceVision nightlies).
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
LINUX_FULL_NAME=""
WINDOWS_FULL_NAME=""
# Paths of the four local archives, and their names one per line
NEW_FILES=()
NEW_NAMES=""
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
# after the build, containing the GUI executable (and, for a full archive, AliceVision and QtAliceVision).
# Arguments: $1 - archive path,
#            $2 - expected top-level folder,
#            $3 - "full" if the archive must bundle AliceVision, QtAliceVision and Python (non-empty
#                 aliceVision/, qtPlugins/ and python/ folders), "meshroom" if it must not contain them,
#            $4... - paths that must be in the archive, relative to the top-level folder
#                    (e.g. the GUI executable).
# Exits: fail on any problem.
checkArchive() {
  local archive="$1" top="$2" kind="$3" listing topLevel entry dir
  shift 3
  [ -s "$archive" ] || fail "Archive missing or empty: $archive"
  case "$archive" in
    *.tar.gz) listing=$(tar -tzf "$archive") || fail "Corrupt archive: $archive" ;;
    *.zip)    unzip -tq "$archive" > /dev/null || fail "Corrupt archive: $archive"
              listing=$(unzip -Z1 "$archive") || fail "Cannot list archive: $archive" ;;
    *)        fail "Unexpected archive type: $archive" ;;
  esac
  topLevel=$(cut -d/ -f1 <<< "$listing" | sort -u)
  [ "$topLevel" = "$top" ] || fail "Unexpected top-level content in $archive: ${topLevel//$'\n'/ }"
  for entry in "$@"; do
    inList "$listing" "${top}/${entry}" || fail "${top}/${entry} missing from $archive"
  done
  for dir in aliceVision qtPlugins python; do
    case "$kind" in
      full)     grep -q "^${top}/${dir}/." <<< "$listing" || fail "${top}/${dir}/ missing or empty in $archive" ;;
      meshroom) if grep -q "^${top}/${dir}/" <<< "$listing"; then fail "$archive must not contain ${top}/${dir}/"; fi ;;
      *)        fail "checkArchive: unexpected kind '$kind'" ;;
    esac
  done
}

# ──────────────────────────────────────────────────────────────────────────────
# Steps
# ──────────────────────────────────────────────────────────────────────────────

# Validate the environment and the local archives, create the release if it does not exist yet, and record
# its current assets. Nothing existing is modified on GitHub by this step.
# Globals modified: REPO, LINUX_NAME, WINDOWS_NAME, LINUX_FULL_NAME, WINDOWS_FULL_NAME, NEW_FILES, NEW_NAMES,
#                   OLD_ASSETS.
# Exits: fail on any problem.
preflight() {
  local release rc linuxTop windowsTop file
  local bundled=()
  REPO="${GITHUB_REPOSITORY:-}"
  [ -n "$REPO" ] || fail "GITHUB_REPOSITORY is not set"
  [[ "${GITHUB_SHA:-}" =~ ^[0-9a-f]{40}$ ]] || fail "Invalid GITHUB_SHA '${GITHUB_SHA:-}'"
  [[ "${SHORT_SHA:-}" =~ ^[0-9a-f]{7,}$ && "$GITHUB_SHA" == "$SHORT_SHA"* ]] || fail "Invalid SHORT_SHA '${SHORT_SHA:-}'"
  # The label ends up in asset names: only allow safe characters
  [[ "${BUILD_LABEL:-}" =~ ^[A-Za-z0-9._-]+$ ]] || fail "Invalid BUILD_LABEL '${BUILD_LABEL:-}'"

  # Every archive of a platform holds the same top-level folder
  linuxTop="Meshroom-${BUILD_LABEL}-linux"
  windowsTop="Meshroom-${BUILD_LABEL}-windows"
  LINUX_NAME="${linuxTop}.tar.gz"
  WINDOWS_NAME="${windowsTop}.zip"
  LINUX_FULL_NAME="${linuxTop}-full.tar.gz"
  WINDOWS_FULL_NAME="${windowsTop}-full.zip"
  NEW_FILES=(
    "${DIST_DIR}/binary-linux/${LINUX_NAME}"
    "${DIST_DIR}/binary-windows/${WINDOWS_NAME}"
    "${DIST_DIR}/binary-linux/${LINUX_FULL_NAME}"
    "${DIST_DIR}/binary-windows/${WINDOWS_FULL_NAME}"
  )
  NEW_NAMES=$(for file in "${NEW_FILES[@]}"; do basename "$file"; done)

  # Key files of the bundled dependencies: AliceVision data, QtAliceVision QML module
  bundled=("aliceVision/share/aliceVision/cameraSensors.db" "qtPlugins/qml/AliceVision/qmldir")
  checkArchive "${NEW_FILES[0]}" "$linuxTop" meshroom "Meshroom"
  checkArchive "${NEW_FILES[1]}" "$windowsTop" meshroom "Meshroom.exe"
  checkArchive "${NEW_FILES[2]}" "$linuxTop" full "Meshroom" "${bundled[@]}" "python/bin/python3"
  checkArchive "${NEW_FILES[3]}" "$windowsTop" full "Meshroom.exe" "${bundled[@]}" "python/python.exe"
  echo "Archives checked: ${NEW_NAMES//$'\n'/, }"

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
# Globals read: NEW_NAMES, OLD_ASSETS.
rollbackUpload() {
  local name
  while IFS= read -r name; do
    if ! inList "$OLD_ASSETS" "$name"; then
      echo "Rollback: removing ${name}"
      gh release delete-asset nightly "$name" --repo "$REPO" --yes \
        || echo "::warning title=Nightly publication::Rollback: cannot remove ${name} (not uploaded?)"
    fi
  done <<< "$NEW_NAMES"
}

# Upload the four new archives next to the previous ones. An asset with the same name (rebuild of the same
# commit the same day, e.g. for a new AliceVision nightly) is replaced (--clobber).
# Exits: fail after rollbackUpload if the upload fails.
uploadAssets() {
  echo "Uploading ${NEW_NAMES//$'\n'/, }"
  if ! gh release upload nightly --repo "$REPO" --clobber "${NEW_FILES[@]}"; then
    rollbackUpload
    fail "Upload failed: the previous nightly is left in place"
  fi
}

# Remove the previous archives: every recorded asset that is not one of the four new archives.
# Globals read: OLD_ASSETS, NEW_NAMES.
# Exits: fail if a removal fails (the nightly check then sees duplicate archives and reports an error).
deleteOldAssets() {
  local name
  while IFS= read -r name; do
    [ -n "$name" ] || continue
    if ! inList "$NEW_NAMES" "$name"; then
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

| | Meshroom | Meshroom + AliceVision + QtAliceVision |
|---|---|---|
| **Windows** | \`${WINDOWS_NAME}\` | \`${WINDOWS_FULL_NAME}\` |
| **Linux** | \`${LINUX_NAME}\` | \`${LINUX_FULL_NAME}\` |

The full archives are ready to use: they bundle the AliceVision and QtAliceVision nightlies below in the \`aliceVision/\`, \`qtPlugins/\` and \`python/\` folders of Meshroom.

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

# Check the published state: exactly the four new archives, fully uploaded, with the sizes of the local
# files, and notes listing the commit and all the archives.
# Exits: fail on any mismatch.
verifyRelease() {
  local release names name file expected actual notes
  release=$(fetchRelease) || fail "Cannot read the nightly release for verification"
  names=$(jq -r '.assets[].name' <<< "$release" | sort)
  [ "$names" = "$(sort <<< "$NEW_NAMES")" ] \
    || fail "Unexpected assets after publication: ${names//$'\n'/ }"
  notes=$(jq -r '.body // ""' <<< "$release")
  grep -qF "/commit/${GITHUB_SHA}" <<< "$notes" || fail "The release notes do not contain the commit"
  for file in "${NEW_FILES[@]}"; do
    name=$(basename "$file")
    expected=$(stat -c %s "$file")
    actual=$(jq -r --arg n "$name" '.assets[] | select(.name == $n) | "\(.state) \(.size)"' <<< "$release")
    [ "$actual" = "uploaded ${expected}" ] || fail "${name}: expected 'uploaded ${expected}', got '${actual}'"
    grep -qF "\`${name}\`" <<< "$notes" || fail "The release notes do not list ${name}"
  done
  echo "Nightly published: ${NEW_NAMES//$'\n'/, } (${GITHUB_SHA})"
}

main() {
  preflight
  uploadAssets
  deleteOldAssets
  updateNotes
  verifyRelease
}

main "$@"
