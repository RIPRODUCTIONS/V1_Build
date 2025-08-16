/* eslint-disable */
// Remove extended attributes (resource forks) from app bundle before signing/notarization
// Fixes: codesign error "resource fork, Finder information, or similar detritus not allowed"
const { execFileSync } = require("child_process");
const path = require("path");

exports.default = async function afterSign(context) {
  const appPath = context.appOutDir;
  const { electronPlatformName } = context;
  if (electronPlatformName !== "darwin") return;
  try {
    execFileSync("xattr", ["-cr", appPath], { stdio: "inherit" });
  } catch (e) {
    // non-fatal
  }
};





