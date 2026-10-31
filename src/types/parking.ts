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
