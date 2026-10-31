import { chromium, expect } from "@playwright/test";
import { mkdir, writeFile } from "node:fs/promises";
import path from "node:path";
import { execFileSync } from "node:child_process";

// Run a built application first. Uses an installed Playwright Chromium by default.
// REPORT_CHROMIUM_PATH / REPORT_BROWSER_ARGS support alternative Chromium builds.
const root = process.cwd();
const output = path.join(root, "docs/project-report");
const shots = path.join(output, "assets/screenshots");
await mkdir(shots, { recursive: true });
const baseURL = process.env.REPORT_BASE_URL || "http://127.0.0.1:3000";
const browser = await chromium.launch({
  headless: true,
  ...(process.env.REPORT_CHROMIUM_PATH ? { executablePath: process.env.REPORT_CHROMIUM_PATH } : {}),
  args: JSON.parse(process.env.REPORT_BROWSER_ARGS || '["--no-sandbox"]'),
});
const context = await browser.newContext({ viewport: { width: 1440, height: 1000 }, deviceScaleFactor: 1.5, reducedMotion: "reduce" });
const page = await context.newPage();
const errors = [];
page.on("pageerror", (error) => errors.push(error.message));
const results = [];
async function check(id, name, fn) {
  try {
    await fn();
    results.push({ id, name, status: "passed" });
    console.log(`PASS ${id}: ${name}`);
  } catch (error) {
    const detail = error.message.replace(/\u001b\[[0-9;]*m/g, "").slice(0, 2400);
    results.push({ id, name, status: "failed", detail });
    console.log(`FAIL ${id}: ${name}\n${detail}`);
  }
}
async function fresh() {
  await page.goto(baseURL);
  await page.evaluate(() => localStorage.clear());
  await page.reload();
  await page.waitForFunction(() => Boolean(localStorage.getItem("parkline-garage-planning")));
  await expect(page.getByRole("heading", { name: "Good morning, Reshma." })).toBeVisible();
}
async function screenshot(name, locator) {
  if (locator) await locator.screenshot({ path: path.join(shots, name), animations: "disabled" });
  else await page.screenshot({ path: path.join(shots, name), fullPage: true, animations: "disabled" });
}
try {
  await fresh();
  await check("B01", "Riverside seed inventory is 72 total, 34 occupied, 32 available and 6 reserved", async () => {
    const values = await page.locator(".metric-value").allTextContents();
    expect(values.map((v) => Number.parseInt(v))).toEqual([72, 34, 32, 6]);
    await expect(page.locator(".bay-grid .bay")).toHaveCount(24);
  });
  await screenshot("01-overview.png");
  await check("B02", "Floor selection and reserved-state filtering agree", async () => {
    await page.getByRole("tab", { name: "02" }).click();
    await page.getByLabel("Filter bay status").selectOption("reserved");
    await expect(page.locator(".bay-grid .bay")).toHaveCount(2);
  });
  await screenshot("02-floor-filter.png", page.locator(".parking-panel"));
  await check("B03", "Reserved bay click reports reservation rather than starting a session", async () => {
    await page.getByRole("button", { name: "L2-04, reserved", exact: true }).click();
    await expect(page.getByRole("status")).toContainText("L2-04 is reserved.");
    await expect(page.getByRole("dialog")).toHaveCount(0);
  });
  await page.getByLabel("Filter bay status").selectOption("all");
  await check("B04", "Unknown bay search displays an explicit empty result", async () => {
    await page.getByLabel("Find bay or registration").fill("NO-SUCH-BAY");
    await expect(page.getByText("No bays match this search.")).toBeVisible();
  });
  await fresh();
  await page.getByRole("button", { name: "New arrival" }).click();
  await page.getByLabel("Vehicle registration").fill("tn 01 aa 3042");
  await page.getByLabel("Vehicle description").fill("Green test vehicle");
  await screenshot("03-arrival-form.png", page.getByRole("dialog"));
  await check("B05", "Arrival normalizes the plate, occupies B1-01 and preserves the capacity sum", async () => {
    await page.getByRole("button", { name: "Start parking session" }).click();
    await expect(page.getByRole("status")).toContainText("TN01AA3042 checked in at B1-01.");
    await expect(page.getByRole("button", { name: "B1-01, occupied by TN01AA3042", exact: true })).toBeVisible();
    const values = await page.locator(".metric-value").allTextContents();
    expect(values.map((v) => Number.parseInt(v))).toEqual([72, 35, 31, 6]);
  });
  await screenshot("04-arrival-success.png");
  await check("B06", "Arrival state persists across a same-browser page reload", async () => {
    await page.reload();
    await expect(page.getByRole("button", { name: "B1-01, occupied by TN01AA3042", exact: true })).toBeVisible();
  });
  await check("B07", "A duplicate normalized registration is rejected without closing the arrival dialog", async () => {
    await page.getByRole("button", { name: "New arrival" }).click();
    await page.getByLabel("Vehicle registration").fill("TN01AA3042");
    await page.getByRole("button", { name: "Start parking session" }).click();
    await expect(page.getByRole("dialog").getByRole("alert")).toContainText("already has an active parking session");
  });
  await screenshot("08-duplicate-validation.png", page.getByRole("dialog"));
  await page.getByLabel("Close dialog").click();
  await page.getByRole("button", { name: "Check out", exact: true }).click();
  await page.getByLabel("Active parking session").selectOption({ label: "TN01AA3042 · B1-01 · Green test vehicle" });
  await screenshot("05-departure-form.png", page.getByRole("dialog"));
  await check("B08", "Checkout releases the selected bay and restores counts", async () => {
    await page.getByRole("button", { name: "Complete check out" }).click();
    await expect(page.getByRole("status")).toContainText("TN01AA3042 checked out from B1-01.");
    await expect(page.getByRole("button", { name: "B1-01, available", exact: true })).toBeVisible();
    expect((await page.locator(".metric-value").allTextContents()).map((v) => Number.parseInt(v))).toEqual([72, 34, 32, 6]);
  });
  await page.getByRole("button", { name: "Plan capacity" }).click();
  await page.getByLabel("Basement capacity").fill("28");
  await screenshot("06-capacity-form.png", page.getByRole("dialog"));
  await check("B09", "Capacity expansion changes total but preserves occupied and reserved counts", async () => {
    await page.getByRole("button", { name: "Save capacity" }).click();
    await expect(page.getByRole("status")).toContainText("capacity updated to 76 bays");
    expect((await page.locator(".metric-value").allTextContents()).map((v) => Number.parseInt(v))).toEqual([76, 34, 36, 6]);
  });
  await page.getByRole("button", { name: "Plan capacity" }).click();
  await check("B10", "Capacity input advertises the protected occupied-plus-reserved minimum", async () => {
    await expect(page.getByLabel("Basement capacity")).toHaveAttribute("min", "12");
    await page.getByLabel("Basement capacity").fill("11");
    expect(await page.getByLabel("Basement capacity").evaluate((el) => el.validity.rangeUnderflow)).toBe(true);
  });
  await page.getByRole("tab", { name: "Add location" }).click();
  await page.getByLabel("Location name").fill("Harbour Point");
  await page.getByLabel("Number of floors").fill("2");
  await page.getByLabel("Bays per floor").fill("15");
  await screenshot("07-new-location-form.png", page.getByRole("dialog"));
  await check("B11", "Adding Harbour Point creates independent empty inventory and persists its plan", async () => {
    await page.getByRole("button", { name: "Add location", exact: true }).click();
    expect((await page.locator(".metric-value").allTextContents()).map((v) => Number.parseInt(v))).toEqual([30, 0, 30, 0]);
    await page.reload();
    await expect(page.getByLabel("Garage location").locator("option:checked")).toHaveText("Harbour Point");
  });
  await screenshot("09-new-location-result.png");
  await check("B12", "Location switching restores independent Riverside inventory and resets the floor", async () => {
    await page.getByLabel("Garage location").selectOption("riverside");
    expect((await page.locator(".metric-value").allTextContents()).map((v) => Number.parseInt(v))).toEqual([76, 34, 36, 6]);
    await expect(page.getByRole("tab", { name: "B1" })).toHaveAttribute("aria-selected", "true");
  });
  await check("B13", "Invalid Tamil Nadu registration format displays the domain error", async () => {
    await page.getByRole("button", { name: "New arrival" }).click();
    await page.getByLabel("Vehicle registration").fill("KA01AA1234");
    await page.getByRole("button", { name: "Start parking session" }).click();
    await expect(page.getByRole("dialog").getByRole("alert")).toContainText("TN + 2 digits + 2 letters + 4 digits");
  });
  await screenshot("10-format-validation.png", page.getByRole("dialog"));
  await page.getByLabel("Close dialog").click();
  await page.getByRole("button", { name: "Plan capacity" }).click();
  await page.getByRole("tab", { name: "Add location" }).click();
  await check("B14", "Case-insensitive duplicate location names are rejected", async () => {
    await page.getByLabel("Location name").fill(" riverside centre ");
    await page.getByRole("button", { name: "Add location", exact: true }).click();
    await expect(page.getByRole("dialog").getByRole("alert")).toContainText("A location with this name already exists.");
  });
  await page.getByLabel("Close capacity manager").click();
  await fresh();
  await page.setViewportSize({ width: 390, height: 844 });
  await check("B15", "Mobile layout has no document-level horizontal overflow at 390 pixels", async () => {
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
    await expect(page.getByRole("button", { name: "New arrival", exact: true })).toBeVisible();
  });
  const mobileGeometry = await page.evaluate(() => ({ viewport: innerWidth, documentWidth: document.documentElement.scrollWidth, overflowingElements: [...document.querySelectorAll("body *")].filter((el) => el.getBoundingClientRect().right > innerWidth + 2).slice(0, 12).map((el) => ({ element: el.tagName, className: el.className, right: Math.round(el.getBoundingClientRect().right) })) }));
  await screenshot("11-mobile-overview.png");
  await check("B16", "The exercised browser workflows raise no uncaught page errors", async () => {
    expect(errors).toEqual([]);
  });
  const report = {
    recordedAt: new Date().toISOString(),
    sourceCommit: execFileSync("git", ["rev-parse", "HEAD"], { encoding: "utf8" }).trim(),
    browser: `Chromium ${browser.version()}`,
    mode: "Local production build, single isolated Chromium context; supplemental checks, not a cross-browser audit",
    desktopViewport: "1440 x 1000 CSS pixels; screenshots at 1.5 device scale",
    mobileViewport: "390 x 844 CSS pixels",
    mobileGeometry,
    results,
    uncaughtErrors: errors,
  };
  await writeFile(path.join(output, "source/browser-evidence.json"), JSON.stringify(report, null, 2) + "\n");
} finally {
  await browser.close();
}
