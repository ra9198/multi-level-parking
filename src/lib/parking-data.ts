import type { ParkingActivity, ParkingBay, ParkingLevel, ParkingLocation, ParkingSession } from "@/types/parking";

export const levels: ParkingLevel[] = [
  { id: "B1", label: "B1", name: "Basement", capacity: 24 },
  { id: "L1", label: "01", name: "Ground floor", capacity: 24 },
  { id: "L2", label: "02", name: "Upper deck", capacity: 24 },
];

const bayStatus: Record<string, "available" | "occupied" | "reserved"> = {
  "B1-02": "occupied", "B1-03": "occupied", "B1-05": "reserved", "B1-06": "occupied",
  "B1-08": "occupied", "B1-09": "occupied", "B1-12": "occupied", "B1-13": "reserved",
  "B1-16": "occupied", "B1-18": "occupied", "B1-20": "occupied", "B1-21": "occupied",
  "L1-01": "occupied", "L1-02": "occupied", "L1-04": "occupied", "L1-05": "occupied",
  "L1-07": "reserved", "L1-08": "occupied", "L1-09": "occupied", "L1-11": "occupied",
  "L1-12": "occupied", "L1-14": "occupied", "L1-15": "occupied", "L1-17": "occupied",
  "L1-19": "occupied", "L1-21": "occupied", "L1-22": "reserved", "L1-23": "occupied",
  "L2-01": "occupied", "L2-03": "occupied", "L2-04": "reserved", "L2-06": "occupied",
  "L2-08": "occupied", "L2-10": "occupied", "L2-11": "occupied", "L2-13": "occupied",
  "L2-14": "reserved", "L2-17": "occupied", "L2-19": "occupied", "L2-22": "occupied",
};

const plates: Record<string, string> = {
  "B1-02": "TN01AA4821", "B1-03": "TN02AB9014", "B1-06": "TN03AC2180", "B1-08": "TN04AD7729",
  "B1-09": "TN05AE0642", "B1-12": "TN06AF1938", "B1-16": "TN07AG5051", "B1-18": "TN08AH8246",
  "B1-20": "TN09AJ4328", "B1-21": "TN10AK7510",
  "L1-01": "TN11AL3370", "L1-02": "TN12AM6258", "L1-04": "TN13AN1043", "L1-05": "TN14AP8892",
  "L1-08": "TN15AQ2716", "L1-09": "TN16AR4620", "L1-11": "TN17AS7419", "L1-12": "TN18AT3895",
  "L1-14": "TN19AU2007", "L1-15": "TN20AV5584", "L1-17": "TN21AW0108", "L1-19": "TN22AX9931",
  "L1-21": "TN23AY6312", "L1-23": "TN24AZ8045", "L2-01": "TN25BA1947", "L2-03": "TN26BB3508",
  "L2-06": "TN27BC6163", "L2-08": "TN28BD9481", "L2-10": "TN29BE2740", "L2-11": "TN30BF8836",
  "L2-13": "TN31BG5102", "L2-17": "TN32BH7369", "L2-19": "TN33BJ4061", "L2-22": "TN34BK1285",
};

const accessibleBays = new Set(["B1-01", "L1-01", "L2-01"]);
const evBays = new Set(["B1-07", "B1-14", "L1-06", "L1-16", "L2-07", "L2-16"]);

export const initialBays: ParkingBay[] = levels.flatMap((level) =>
  Array.from({ length: level.capacity }, (_, index) => {
    const number = String(index + 1).padStart(2, "0");
    const id = `${level.id}-${number}`;
    return {
      id,
      levelId: level.id,
      status: bayStatus[id] ?? "available",
      kind: accessibleBays.has(id) ? "accessible" : evBays.has(id) ? "ev" : "standard",
      ...(plates[id] ? { plate: plates[id], since: new Date(Date.now() - (index + 2) * 18 * 60_000).toISOString() } : {}),
    };
  }),
);

export const initialSessions: ParkingSession[] = initialBays
  .filter((bay) => bay.status === "occupied" && bay.plate)
  .map((bay, index) => ({
    id: `session-${index + 1}`,
    bayId: bay.id,
    levelId: bay.levelId,
    plate: bay.plate!,
    vehicle: ["Volvo XC40", "Toyota Corolla", "Mini Cooper", "Tesla Model 3"][index % 4],
    startedAt: bay.since!,
  }));

export const initialActivity: ParkingActivity[] = [
  { id: "a1", type: "arrival", plate: "TN01AA4821", bayId: "B1-02", time: "2 min ago" },
  { id: "a2", type: "departure", plate: "TN35BL7164", bayId: "L1-18", time: "8 min ago" },
  { id: "a3", type: "reservation", plate: "Reserved", bayId: "L2-04", time: "14 min ago" },
  { id: "a4", type: "arrival", plate: "TN02AB9014", bayId: "B1-03", time: "21 min ago" },
];

function createLocation(id: string, name: string, seed: number): ParkingLocation {
  const locationBays = initialBays.map((bay, index) => {
    const statusRoll = (index * 7 + seed * 5) % 19;
    const status: ParkingBay["status"] = statusRoll < 10 ? "occupied" : statusRoll < 13 ? "reserved" : "available";
    const rto = String(((seed * 7 + index) % 99) + 1).padStart(2, "0");
    const series = `${String.fromCharCode(65 + (seed + index) % 26)}${String.fromCharCode(65 + (seed * 2 + index) % 26)}`;
    const serial = String(2400 + seed * 317 + index * 29).slice(-4);
    const plate = `TN${rto}${series}${serial}`;

    return {
      ...bay,
      status,
      plate: status === "occupied" ? plate : undefined,
      since: status === "occupied" ? new Date(Date.now() - (index + seed + 2) * 18 * 60_000).toISOString() : undefined,
    };
  });
  const locationSessions = locationBays
    .filter((bay) => bay.status === "occupied" && bay.plate)
    .map((bay, index) => ({
      id: `${id}-${bay.id}`,
      bayId: bay.id,
      levelId: bay.levelId,
      plate: bay.plate!,
      vehicle: ["Hyundai Creta", "Honda City", "Tata Nexon", "Kia Seltos"][index % 4],
      startedAt: bay.since!,
    }));
  const reservedBay = locationBays.find((bay) => bay.status === "reserved")!;
  const firstSession = locationSessions[0];

  return {
    id,
    name,
    levels,
    bays: locationBays,
    sessions: locationSessions,
    activity: [
      { id: `${id}-arrival`, type: "arrival", plate: firstSession.plate, bayId: firstSession.bayId, time: "3 min ago" },
      { id: `${id}-reservation`, type: "reservation", plate: "Reserved", bayId: reservedBay.id, time: "16 min ago" },
      { id: `${id}-departure`, type: "departure", plate: "Previous visit", bayId: "L1-18", time: "24 min ago" },
    ],
  };
}

export const locations: ParkingLocation[] = [
  { id: "riverside", name: "Riverside Centre", levels, bays: initialBays, sessions: initialSessions, activity: initialActivity },
  createLocation("marina-velachery", "Marina Mall, Velachery", 1),
  createLocation("vr-anna-nagar", "VR Mall, Anna Nagar", 2),
  createLocation("phoenix-omr", "Phoenix Mall, OMR", 3),
];

export function createManagedLocation(name: string, floorCount: number, baysPerFloor: number): ParkingLocation {
  const cleanName = name.trim();
  if (!cleanName) throw new Error("Enter a location name.");
  if (!Number.isInteger(floorCount) || floorCount < 1 || floorCount > 10) {
    throw new Error("Choose between 1 and 10 floors.");
  }
  if (!Number.isInteger(baysPerFloor) || baysPerFloor < 1 || baysPerFloor > 99) {
    throw new Error("Choose between 1 and 99 bays per floor.");
  }

  const newLevels: ParkingLevel[] = Array.from({ length: floorCount }, (_, index) => ({
    id: index === 0 ? "B1" : `L${index}`,
    label: index === 0 ? "B1" : String(index).padStart(2, "0"),
    name: index === 0 ? "Basement" : index === 1 ? "Ground floor" : `Level ${index}`,
    capacity: baysPerFloor,
  }));
  const newBays: ParkingBay[] = newLevels.flatMap((level) =>
    Array.from({ length: baysPerFloor }, (_, index) => ({
      id: `${level.id}-${String(index + 1).padStart(2, "0")}`,
      levelId: level.id,
      status: "available" as const,
      kind: "standard" as const,
    })),
  );

  return {
    id: `location-${Date.now()}`,
    name: cleanName,
    levels: newLevels,
    bays: newBays,
    sessions: [],
    activity: [],
  };
}
