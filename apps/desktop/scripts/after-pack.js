/* eslint-disable */
// Remove extended attributes from packaged app before signing
const { execFileSync } = require("child_process");
const path = require("path");

exports.default = async function afterPack(context) {
  if (context.electronPlatformName !== "darwin") return;
  const appPath = path.join(
    context.appOutDir,
    `${context.packager.appInfo.productFilename}.app`,
  );
  try {
    execFileSync("xattr", ["-cr", appPath], { stdio: "inherit" });
  } catch (e) {
    // ignore
  }
};





