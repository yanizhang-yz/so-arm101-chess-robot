/*
 * App Store review-readiness checks for Kid Chess.
 *
 *   node tools/review-readiness.test.js      (or: npm run test:appstore)
 *
 * These are the App Store REJECTION CAUSES that a machine can check before you
 * ever open Xcode: offline/no-tracking (the Kids Category bar), a correct
 * privacy manifest, export-compliance flag, a valid alpha-free icon, no stray
 * data-permission prompts, and no un-gated links out of the app. Passing here
 * does not replace Apple's human reviewer — it clears every objective hurdle so
 * the review comes down to taste, not paperwork. Each failure prints the fix.
 *
 * Pure Node, no dependencies, no Xcode required — runs anywhere (incl. CI).
 */
"use strict";
const fs = require("fs");
const path = require("path");

const ROOT = path.resolve(__dirname, "..");
const p = (...a) => path.join(ROOT, ...a);
const read = (rel) => fs.readFileSync(p(rel), "utf8");
const exists = (rel) => fs.existsSync(p(rel));

let failures = 0;
let group = "";
function section(name) { group = name; console.log(`\n${name}`); }
function check(name, cond, fix) {
  console.log((cond ? "  ok   " : "  FAIL ") + name);
  if (!cond) { failures++; if (fix) console.log("       ↳ " + fix); }
}

// ---- tiny plist helpers (the keys we check are simple top-level values) ----
function plistBool(xml, key) {
  const m = xml.match(new RegExp(`<key>${key}</key>\\s*<(true|false)\\s*/>`));
  return m ? m[1] === "true" : undefined;
}
function plistString(xml, key) {
  const m = xml.match(new RegExp(`<key>${key}</key>\\s*<string>([^<]*)</string>`));
  return m ? m[1] : undefined;
}
function plistHasKey(xml, key) {
  return new RegExp(`<key>${key}</key>`).test(xml);
}
// True when <key>K</key> is followed by an EMPTY array (<array/> or <array></array>).
function plistArrayEmpty(xml, key) {
  const m = xml.match(new RegExp(`<key>${key}</key>\\s*<array\\s*(/>|>\\s*</array>)`));
  return !!m;
}

// ---- the runtime web files the app actually ships ----
const WEB = ["webgame/index.html", "webgame/ai.js", "webgame/chess.js"];

// =====================================================================
section("1. Fully offline — no network, no tracking (Kids Category 1.3 / 5.1.4)");
// A live network call is the #1 thing that turns a "no data collected" claim
// into a rejection. Match request-making APIs, not URLs-in-comments.
const NET = [
  [/<script[^>]+src\s*=\s*["']https?:/i, "external <script src>"],
  [/<link[^>]+href\s*=\s*["']https?:/i, "external <link href>"],
  [/<img[^>]+src\s*=\s*["']https?:/i, "remote <img src>"],
  [/\bfetch\s*\(/i, "fetch()"],
  [/XMLHttpRequest/i, "XMLHttpRequest"],
  [/new\s+WebSocket/i, "WebSocket"],
  [/new\s+EventSource/i, "EventSource (SSE)"],
  [/navigator\.sendBeacon/i, "sendBeacon"],
  [/import\s*\(\s*["']https?:/i, "dynamic import from URL"],
];
for (const rel of WEB) {
  const src = read(rel);
  const hits = NET.filter(([re]) => re.test(src)).map(([, label]) => label);
  check(`${rel} makes no network calls`, hits.length === 0,
    `remove/replace: ${hits.join(", ")} — a kids app must run fully offline`);
}

// =====================================================================
section("2. No third-party analytics / ad / tracking SDKs");
const pkg = JSON.parse(read("package.json"));
const deps = { ...pkg.dependencies, ...pkg.devDependencies };
const ALLOWED = /^@capacitor\/(core|ios|cli)$/;
const badDeps = Object.keys(deps).filter((d) => !ALLOWED.test(d));
check("package.json has only Capacitor deps (no SDKs)", badDeps.length === 0,
  `unexpected deps: ${badDeps.join(", ")} — Kids apps may not include 3rd-party analytics/ads`);

const podfile = read("ios/App/Podfile");
const BAD_PODS = /Firebase|GoogleAnalytics|Google-Mobile-Ads|AdMob|FBSDK|Facebook|AppsFlyer|Amplitude|Segment|Mixpanel|Flurry|Crashlytics|Sentry|OneSignal/i;
check("Podfile pulls in no analytics/ad pods", !BAD_PODS.test(podfile),
  "remove the SDK pod — Kids Category forbids third-party analytics & advertising");

// =====================================================================
section("3. Privacy manifest (PrivacyInfo.xcprivacy) — required for new apps");
const MAN = "ios/App/App/PrivacyInfo.xcprivacy";
check("privacy manifest file exists", exists(MAN),
  "add ios/App/App/PrivacyInfo.xcprivacy");
if (exists(MAN)) {
  const man = read(MAN);
  check("declares NSPrivacyTracking = false", plistBool(man, "NSPrivacyTracking") === false,
    "kids apps must not track");
  check("declares an EMPTY NSPrivacyTrackingDomains", plistArrayEmpty(man, "NSPrivacyTrackingDomains"),
    "no tracking domains allowed");
  check("declares NSPrivacyCollectedDataTypes = [] (no data collected)",
    plistArrayEmpty(man, "NSPrivacyCollectedDataTypes"),
    "leave the collected-data array empty — the app stores nothing");
  // Registered in the build, else Xcode won't bundle it and App Store Connect complains.
  const pbx = read("ios/App/App.xcodeproj/project.pbxproj");
  check("privacy manifest is registered in the App target", /PrivacyInfo\.xcprivacy/.test(pbx),
    "run tools/xcodeproj-ruby.sh tools/add_privacy_manifest.rb");
}

// =====================================================================
section("4. Info.plist — export compliance, iPad support, no stray permissions");
const INFO = read("ios/App/App/Info.plist");
check("ITSAppUsesNonExemptEncryption = false (no export-compliance stall)",
  plistBool(INFO, "ITSAppUsesNonExemptEncryption") === false,
  "add <key>ITSAppUsesNonExemptEncryption</key><false/> so uploads don't hang on the encryption question");
const displayName = plistString(INFO, "CFBundleDisplayName");
check("has a real display name (not 'App')", !!displayName && displayName !== "App" && displayName !== "$(PRODUCT_NAME)",
  "set CFBundleDisplayName to the store name, e.g. Kid Chess");
check("declares iPad orientations", plistHasKey(INFO, "UISupportedInterfaceOrientations~ipad"),
  "iPad build needs UISupportedInterfaceOrientations~ipad");
// ATS must not be globally weakened — an offline app never needs arbitrary loads.
check("does NOT weaken App Transport Security", plistBool(INFO, "NSAllowsArbitraryLoads") !== true,
  "remove NSAllowsArbitraryLoads=true — reviewers flag it and the app is offline anyway");
// A chess game needs no sensitive-data permissions; requesting one that's unused = rejection.
const FORBIDDEN_USAGE = [
  "NSCameraUsageDescription", "NSMicrophoneUsageDescription", "NSLocationWhenInUseUsageDescription",
  "NSLocationAlwaysAndWhenInUseUsageDescription", "NSContactsUsageDescription",
  "NSPhotoLibraryUsageDescription", "NSPhotoLibraryAddUsageDescription", "NSBluetoothAlwaysUsageDescription",
  "NSUserTrackingUsageDescription", "NSHealthShareUsageDescription", "NSCalendarsUsageDescription",
  "NSRemindersUsageDescription", "NSMotionUsageDescription", "NSSpeechRecognitionUsageDescription",
];
const present = FORBIDDEN_USAGE.filter((k) => plistHasKey(INFO, k));
check("requests no camera/mic/location/tracking/etc. permissions", present.length === 0,
  `remove unused permission strings: ${present.join(", ")} — a chess game must not ask for them`);

// =====================================================================
section("5. App icon — present, 1024×1024, and NO alpha channel");
const ICON = "ios/App/App/Assets.xcassets/AppIcon.appiconset/AppIcon-512@2x.png";
check("marketing icon exists", exists(ICON), "generate it: npm run ios:icons");
if (exists(ICON)) {
  const buf = fs.readFileSync(p(ICON));
  const isPng = buf.slice(0, 8).equals(Buffer.from([0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a]));
  check("icon is a PNG", isPng);
  if (isPng) {
    // IHDR: width(4) height(4) bitdepth(1) colortype(1) starting at byte 16.
    const width = buf.readUInt32BE(16);
    const height = buf.readUInt32BE(20);
    const colorType = buf.readUInt8(25);
    check("icon is 1024×1024", width === 1024 && height === 1024, `got ${width}×${height}`);
    // colorType 4 (gray+alpha) or 6 (RGBA) carry alpha — Apple rejects those for the marketing icon.
    check("icon has NO alpha channel", colorType !== 4 && colorType !== 6,
      "re-export as flat RGB (npm run ios:icons does this) — Apple rejects icons with transparency");
  }
}

// =====================================================================
section("6. No un-gated links out of the app (Kids Category needs a parental gate)");
// Any way for a 4-year-old to leave the app (a link, a store page, a share
// sheet) must sit behind a parental gate. The simplest pass: have none.
const html = read("webgame/index.html");
const EXITS = [
  [/<a\b[^>]*href\s*=\s*["']https?:/i, "external <a href> link"],
  [/target\s*=\s*["']_blank["']/i, 'target="_blank"'],
  [/window\.open\s*\(/i, "window.open()"],
  [/location\.(href|assign|replace)\s*=?\s*\(?\s*["']https?:/i, "location -> external URL"],
];
const exitsFound = EXITS.filter(([re]) => re.test(html)).map(([, l]) => l);
check("the game never links out to the web", exitsFound.length === 0,
  `found: ${exitsFound.join(", ")} — either remove it or put it behind a parental gate (math question)`);

// =====================================================================
section("7. Store paperwork present");
check("privacy policy exists (Apple requires a URL for kids apps)",
  exists("docs/app-store/privacy-policy.md"),
  "write docs/app-store/privacy-policy.md and host it (GitHub Pages)");
check("submission checklist exists", exists("docs/app-store/README.md"),
  "the human-only steps (Developer Program, App Store Connect) live here");

// =====================================================================
section("8. Bundle configuration sanity");
const pbx = read("ios/App/App.xcodeproj/project.pbxproj");
const bundleId = (pbx.match(/PRODUCT_BUNDLE_IDENTIFIER = ([^;]+);/) || [])[1];
check("bundle id is set and not a placeholder",
  !!bundleId && /^[A-Za-z0-9.-]+\.[A-Za-z0-9.-]+/.test(bundleId) &&
    !/example|ionic\.starter|com\.getcapacitor/i.test(bundleId),
  `bundle id is ${bundleId} — set a real reverse-DNS id you own`);
check("iPad is in the device family", /TARGETED_DEVICE_FAMILY = "?[^";]*2/.test(pbx),
  'TARGETED_DEVICE_FAMILY must include 2 (iPad)');
const cfg = JSON.parse(read("capacitor.config.json"));
check("capacitor appId matches the bundle id", cfg.appId === (bundleId || "").trim(),
  `capacitor.config.json appId (${cfg.appId}) should equal ${bundleId}`);
check("capacitor webDir points at the game", cfg.webDir === "webgame" && exists("webgame/index.html"));

// =====================================================================
console.log(failures ? `\n${failures} CHECK(S) FAILED — fix the ↳ items above` :
  "\n✅ all review-readiness checks passed");
process.exit(failures ? 1 : 0);
