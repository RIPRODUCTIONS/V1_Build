/* eslint-disable */
// Strip extended attributes early to avoid codesign "resource fork" error
const { execFileSync } = require("child_process");
const path = require("path");

exports.default = async function beforeSign(context) {
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





