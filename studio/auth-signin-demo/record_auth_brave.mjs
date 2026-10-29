#!/usr/bin/env node
/**
 * Automated Brave Browser Controller & Interaction Recorder for Continuum AI Auth Demo
 *
 * Connects to the user's live Brave Browser via CDP (http://127.0.0.1:9222) opened by
 * `start-brave-studio.bat`, drives:
 *   Flow A: Standard Email + Password Sign-In
 *   Flow B: "Continue with Google" Real OAuth Sign-In (using Brave's signed-in Google session)
 *
 * Outputs:
 *   - Raw 1920x1080 screenshots & frame sequence / MP4 video in `./captures/`
 *   - Exact cursor & click coordinates timeline `./captures/interactions.json` (zero secrets logged!)
 */

import fs from "node:fs";
import path from "node:path";
import { spawn } from "node:child_process";
import { fileURLToPath } from "node:url";
import { createRequire } from "node:module";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const CREATE_VIDEO_ROOT = path.resolve(__dirname, "../..");
const WORKSPACE_ROOT = path.resolve(CREATE_VIDEO_ROOT, "..");
const requireFromCV = createRequire(path.join(CREATE_VIDEO_ROOT, "package.json"));
const { chromium } = requireFromCV("playwright");

const CDP_URL = process.env.BRAVE_CDP_URL || "http://127.0.0.1:9333";
const APP_SIGNIN_URL = process.env.APP_SIGNIN_URL || "http://localhost:3000/en/signin";
const OUT_DIR = path.join(__dirname, "captures");
const FRAMES_DIR = path.join(OUT_DIR, "frames");

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

/**
 * Reads local dev test account from `.agents/local-test-accounts.md` at runtime
 * without ever hardcoding or logging passwords.
 */
function loadLocalDemoAccount(preferredEmail = "manager@continuum.ai") {
  if (process.env.DEMO_EMAIL && process.env.DEMO_PASSWORD) {
    return { email: process.env.DEMO_EMAIL, password: process.env.DEMO_PASSWORD };
  }
  const accountsFile = path.join(WORKSPACE_ROOT, ".agents/local-test-accounts.md");
  if (!fs.existsSync(accountsFile)) {
    throw new Error("Missing .agents/local-test-accounts.md and DEMO_EMAIL/DEMO_PASSWORD not set.");
  }
  const lines = fs.readFileSync(accountsFile, "utf8").split(/\r?\n/);
  for (const line of lines) {
    const match = line.match(/\|\s*`([^`]+@[^`]+)`\s*\|\s*`([^`]+)`\s*\|/);
    if (match && match[1] === preferredEmail) {
      return { email: match[1], password: match[2] };
    }
  }
  throw new Error(`Account ${preferredEmail} not found in local-test-accounts.md`);
}

async function getCenterBox(locator) {
  const box = await locator.boundingBox();
  if (!box) return { x: 960, y: 540, width: 0, height: 0 };
  return {
    x: Math.round(box.x + box.width / 2),
    y: Math.round(box.y + box.height / 2),
    width: Math.round(box.width),
    height: Math.round(box.height),
  };
}

async function smoothMoveMouse(page, from, to, steps = 22) {
  for (let i = 1; i <= steps; i++) {
    const t = i / steps;
    const ease = t < 0.5 ? 2 * t * t : 1 - Math.pow(-2 * t + 2, 2) / 2;
    const arcY = Math.sin(t * Math.PI) * -18;
    const x = from.x + (to.x - from.x) * ease;
    const y = from.y + (to.y - from.y) * ease + arcY;
    await page.mouse.move(x, y);
    await sleep(14);
  }
  return { x: to.x, y: to.y };
}

async function startCdpRecorder(page, tag) {
  const tagFramesDir = path.join(FRAMES_DIR, tag);
  fs.rmSync(tagFramesDir, { recursive: true, force: true });
  fs.mkdirSync(tagFramesDir, { recursive: true });

  const client = await page.context().newCDPSession(page);
  await client.send("Emulation.setDeviceMetricsOverride", {
    width: 1920,
    height: 1080,
    deviceScaleFactor: 1,
    mobile: false,
  });

  const frameMeta = [];
  const t0 = Date.now();
  client.on("Page.screencastFrame", async (event) => {
    const idx = String(frameMeta.length).padStart(5, "0");
    const file = path.join(tagFramesDir, `frame_${idx}.jpg`);
    fs.writeFileSync(file, Buffer.from(event.data, "base64"));
    frameMeta.push({ index: frameMeta.length, elapsedMs: Date.now() - t0, file: `frames/${tag}/frame_${idx}.jpg` });
    try {
      await client.send("Page.screencastFrameAck", { sessionId: event.sessionId });
    } catch {
      // session closed
    }
  });

  await client.send("Page.startScreencast", {
    format: "jpeg",
    quality: 94,
    maxWidth: 1920,
    maxHeight: 1080,
    everyNthFrame: 1,
  });

  return {
    t0,
    async stopAndEncode(outMp4Path) {
      try {
        await client.send("Page.stopScreencast");
        await client.detach();
      } catch {
        // ignore detach errors on navigation
      }
      if (frameMeta.length < 2) return { frameCount: frameMeta.length, video: null };
      const totalSec = Math.max(0.5, (frameMeta[frameMeta.length - 1].elapsedMs - frameMeta[0].elapsedMs) / 1000);
      const effectiveFps = Math.max(5, Math.min(60, +(frameMeta.length / totalSec).toFixed(2)));
      await new Promise((resolve, reject) => {
        const ff = spawn("ffmpeg", [
          "-y",
          "-framerate", String(effectiveFps),
          "-i", path.join(tagFramesDir, "frame_%05d.jpg"),
          "-vf", "fps=30,scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2",
          "-c:v", "libx264",
          "-preset", "fast",
          "-crf", "18",
          "-pix_fmt", "yuv420p",
          outMp4Path,
        ], { stdio: "ignore" });
        ff.on("close", (code) => (code === 0 ? resolve() : reject(new Error(`ffmpeg exited with ${code}`))));
      });
      return { frameCount: frameMeta.length, effectiveFps, video: outMp4Path };
    },
  };
}

async function main() {
  const mode = process.argv[2] || "both"; // "email" | "google" | "both" | "check"
  fs.mkdirSync(OUT_DIR, { recursive: true });

  console.log(`Connecting to Brave Browser over CDP at ${CDP_URL} ...`);
  const browser = await chromium.connectOverCDP(CDP_URL);
  const context = browser.contexts()[0];
  if (!context) {
    throw new Error("No browser context found in Brave. Please run start-brave-studio.bat first.");
  }

  if (mode === "check") {
    console.log(`Connected to Brave successfully! Open pages: ${context.pages().length}`);
    process.exit(0);
  }

  const events = [];
  const page = await context.newPage();
  let cursor = { x: 960, y: 540 };

  if (mode === "email" || mode === "both") {
    console.log("Recording Flow A: Email & Password Sign-In ...");
    await context.clearCookies({ domain: "localhost" });
    await page.goto(APP_SIGNIN_URL, { waitUntil: "networkidle" });
    await sleep(800);

    const rec = await startCdpRecorder(page, "flow-email");
    const mark = (type, label, box) =>
      events.push({ flow: "email", type, label, tMs: Date.now() - rec.t0, ...box });

    await page.screenshot({ path: path.join(OUT_DIR, "01-signin-initial.png") });
    const { email, password } = loadLocalDemoAccount("manager@continuum.ai");

    const emailInput = page.locator("#signin-email");
    const emailBox = await getCenterBox(emailInput);
    cursor = await smoothMoveMouse(page, cursor, emailBox);
    await page.mouse.click(emailBox.x, emailBox.y);
    mark("click", "email-input", emailBox);
    await sleep(250);

    mark("typing-start", "email-input", emailBox);
    await page.keyboard.type(email, { delay: 55 });
    mark("typing-end", "email-input", emailBox);
    await sleep(400);

    const passInput = page.locator("#signin-password");
    const passBox = await getCenterBox(passInput);
    cursor = await smoothMoveMouse(page, cursor, passBox);
    await page.mouse.click(passBox.x, passBox.y);
    mark("click", "password-input", passBox);
    await sleep(250);

    mark("typing-start", "password-input", passBox);
    await page.keyboard.type(password, { delay: 50 });
    mark("typing-end", "password-input", passBox);
    await sleep(450);

    const submitBtn = page.locator('form button[type="submit"]').first();
    const submitBox = await getCenterBox(submitBtn);
    cursor = await smoothMoveMouse(page, cursor, submitBox);
    mark("click", "signin-submit", submitBox);
    await page.mouse.click(submitBox.x, submitBox.y);

    await sleep(1200);
    // Handle optional multi-organization selector if 409 ORGANIZATION_SELECTION_REQUIRED occurs
    const orgSelect = page.locator("#signin-organization");
    if (await orgSelect.isVisible({ timeout: 1500 }).catch(() => false)) {
      const selBox = await getCenterBox(orgSelect);
      cursor = await smoothMoveMouse(page, cursor, selBox);
      mark("click", "signin-organization-select", selBox);
      const opts = await orgSelect.locator("option").allTextContents();
      if (opts.length > 1) {
        await orgSelect.selectOption({ index: 1 });
        await sleep(500);
        const submitBox2 = await getCenterBox(submitBtn);
        cursor = await smoothMoveMouse(page, cursor, submitBox2);
        mark("click", "signin-submit-with-org", submitBox2);
        await page.mouse.click(submitBox2.x, submitBox2.y);
      }
    }

    await page.waitForURL((u) => !u.pathname.endsWith("/signin"), { timeout: 12000 }).catch(() => {});
    await sleep(1400);
    await page.screenshot({ path: path.join(OUT_DIR, "02-signin-select-org.png") });

    // If landed on /select-organization, click the first Organization card to enter Dashboard!
    const orgCardBtn = page.locator('section[aria-labelledby="organization-list-title"] ul li button').first();
    if (await orgCardBtn.isVisible({ timeout: 2500 }).catch(() => false)) {
      const cardBox = await getCenterBox(orgCardBtn);
      cursor = await smoothMoveMouse(page, cursor, cardBox);
      await sleep(300);
      mark("click", "select-organization-card", cardBox);
      await page.mouse.click(cardBox.x, cardBox.y);
      await page.waitForURL((u) => !u.pathname.includes("select-organization"), { timeout: 10000 }).catch(() => {});
      await sleep(1800);
    }

    await page.screenshot({ path: path.join(OUT_DIR, "02b-workspace-entered.png") });
    mark("complete", "email-authenticated", { x: cursor.x, y: cursor.y, width: 1920, height: 1080 });

    const outMp4 = path.join(OUT_DIR, "flow-a-email-signin.mp4");
    const res = await rec.stopAndEncode(outMp4);
    console.log("Flow A saved:", res);
  }

  if (mode === "google" || mode === "both") {
    console.log("Recording Flow B: Continue with Google OAuth Sign-In ...");
    await context.clearCookies({ domain: "localhost" });
    await page.goto(APP_SIGNIN_URL, { waitUntil: "networkidle" });
    await sleep(900);

    const rec = await startCdpRecorder(page, "flow-google");
    const mark = (type, label, box) =>
      events.push({ flow: "google", type, label, tMs: Date.now() - rec.t0, ...box });

    const googleBtn = page.locator('form[action="/api/auth/google"] button[type="submit"]');
    const googleBox = await getCenterBox(googleBtn);
    cursor = await smoothMoveMouse(page, cursor, googleBox);
    await sleep(300);
    mark("click", "continue-with-google", googleBox);
    await page.mouse.click(googleBox.x, googleBox.y);

    // Wait for Google Account Chooser or instant callback redirect
    await page.waitForLoadState("domcontentloaded").catch(() => {});
    await sleep(1800);
    await page.screenshot({ path: path.join(OUT_DIR, "03-google-oauth-step.png") });

    if (page.url().includes("accounts.google.com")) {
      const firstAccount = page.locator('[data-identifier], li [ role="link" ]').first();
      if (await firstAccount.isVisible({ timeout: 5000 }).catch(() => false)) {
        const accBox = await getCenterBox(firstAccount);
        cursor = await smoothMoveMouse(page, cursor, accBox);
        mark("click", "google-account-choice", accBox);
        await firstAccount.click();
      }
      // Handle optional Continue/Consent button on Google screen
      await sleep(1800);
      if (page.url().includes("accounts.google.com")) {
        const continueBtn = page.getByRole("button", { name: /continue|tiếp tục|allow|cho phép/i }).first();
        if (await continueBtn.isVisible({ timeout: 3000 }).catch(() => false)) {
          const cBox = await getCenterBox(continueBtn);
          cursor = await smoothMoveMouse(page, cursor, cBox);
          mark("click", "google-consent-continue", cBox);
          await continueBtn.click();
        }
      }
    }

    await page.waitForURL((u) => u.hostname === "localhost" && !u.pathname.endsWith("/signin"), { timeout: 15000 }).catch(() => {});
    await sleep(2000);
    await page.screenshot({ path: path.join(OUT_DIR, "04-google-signin-result.png") });
    mark("complete", "google-oauth-finished", { x: cursor.x, y: cursor.y, width: 1920, height: 1080 });

    const outMp4 = path.join(OUT_DIR, "flow-b-google-signin.mp4");
    const res = await rec.stopAndEncode(outMp4);
    console.log("Flow B saved:", res);
  }

  fs.writeFileSync(path.join(OUT_DIR, "interactions.json"), JSON.stringify({ recordedAt: new Date().toISOString(), events }, null, 2));
  await page.close().catch(() => {});
  console.log("All recordings & interactions.json saved to:", OUT_DIR);
  process.exit(0);
}

main().catch((err) => {
  console.error("Recorder error:", err.message);
  process.exit(1);
});
