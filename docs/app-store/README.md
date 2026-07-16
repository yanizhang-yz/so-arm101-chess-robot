# Putting Kid Chess on the App Store 🍎

This is the start-to-finish guide for turning the Kid Chess web game into a real
iPad app your daughter — and any other kid — can download from the App Store.
It assumes **no prior app-development experience**. Read it top to bottom once
before you start; it takes an afternoon plus Apple's review wait.

> **What's already done for you.** The whole app is built and configured. A test
> suite (`npm run test:appstore`) checks the parts that make Apple *reject*
> apps, and they all pass. What's left is the part only *you* can do, because it
> needs your real identity and a payment method: enrolling as an Apple developer
> and clicking the final buttons. Those steps are in **Part 3**.

---

## The big picture (how a web game becomes an iPad app)

Your game is a folder of HTML/JavaScript (`webgame/`). We wrapped it with a tool
called **[Capacitor](https://capacitorjs.com/)**, which puts the game inside a
tiny native iPad app — essentially a full-screen, private web view with no
address bar, no browser buttons, and no internet. Apple sees a normal native
app; your daughter sees the game.

```
webgame/  ──(Capacitor)──►  ios/  ──(Xcode)──►  Kid Chess.app  ──►  App Store
 the game                  native project      the built app        review
```

Nothing about the game logic changed. You still double-click `webgame/index.html`
to play in a browser; the iPad app runs the exact same files.

---

## Will it pass review? What we already handled

Apple's **Kids Category** (ages 4+) is the strictest part of the store. The good
news: your game already meets the hardest bar because it **collects no data and
uses no network**. Here's each common rejection cause and how it's covered.

| Apple rejection cause | Status | Where |
|---|---|---|
| Third-party analytics / ads in a kids app | ✅ none | no SDKs; `test:appstore` §2 |
| Collecting kids' data without consent | ✅ collects nothing | privacy manifest §3 |
| Missing privacy manifest (`PrivacyInfo.xcprivacy`) | ✅ added | `ios/App/App/PrivacyInfo.xcprivacy` |
| Un-gated links / purchases leaving the app | ✅ none exist | `test:appstore` §6 |
| Export-compliance upload stall | ✅ flag set | `ITSAppUsesNonExemptEncryption=false` |
| Missing / transparent app icon | ✅ 1024², no alpha | `test:appstore` §5 |
| Requesting camera/mic/location it never uses | ✅ requests none | `test:appstore` §4 |
| No privacy policy URL (required for kids) | ✅ written | [privacy-policy.md](privacy-policy.md) |

Run the checker any time:

```bash
npm run test:appstore     # the review-readiness suite (no Xcode needed)
npm test                  # that, plus the game's own AI tests
```

**A promise this suite can't make:** it clears every *objective* hurdle. A human
at Apple still opens the app and judges whether it looks finished and works.
Ours does — but that's why Part 2 has you run it on a real iPad first.

---

## Part 1 — What you need before you start

1. **A Mac** (you have one) with **Xcode** installed (you have 26.0.1). ✅
2. **An Apple ID** — the same one you use on your iPhone is fine.
3. **The Apple Developer Program — $99/year.** This is Apple's charge, not ours.
   You cannot publish to the App Store without it. Enroll at
   <https://developer.apple.com/programs/enroll/>. Approval is usually minutes to
   a day. *(You only need this for Part 3. You can do all of Part 2 for free.)*
4. **An iPad** to test on (strongly recommended — the simulator can't fully
   test the spoken hints).

---

## Part 2 — Build it and try it (free, no Developer Program yet)

Everything here works with just your free Apple ID.

### 2a. Refresh the app from the game, then open Xcode

Any time you change the game, copy it into the native app and open Xcode:

```bash
npm install            # first time only — installs Capacitor
npm run cap:sync       # copies webgame/ into the iOS app
npm run cap:open       # opens the project in Xcode
```

> If `cap:sync` ever errors about `pod` and text encoding, run it with a UTF-8
> locale: `LANG=en_US.UTF-8 LC_ALL=en_US.UTF-8 npm run cap:sync`. (A known
> CocoaPods + Ruby 4 quirk on newer Macs.)

### 2b. Set your signing team (one-time)

In Xcode: click the blue **App** project on the left → the **App** target →
**Signing & Capabilities** tab. Check **Automatically manage signing** and pick
your name under **Team**. (Your free Apple ID appears here once you've added it
in Xcode ▸ Settings ▸ Accounts.)

### 2c. Run it on the simulator, then your iPad

- **Simulator:** pick an **iPad** from the device menu at the top, press ▶︎. The
  game launches full-screen.
- **Your iPad:** plug it in, pick it from the device menu, press ▶︎. The first
  time, the iPad asks you to trust the developer (Settings ▸ General ▸ VPN &
  Device Management). Free Apple-ID installs expire after 7 days — that's normal;
  it's just for testing. Part 3 makes it permanent.

### 2d. The on-device checklist (do this before submitting)

- [ ] The board and pieces fit the screen in **portrait and landscape**.
- [ ] **Tap a piece → legal squares light up → tap to move.** Pieces glide.
- [ ] **Spoken hints talk.** iPad WKWebView needs a tap before it will speak, and
      the game already speaks on taps — confirm you hear a voice. If silent,
      flip the iPad's **Silent switch** off and turn the volume up.
- [ ] **Music/sound effects** play, and the mute button silences them.
- [ ] Win a game (beat the Chick) → **confetti**. Trigger the end-of-game
      **spoken mini-lesson**.
- [ ] Nothing is cut off under the rounded corners / home indicator.

---

## Part 3 — Publish it (needs the Developer Program)

### 3a. Create the app record in App Store Connect

1. Go to <https://appstoreconnect.apple.com> → **My Apps** → **＋** → **New App**.
2. Platform **iOS**; Name **Kid Chess** (must be unique store-wide — if taken,
   try "Kid Chess — Horsey" or similar); Primary language **English**.
3. **Bundle ID:** pick `com.yanizhang.kidchess` (it's already set in the Xcode
   project). If it's not in the dropdown, create it first at
   <https://developer.apple.com/account/resources/identifiers> with that exact id.
4. SKU: anything, e.g. `kidchess001`.

### 3b. Fill in the App Store listing

- **Category:** Primary **Games**; you'll also set the age band next.
- **Age rating:** answer the questionnaire honestly — for Kid Chess everything is
  "None," which yields **4+**. When asked **"Made for Kids?"**, say yes and pick
  the **Ages 5 and under** (or 6–8) band. This is what places it in the Kids
  Category and enables the extra kid protections.
- **Privacy Policy URL (required):** the repo is public and this file is already
  a valid public URL that renders nicely — paste
  `https://github.com/yanizhang-yz/chess-robot/blob/main/docs/app-store/privacy-policy.md`
  into App Store Connect. (The game itself is also live via GitHub Pages at
  `https://yanizhang-yz.github.io/chess-robot/`.)
- **App Privacy ("nutrition label"):** choose **Data Not Collected**. That single
  choice matches the privacy manifest and is the whole reason review is easy.
- **Price:** Free.
- **Screenshots:** you need **iPad 13"** screenshots. Easiest way: run the app in
  the iPad simulator (Part 2c), play a bit, and press **⌘S** in the simulator to
  save screenshots — or File ▸ Save Screen. Grab 3–5: the world-picker, a game in
  progress with squares lit up, the confetti win, the treasure tray.

### 3c. Upload the build

In Xcode: device menu → **Any iOS Device (arm64)** → menu bar **Product ▸
Archive**. When the Organizer opens, **Distribute App ▸ App Store Connect ▸
Upload**. Because `ITSAppUsesNonExemptEncryption` is already set, it won't stop
to ask about encryption. The build appears in App Store Connect after a few
minutes of processing.

### 3d. Submit for review

Back in App Store Connect: attach the uploaded build to the version, confirm the
age rating and the **Data Not Collected** label, then **Add for Review ▸ Submit**.
Kids-category reviews sometimes take a little longer than usual. If anything
comes back, it'll be a specific note — fix it and resubmit; the paperwork above
is already handled.

---

## Keeping the browser version alive

Making an iPad app doesn't retire the free web version. `webgame/index.html`
still opens in any browser, and GitHub Pages still serves it. The App Store build
is just the same game in a nicer wrapper for kids who live on an iPad.

## If you want to change things later

- **App name / icon color / bundle id:** name & id in `capacitor.config.json`
  and Xcode's Signing tab; icon in `tools/make_app_art.py` → `npm run ios:icons`.
- **New game version to the store:** bump `MARKETING_VERSION` in Xcode (e.g.
  1.0 → 1.1), `npm run cap:sync`, then re-Archive and upload.
- Always re-run `npm run test:appstore` before you upload.
