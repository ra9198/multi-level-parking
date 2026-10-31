<!-- page: app-a-types | Appendix A: SOURCE CODE -->
# APPENDIX A — SAMPLE SOURCE CODE
## A.1 Complete Domain Type Declarations

These complete declarations from `src/types/parking.ts` describe the reviewed record shapes and vocabularies. They are not a database schema or runtime validator.

```typescript
export type BayStatus = "available" | "occupied" | "reserved";
export type BayKind = "standard" | "ev" | "accessible";

export interface ParkingLevel {
  id: string;
  label: string;
  name: string;
  capacity: number;
}

export interface ParkingBay {
  id: string;
  levelId: string;
  status: BayStatus;
  kind: BayKind;
  plate?: string;
  since?: string;
}

export interface ParkingSession {
  id: string;
  bayId: string;
  levelId: string;
  plate: string;
  vehicle: string;
  startedAt: string;
}

export interface ParkingActivity {
  id: string;
  type: "arrival" | "departure" | "reservation";
  plate: string;
  bayId: string;
  time: string;
}

export interface ParkingLocation {
  id: string;
  name: string;
  levels: ParkingLevel[];
  bays: ParkingBay[];
  sessions: ParkingSession[];
  activity: ParkingActivity[];
}
```

An occupied bay's optional fields and session relationship must still be validated at runtime. Location scope is carried by the containing collection, not by a `locationId` field in every bay.

<!-- page: app-a-counts | Appendix A: SOURCE CODE -->
## A.2 Occupancy and Registration Helpers

These complete helper functions are reproduced from `src/lib/parking.ts`. Occupancy derives availability from actual bay records, while normalization supplies one accepted representation before duplicate checking. Neither helper performs network access.

```typescript
export function occupancyForLevel(bays: ParkingBay[], levelId: string) {
  const levelBays = bays.filter((bay) => bay.levelId === levelId);
  const occupied = levelBays.filter((bay) => bay.status === "occupied").length;
  const reserved = levelBays.filter((bay) => bay.status === "reserved").length;

  return {
    total: levelBays.length,
    occupied,
    reserved,
    available: levelBays.length - occupied - reserved,
    percent: levelBays.length === 0 ? 0 : Math.round((occupied / levelBays.length) * 100),
  };
}

export function normalizeTamilNaduPlate(value: string): string {
  const plate = value.replace(/[\s-]/g, "").toUpperCase();
  if (!/^TN\d{2}[A-Z]{2}\d{4}$/.test(plate)) {
    throw new Error("Use TN + 2 digits + 2 letters + 4 digits, for example TN01AA1234.");
  }
  return plate;
}
```

The zero-level branch avoids a non-finite percentage. The regular expression accepts a project-specific Tamil Nadu format only. It does not verify legal registration existence or ownership, and it does not accept every real-world vehicle-registration variant.

The distinction between status and kind is preserved because counting reads status only. A reserved accessible bay is reserved inventory; an occupied EV bay is one parked vehicle. Derived percentages should not be substituted with static trend labels elsewhere in the UI.

<!-- page: app-a-checkin | Appendix A: SOURCE CODE -->
## A.3 Complete Local Check-In Transition

The following function is reproduced from `src/lib/parking.ts`. Its returned arrays form the next local state. The dashboard is responsible for committing those arrays, generating activity and saving locally.

```typescript
export function checkIn(
  bays: ParkingBay[],
  sessions: ParkingSession[],
  bayId: string,
  plate: string,
  vehicle: string,
  startedAt: string,
): { bays: ParkingBay[]; sessions: ParkingSession[] } {
  const bay = bays.find((item) => item.id === bayId);
  const normalizedPlate = normalizeTamilNaduPlate(plate);
  if (!bay || bay.status !== "available") throw new Error("Choose an available parking bay.");
  if (sessions.some((session) => session.plate === normalizedPlate)) {
    throw new Error("This vehicle already has an active parking session.");
  }

  const session: ParkingSession = {
    id: `session-${bayId}-${Date.parse(startedAt)}`,
    bayId,
    levelId: bay.levelId,
    plate: normalizedPlate,
    vehicle: vehicle.trim() || "Vehicle",
    startedAt,
  };

  return {
    bays: bays.map((item) => item.id === bayId
      ? { ...item, status: "occupied", plate: normalizedPlate, since: startedAt }
      : item),
    sessions: [...sessions, session],
  };
}
```

The caller supplies `startedAt`; this helper does not validate its date syntax. Duplicate detection is restricted to the supplied active-session collection. UI callers scope that collection to the selected location, so this is not a global multi-garage or concurrent-operator guarantee.

<!-- page: app-a-resize | Appendix A: SOURCE CODE -->
## A.4 Complete Protected Capacity-Resizing Helper

This complete implementation from `src/lib/parking.ts` is the authoritative local resizing rule. It protects status rather than bay kind, keeps surviving IDs stable and fills unused numeric suffixes on expansion.

```typescript
export function resizeLevelBays(bays: ParkingBay[], levelId: string, capacity: number): ParkingBay[] {
  if (!Number.isInteger(capacity) || capacity < 1 || capacity > 99) {
    throw new Error("Capacity must be between 1 and 99 bays per level.");
  }

  const levelBays = bays.filter((bay) => bay.levelId === levelId);
  if (levelBays.length === 0) throw new Error("Parking level not found.");

  const protectedCount = levelBays.filter((bay) => bay.status !== "available").length;
  if (capacity < protectedCount) {
    throw new Error("Capacity cannot be below the number of occupied or reserved bays.");
  }

  const difference = capacity - levelBays.length;
  if (difference === 0) return bays;

  if (difference < 0) {
    const removable = [...levelBays]
      .filter((bay) => bay.status === "available")
      .sort((left, right) => Number(right.id.split("-").at(-1)) - Number(left.id.split("-").at(-1)))
      .slice(0, Math.abs(difference));
    const removedIds = new Set(removable.map((bay) => bay.id));
    return bays.filter((bay) => !removedIds.has(bay.id));
  }

  const usedNumbers = new Set(levelBays.map((bay) => Number(bay.id.split("-").at(-1))));
  const additions: ParkingBay[] = [];
  for (let number = 1; additions.length < difference && number <= 99; number += 1) {
    if (usedNumbers.has(number)) continue;
    additions.push({
      id: `${levelId}-${String(number).padStart(2, "0")}`,
      levelId,
      status: "available",
      kind: "standard",
    });
  }
  if (additions.length !== difference) throw new Error("Unable to allocate bay numbers for this capacity.");
  return [...bays, ...additions];
}
```

A production service must enforce the same rule against current authoritative data and an approved facility-capacity policy. This helper alone cannot synchronize multiple browsers.

<!-- page: app-a-checkout-test | Appendix A: SOURCE CODE -->
## A.5 Checkout and an Existing Protection Test

The complete checkout helper below is reproduced from `src/lib/parking.ts`. The test excerpt is an existing case from `src/lib/parking.test.ts`, not a newly invented passing result.

```typescript
export function checkOut(
  bays: ParkingBay[],
  sessions: ParkingSession[],
  sessionId: string,
): { bays: ParkingBay[]; sessions: ParkingSession[] } {
  const session = sessions.find((item) => item.id === sessionId);
  if (!session) throw new Error("Active parking session not found.");

  return {
    bays: bays.map((bay) => bay.id === session.bayId
      ? { ...bay, status: "available", plate: undefined, since: undefined }
      : bay),
    sessions: sessions.filter((item) => item.id !== sessionId),
  };
}
```

```typescript
it("resizes capacity without removing occupied or reserved bays", () => {
    const expanded = resizeLevelBays(bays, "B1", 5);
    expect(expanded.filter((bay) => bay.levelId === "B1")).toHaveLength(5);
    expect(expanded.find((bay) => bay.id === "B1-02")?.status).toBe("occupied");
    const reduced = resizeLevelBays(expanded, "B1", 3);
    expect(reduced.filter((bay) => bay.levelId === "B1")).toHaveLength(3);
    expect(reduced.map((bay) => bay.id)).toContain("B1-02");
    expect(reduced.map((bay) => bay.id)).toContain("B1-03");
  });
```

The test inspects protected IDs as well as capacity. It does not test every boundary or corrupted session/bay relationship. The original suite's total remains nine cases, and its results are reported separately from supplemental browser checks.
