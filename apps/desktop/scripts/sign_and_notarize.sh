#!/usr/bin/env bash
set -euo pipefail

# macOS Electron app signing + notarization helper
# Usage (env-driven):
#   IDENTITY="Donald Proctor (2A3WS76FV4)" TEAM_ID=2A3WS76FV4 \
#   NOTARY_PROFILE="atomic-notary" \
#   APP_NAME="Atomic Desktop.app" \
#   ./scripts/sign_and_notarize.sh
#
# Or using Apple ID:
#   APPLE_ID="TPRIPPY@GMAIL.COM" TEAM_ID=2A3WS76FV4 APP_PASSWORD="app-specific-password" \
#   ./scripts/sign_and_notarize.sh

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
BUILD_DIR="${ROOT_DIR}/dist/mac-arm64"
APP_NAME="${APP_NAME:-Atomic Desktop.app}"
APP_PATH="${BUILD_DIR}/${APP_NAME}"
APP_CLEAN="${BUILD_DIR}/${APP_NAME%.app}-CLEAN.app"

ENT_MAIN="${ROOT_DIR}/build/entitlements.mac.plist"
ENT_INHERIT="${ROOT_DIR}/build/entitlements.mac.inherit.plist"

IDENTITY="${IDENTITY:-}"  # Common Name (no "Developer ID Application:" prefix)
TEAM_ID="${TEAM_ID:-}"
NOTARY_PROFILE="${NOTARY_PROFILE:-}"
APPLE_ID="${APPLE_ID:-}"
APP_PASSWORD="${APP_PASSWORD:-}"

DMG_OUT="${ROOT_DIR}/dist/${APP_NAME/.app/}-signed.dmg"

log(){ printf "[sign] %s\n" "$*"; }
die(){ printf "[sign:ERROR] %s\n" "$*" >&2; exit 1; }
run(){ log "$*"; eval "$*"; }

require(){ command -v "$1" >/dev/null 2>&1 || die "Missing required tool: $1"; }

scrub_all_xattrs(){
  local target="$1"
  dot_clean -m "$target" || true
  find "$target" -name '._*' -type f -print -delete || true
  while IFS= read -r -d '' any; do xattr -d com.apple.FinderInfo "$any" 2>/dev/null || true; done < <(find "$target" -print0)
  while IFS= read -r -d '' any; do xattr -d com.apple.ResourceFork "$any" 2>/dev/null || true; done < <(find "$target" -print0)
  xattr -cr "$target" || true
}

main(){
  require xattr; require codesign; require xcrun; require plutil; require find; require sed

  # 1) Build unsigned app directory
  if [[ ! -d "$APP_PATH" ]]; then
    log "Building unsigned app directory via electron-builder (dir)…"
    (cd "$ROOT_DIR" && CSC_IDENTITY_AUTO_DISCOVERY=false npx --yes electron-builder --mac --dir)
  fi
  [[ -d "$APP_PATH" ]] || die "App not found: $APP_PATH"

  # 2) Create a cleaned copy without extended attributes/resource forks
  log "Creating cleaned app bundle (ditto --noextattr --norsrc)"
  rm -rf "$APP_CLEAN"
  ditto --noextattr --norsrc "$APP_PATH" "$APP_CLEAN"
  # Remove any AppleDouble files and residual resource forks
  scrub_all_xattrs "$APP_CLEAN"

  # 3) Sign nested binaries (helpers, frameworks, dylibs)
  [[ -n "$IDENTITY" ]] || die "IDENTITY (codesign CN) is required"
  [[ -f "$ENT_MAIN" && -f "$ENT_INHERIT" ]] || die "Entitlement plists missing under build/"

  FRAME_DIR="$APP_CLEAN/Contents/Frameworks"
  if [[ -d "$FRAME_DIR" ]]; then
    log "Signing nested .dylib/.so files"
    while IFS= read -r -d '' f; do
      xattr -cr "$f" || true
      xattr -d com.apple.FinderInfo "$f" 2>/dev/null || true
      xattr -d com.apple.ResourceFork "$f" 2>/dev/null || true
      run "codesign --force --timestamp --options runtime -s \"$IDENTITY\" \"$f\""
    done < <(find "$FRAME_DIR" -type f \( -name "*.dylib" -o -name "*.so" \) -print0)

    log "Signing .framework bundles"
    while IFS= read -r -d '' fw; do
      xattr -cr "$fw" || true
      xattr -d com.apple.FinderInfo "$fw" 2>/dev/null || true
      xattr -d com.apple.ResourceFork "$fw" 2>/dev/null || true
      run "codesign --force --timestamp --options runtime -s \"$IDENTITY\" \"$fw\""
    done < <(find "$FRAME_DIR" -type d -name "*.framework" -print0)

    log "Signing Helper apps (bundle level)"
    while IFS= read -r -d '' helper_app; do
      xattr -cr "$helper_app" || true
      xattr -d com.apple.FinderInfo "$helper_app" 2>/dev/null || true
      xattr -d com.apple.ResourceFork "$helper_app" 2>/dev/null || true
      run "codesign --force --deep --timestamp --options runtime --entitlements \"$ENT_INHERIT\" -s \"$IDENTITY\" \"$helper_app\""
    done < <(find "$FRAME_DIR" -type d -name "*.app" -print0)
    # Extra scrub after helper signing
    scrub_all_xattrs "$APP_CLEAN"
  fi

  # 4) Sign main app
  log "Signing main app bundle"
  xattr -cr "$APP_CLEAN" || true
  xattr -d com.apple.FinderInfo "$APP_CLEAN" 2>/dev/null || true
  xattr -d com.apple.ResourceFork "$APP_CLEAN" 2>/dev/null || true
  run "codesign --force --timestamp --options runtime --entitlements \"$ENT_MAIN\" -s \"$IDENTITY\" \"$APP_CLEAN\""

  # 5) Verify signature
  log "Verifying codesign (deep/strict)"
  run "codesign --verify --deep --strict --verbose=2 \"$APP_CLEAN\""

  # 6) Create DMG
  VOL="${APP_NAME/.app/}"
  log "Creating DMG: $DMG_OUT"
  rm -f "$DMG_OUT" || true
  hdiutil create -volname "$VOL" -srcfolder "$APP_CLEAN" -ov -format UDZO "$DMG_OUT"

  # 7) Notarize (prefer keychain profile)
  if [[ -n "${NOTARY_PROFILE}" ]]; then
    log "Submitting for notarization with keychain profile: $NOTARY_PROFILE"
    run "xcrun notarytool submit \"$DMG_OUT\" --keychain-profile \"$NOTARY_PROFILE\" --team-id \"$TEAM_ID\" --wait"
  elif [[ -n "${APPLE_ID}" && -n "${APP_PASSWORD}" ]]; then
    log "Submitting for notarization with Apple ID"
    run "xcrun notarytool submit \"$DMG_OUT\" --apple-id \"$APPLE_ID\" --team-id \"$TEAM_ID\" --password \"$APP_PASSWORD\" --wait"
  else
    log "Notarization skipped (no NOTARY_PROFILE or APPLE_ID/APP_PASSWORD provided)"
    return 0
  fi

  # 8) Staple
  log "Stapling tickets"
  run "xcrun stapler staple \"$APP_PATH\""
  run "xcrun stapler staple \"$DMG_OUT\""

  log "✅ Signed and notarized: $DMG_OUT"
}

main "$@"


