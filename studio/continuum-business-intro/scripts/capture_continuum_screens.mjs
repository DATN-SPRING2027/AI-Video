#!/usr/bin/env node
/**
 * Captures crisp 1920x1080 real Continuum AI customer-facing product screens
 * via Brave Browser CDP (:9333) for the B2B Business Explainer Video.
 * Zero credentials hardcoded or logged.
 */
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { createRequire } from "node:module";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const PROJECT_ROOT = path.resolve(__dirname, "..");
const CREATE_VIDEO_ROOT = path.resolve(PROJECT_ROOT, "../..");
const WORKSPACE_ROOT = path.resolve(CREATE_VIDEO_ROOT, "..");
const OUT_DIR = path.join(PROJECT_ROOT, "assets/ui");

const requireFromCV = createRequire(path.join(CREATE_VIDEO_ROOT, "package.json"));
const { chromium } = requireFromCV("playwright");

const CDP_URL = process.env.BRAVE_CDP_URL || "http://127.0.0.1:9333";
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

function loadLocalDemoAccount(preferredEmail = process.env.DEMO_ACCOUNT_EMAIL) {
  const accountsFile = path.join(WORKSPACE_ROOT, ".agents/local-test-accounts.md");
  const lines = fs.readFileSync(accountsFile, "utf8").split(/\r?\n/);
  let fallback = null;
  for (const line of lines) {
    const match = line.match(/\|\s*`([^`]+@[^`]+)`\s*\|\s*`([^`]+)`\s*\|/);
    if (!match) continue;
    if (preferredEmail && match[1] === preferredEmail) {
      return { email: match[1], password: match[2] };
    }
    if (!fallback && /manager/i.test(line)) {
      fallback = { email: match[1], password: match[2] };
    }
  }
  if (fallback) return fallback;
  throw new Error("Matching demo account not found in local-test-accounts.md");
}

async function ensureSignedIn(page) {
  await page.goto("http://localhost:3000/en/signin", { waitUntil: "domcontentloaded", timeout: 25000 });
  await sleep(1800);
  if (page.url().includes("/signin")) {
    const { email, password } = loadLocalDemoAccount();
    const emailInput = page.locator('input[type="email"], input[name="email"]').first();
    if (await emailInput.isVisible().catch(() => false)) {
      await emailInput.fill(email);
      await page.locator('input[type="password"], input[name="password"]').first().fill(password);
      await page.locator('button[type="submit"]').first().click();
      await sleep(2200);
    }
  }
  const wsCard = page.getByText("Continue to workspace").first();
  if (await wsCard.waitFor({ state: "visible", timeout: 8000 }).then(() => true).catch(() => false)) {
    await wsCard.click();
    await page.waitForURL((u) => !u.pathname.includes("select-organization"), { timeout: 12000 }).catch(() => {});
    await page.getByText("Active members").first().waitFor({ state: "visible", timeout: 12000 }).catch(() => {});
    await sleep(1500);
  }
}

async function main() {
  fs.mkdirSync(OUT_DIR, { recursive: true });
  let browser;
  let launchedLocal = false;
  try {
    browser = await chromium.connectOverCDP(CDP_URL);
  } catch {
    browser = await chromium.launch({ headless: true });
    launchedLocal = true;
  }
  const context =
    browser.contexts()[0] || (await browser.newContext({ viewport: { width: 1920, height: 1080 } }));
  const page = await context.newPage();
  const cdp = await context.newCDPSession(page);
  await cdp.send("Emulation.setDeviceMetricsOverride", {
    width: 1920,
    height: 1080,
    deviceScaleFactor: 1,
    mobile: false,
  });

  await ensureSignedIn(page);
  await sleep(2800);
  await page.screenshot({ path: path.join(OUT_DIR, "ui-01-dashboard.png") });
  console.log("[OK] ui-01-dashboard.png ->", page.url());

  // Navigate to Organization Projects hub (populated project cards & members, zero skeletons)
  const projectsLink = page.locator('a[href*="/projects"]').first();
  if (await projectsLink.isVisible().catch(() => false)) {
    await projectsLink.click();
    await page.getByText("Continuum Frontend Portal").first().waitFor({ state: "visible", timeout: 10000 }).catch(() => {});
    await sleep(1800);
  }
  await page.screenshot({ path: path.join(OUT_DIR, "ui-02-worknotes.png") });
  console.log("[OK] ui-02-worknotes.png ->", page.url());

  // Navigate to AI Chat
  const aiChatLink = page.locator('a:has-text("AI Chat")').first();
  if (await aiChatLink.isVisible({ timeout: 3000 }).catch(() => false)) {
    await aiChatLink.click();
    await sleep(3200);
  }
  await page.screenshot({ path: path.join(OUT_DIR, "ui-03-aichat.png") });
  console.log("[OK] ui-03-aichat.png ->", page.url());

  if (launchedLocal) {
    await browser.close();
  }
  process.exit(0);
}

main().catch((err) => {
  console.error(err.message);
  process.exit(1);
});
