import type { ParkingBay, ParkingSession } from "@/types/parking";

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

export function normalizeTamilNaduPlate(value: string): string {
  const plate = value.replace(/[\s-]/g, "").toUpperCase();
  if (!/^TN\d{2}[A-Z]{2}\d{4}$/.test(plate)) {
    throw new Error("Use TN + 2 digits + 2 letters + 4 digits, for example TN01AA1234.");
  }
  return plate;
}

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
