import { describe, expect, it } from "vitest";
import { checkIn, checkOut, occupancyForLevel, resizeLevelBays } from "./parking";
import { createManagedLocation, locations } from "./parking-data";
import type { ParkingBay, ParkingSession } from "@/types/parking";

const bays: ParkingBay[] = [
  { id: "B1-01", levelId: "B1", status: "available", kind: "standard" },
  { id: "B1-02", levelId: "B1", status: "occupied", kind: "ev", plate: "TN01AB1234" },
  { id: "B1-03", levelId: "B1", status: "reserved", kind: "accessible" },
];
const sessions: ParkingSession[] = [{
  id: "s-1", bayId: "B1-02", levelId: "B1", plate: "TN01AB1234", vehicle: "Blue hatchback", startedAt: "2026-10-31T09:00:00.000Z",
}];

describe("parking operations", () => {
  it("counts occupancy without treating reservations as parked vehicles", () => {
    expect(occupancyForLevel(bays, "B1")).toEqual({ total: 3, occupied: 1, reserved: 1, available: 1, percent: 33 });
    expect(occupancyForLevel(bays, "unknown").percent).toBe(0);
  });

  it("checks a vehicle in and normalizes its registration", () => {
    const result = checkIn(bays, sessions, "B1-01", " tn 01 aa 9876 ", "Green compact", "2026-10-31T10:00:00.000Z");
    expect(result.bays[0]).toMatchObject({ status: "occupied", plate: "TN01AA9876" });
    expect(result.sessions).toHaveLength(2);
    expect(result.sessions[1].plate).toBe("TN01AA9876");
    expect(bays[0].status).toBe("available");
  });

  it("rejects a duplicate vehicle and an unavailable bay", () => {
    expect(() => checkIn(bays, sessions, "B1-01", "tn 01 ab 1234", "Car", "2026-10-31T10:00:00.000Z")).toThrow("already has an active");
    expect(() => checkIn(bays, sessions, "B1-02", "TN01CD5678", "Car", "2026-10-31T10:00:00.000Z")).toThrow("available parking bay");
  });

  it("rejects registrations outside the Tamil Nadu format", () => {
    expect(() => checkIn(bays, sessions, "B1-01", "ZZ 3042", "Car", "2026-10-31T10:00:00.000Z"))
      .toThrow("TN + 2 digits + 2 letters + 4 digits");
  });

  it("checks a vehicle out and makes its bay available", () => {
    const result = checkOut(bays, sessions, "s-1");
    expect(result.bays[1]).toMatchObject({ status: "available" });
    expect(result.bays[1].plate).toBeUndefined();
    expect(result.sessions).toHaveLength(0);
    expect(() => checkOut(bays, sessions, "missing")).toThrow("not found");
  });

  it("resizes capacity without removing occupied or reserved bays", () => {
    const expanded = resizeLevelBays(bays, "B1", 5);
    expect(expanded.filter((bay) => bay.levelId === "B1")).toHaveLength(5);
    expect(expanded.find((bay) => bay.id === "B1-02")?.status).toBe("occupied");
    const reduced = resizeLevelBays(expanded, "B1", 3);
    expect(reduced.filter((bay) => bay.levelId === "B1")).toHaveLength(3);
    expect(reduced.map((bay) => bay.id)).toContain("B1-02");
    expect(reduced.map((bay) => bay.id)).toContain("B1-03");
  });

  it("rejects capacity below occupied and reserved bays", () => {
    expect(() => resizeLevelBays(bays, "B1", 1)).toThrow("occupied or reserved");
    expect(() => resizeLevelBays(bays, "B1", 100)).toThrow("between 1 and 99");
  });
});

describe("parking locations", () => {
  it("includes the requested sites with independent, consistent sample inventory", () => {
    expect(locations.map((location) => location.name)).toEqual([
      "Riverside Centre",
      "Marina Mall, Velachery",
      "VR Mall, Anna Nagar",
      "Phoenix Mall, OMR",
    ]);
    for (const location of locations) {
      expect(location.sessions).toHaveLength(location.bays.filter((bay) => bay.status === "occupied").length);
      for (const bay of location.bays.filter((item) => item.plate)) {
        expect(bay.plate).toMatch(/^TN\d{2}[A-Z]{2}\d{4}$/);
      }
    }
    expect(locations[0].bays).not.toBe(locations[1].bays);
  });

  it("creates a location with the requested floor and bay counts", () => {
    const location = createManagedLocation(" Test Garage ", 2, 12);
    expect(location.name).toBe("Test Garage");
    expect(location.levels).toHaveLength(2);
    expect(location.bays).toHaveLength(24);
    expect(location.levels.every((level) => level.capacity === 12)).toBe(true);
    expect(location.bays.every((bay) => bay.status === "available")).toBe(true);
  });
});
