import { expect, test } from "@playwright/test";

test("switches between the configured garage locations", async ({ page }) => {
  await page.goto("/");
  const location = page.getByLabel("Garage location");

  await location.selectOption("marina-velachery");
  await expect(location).toHaveValue("marina-velachery");
  await location.selectOption("vr-anna-nagar");
  await expect(location).toHaveValue("vr-anna-nagar");
  await location.selectOption("phoenix-omr");
  await expect(location).toHaveValue("phoenix-omr");
});

test("adds a location, edits floor capacity, and persists the plan", async ({ page }) => {
  await page.goto("/");
  await page.getByRole("button", { name: "Plan capacity" }).click();
  await page.getByRole("tab", { name: "Add location" }).click();
  await page.getByLabel("Location name").fill("Harbour Point");
  await page.getByLabel("Number of floors").fill("2");
  await page.getByLabel("Bays per floor").fill("15");
  await page.getByRole("button", { name: "Add location" }).click();

  await expect(page.getByRole("combobox", { name: "Garage location" })).toHaveValue(/location-/);
  await expect(page.getByText("30 bays", { exact: false }).first()).toBeVisible();
  await page.getByRole("button", { name: "Plan capacity" }).click();
  await page.getByLabel("Ground floor capacity").fill("18");
  await page.getByRole("button", { name: "Save capacity" }).click();
  await expect(page.getByRole("status")).toContainText("Harbour Point capacity updated to 33 bays.");

  await page.reload();
  await expect(page.getByRole("combobox", { name: "Garage location" })).toHaveValue(/location-/);
  await page.getByRole("button", { name: "Plan capacity" }).click();
  await expect(page.getByLabel("Ground floor capacity")).toHaveValue("18");
});

test("operator checks a vehicle in and back out", async ({ page }) => {
  await page.goto("/");

  await page.getByRole("button", { name: "New arrival" }).click();
  await page.getByLabel("Vehicle registration").fill("TN01AA3042");
  await page.getByLabel("Vehicle description").fill("Green test vehicle");
  await page.getByRole("button", { name: "Start parking session" }).click();

  await expect(page.getByRole("status")).toContainText("TN01AA3042 checked in at B1-01.");
  await expect(page.getByRole("button", { name: "B1-01, occupied by TN01AA3042" })).toBeVisible();

  await page.getByRole("button", { name: "Check out", exact: true }).click();
  await page.getByLabel("Active parking session").selectOption({
    label: "TN01AA3042 · B1-01 · Green test vehicle",
  });
  await page.getByRole("button", { name: "Complete check out" }).click();

  await expect(page.getByRole("status")).toContainText("TN01AA3042 checked out from B1-01.");
  await expect(page.getByRole("button", { name: "B1-01, available" })).toBeVisible();
});
