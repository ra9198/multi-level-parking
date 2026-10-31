"use client";

import { useEffect, useMemo, useState, useTransition, type FormEvent } from "react";
import {
  Accessibility,
  ArrowDownLeft,
  ArrowUpRight,
  Bell,
  CarFront,
  Check,
  ChevronDown,
  Clock3,
  Layers3,
  MapPin,
  Plus,
  Search,
  Settings2,
  X,
  Zap,
} from "lucide-react";
import { createManagedLocation, locations as seedLocations } from "@/lib/parking-data";
import { checkIn, checkOut, normalizeTamilNaduPlate, occupancyForLevel, resizeLevelBays } from "@/lib/parking";
import type { BayStatus, ParkingActivity, ParkingLocation } from "@/types/parking";

type DialogMode = "arrival" | "departure" | null;
type StatusFilter = "all" | BayStatus;
type GarageOperations = Pick<ParkingLocation, "bays" | "sessions" | "activity">;
type ManagementView = "capacity" | "add-location" | null;
const STORAGE_KEY = "parkline-garage-planning";

const filterOptions: { value: StatusFilter; label: string }[] = [
  { value: "all", label: "All bays" },
  { value: "available", label: "Available" },
  { value: "occupied", label: "Occupied" },
  { value: "reserved", label: "Reserved" },
];

function formatPlate(value: string) {
  return normalizeTamilNaduPlate(value);
}

export default function ParkingDashboard() {
  const [, startTransition] = useTransition();
  const [garageLocations, setGarageLocations] = useState(seedLocations);
  const [storageReady, setStorageReady] = useState(false);
  const [locationId, setLocationId] = useState(seedLocations[0].id);
  const [operationsByLocation, setOperationsByLocation] = useState<Record<string, GarageOperations>>(
    () => Object.fromEntries(seedLocations.map(({ id, bays, sessions, activity }) => [id, { bays, sessions, activity }])),
  );
  const [levelId, setLevelId] = useState(seedLocations[0].levels[0].id);
  const [statusFilter, setStatusFilter] = useState<StatusFilter>("all");
  const [search, setSearch] = useState("");
  const [dialog, setDialog] = useState<DialogMode>(null);
  const [selectedBayId, setSelectedBayId] = useState("");
  const [selectedSessionId, setSelectedSessionId] = useState("");
  const [plate, setPlate] = useState("");
  const [vehicle, setVehicle] = useState("");
  const [notice, setNotice] = useState("");
  const [managementView, setManagementView] = useState<ManagementView>(null);
  const [capacityDraft, setCapacityDraft] = useState<Record<string, string>>({});
  const [newLocationName, setNewLocationName] = useState("");
  const [newFloorCount, setNewFloorCount] = useState("3");
  const [newBaysPerFloor, setNewBaysPerFloor] = useState("24");
  const [managementError, setManagementError] = useState("");

  useEffect(() => {
    try {
      const saved = window.localStorage.getItem(STORAGE_KEY);
      if (saved) {
        const parsed = JSON.parse(saved) as {
          locations?: ParkingLocation[];
          operationsByLocation?: Record<string, GarageOperations>;
          locationId?: string;
        };
        if (parsed.locations?.length && parsed.operationsByLocation) {
          startTransition(() => {
            setGarageLocations(parsed.locations!);
            setOperationsByLocation(parsed.operationsByLocation!);
            const savedLocation = parsed.locations!.find((location) => location.id === parsed.locationId) ?? parsed.locations![0];
            setLocationId(savedLocation.id);
            setLevelId(savedLocation.levels[0]?.id ?? seedLocations[0].levels[0].id);
          });
        }
      }
    } catch {
      window.localStorage.removeItem(STORAGE_KEY);
    } finally {
      setStorageReady(true);
    }
  }, [startTransition]);

  useEffect(() => {
    if (!storageReady) return;
    try {
      window.localStorage.setItem(STORAGE_KEY, JSON.stringify({
        locations: garageLocations,
        operationsByLocation,
        locationId,
      }));
    } catch {
      console.warn("Could not save garage planning in this browser.");
    }
  }, [garageLocations, locationId, operationsByLocation, storageReady]);

  const selectedLocation = garageLocations.find((location) => location.id === locationId) ?? garageLocations[0];
  const { bays, sessions, activity } = operationsByLocation[locationId] ?? {
    bays: selectedLocation.bays,
    sessions: selectedLocation.sessions,
    activity: selectedLocation.activity,
  };
  const selectedLevel = selectedLocation.levels.find((level) => level.id === levelId)!;
  const levelBays = bays.filter((bay) => bay.levelId === levelId);
  const levelStats = occupancyForLevel(bays, levelId);
  const totalStats = selectedLocation.levels.reduce(
    (total, level) => {
      const stats = occupancyForLevel(bays, level.id);
      return {
        total: total.total + stats.total,
        occupied: total.occupied + stats.occupied,
        reserved: total.reserved + stats.reserved,
        available: total.available + stats.available,
      };
    },
    { total: 0, occupied: 0, reserved: 0, available: 0 },
  );
  const filteredBays = useMemo(() => {
    const normalizedSearch = search.trim().toLowerCase();
    return levelBays.filter((bay) => {
      const matchesStatus = statusFilter === "all" || bay.status === statusFilter;
      const matchesSearch = !normalizedSearch || bay.id.toLowerCase().includes(normalizedSearch)
        || bay.plate?.toLowerCase().includes(normalizedSearch);
      return matchesStatus && matchesSearch;
    });
  }, [levelBays, search, statusFilter]);

  function updateOperations(next: Partial<GarageOperations>) {
    setOperationsByLocation((current) => ({
      ...current,
      [locationId]: { ...current[locationId], ...next },
    }));
  }

  function changeLocation(nextLocationId: string) {
    const nextLocation = garageLocations.find((location) => location.id === nextLocationId);
    if (!nextLocation) return;
    setLocationId(nextLocationId);
    setLevelId(nextLocation.levels[0].id);
    setSearch("");
    setStatusFilter("all");
    setDialog(null);
    setNotice("");
  }

  function openCapacityManager(view: ManagementView = "capacity") {
    setDialog(null);
    setCapacityDraft(Object.fromEntries(selectedLocation.levels.map((level) => [level.id, String(level.capacity)])));
    setManagementError("");
    setManagementView(view);
  }

  function saveCapacity(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    try {
      let nextBays = bays;
      const nextLevels = selectedLocation.levels.map((level) => {
        const capacity = Number(capacityDraft[level.id]);
        nextBays = resizeLevelBays(nextBays, level.id, capacity);
        return { ...level, capacity };
      });
      setGarageLocations((current) => current.map((location) => location.id === locationId
        ? { ...location, levels: nextLevels, bays: nextBays }
        : location));
      updateOperations({ bays: nextBays });
      setManagementView(null);
      setNotice(`${selectedLocation.name} capacity updated to ${nextLevels.reduce((sum, level) => sum + level.capacity, 0)} bays.`);
    } catch (error) {
      setManagementError(error instanceof Error ? error.message : "Unable to update capacity.");
    }
  }

  function addLocation(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setManagementError("");
    if (garageLocations.some((location) => location.name.toLowerCase() === newLocationName.trim().toLowerCase())) {
      setManagementError("A location with this name already exists.");
      return;
    }
    try {
      const location = createManagedLocation(newLocationName, Number(newFloorCount), Number(newBaysPerFloor));
      setGarageLocations((current) => [...current, location]);
      setOperationsByLocation((current) => ({
        ...current,
        [location.id]: { bays: location.bays, sessions: location.sessions, activity: location.activity },
      }));
      setLocationId(location.id);
      setLevelId(location.levels[0].id);
      setSearch("");
      setStatusFilter("all");
      setManagementView(null);
      setNewLocationName("");
      setNotice(`${location.name} added with ${location.levels.reduce((sum, level) => sum + level.capacity, 0)} bays.`);
    } catch (error) {
      setManagementError(error instanceof Error ? error.message : "Unable to add this location.");
    }
  }

  function openDialog(mode: Exclude<DialogMode, null>, bayId = "") {
    setNotice("");
    setDialog(mode);
    if (mode === "arrival") {
      setSelectedBayId(bayId || levelBays.find((bay) => bay.status === "available")?.id || "");
      setPlate("");
      setVehicle("");
    } else {
      const matchingSession = sessions.find((session) => session.bayId === bayId)
        ?? sessions.find((session) => session.levelId === levelId);
      setSelectedSessionId(matchingSession?.id ?? "");
    }
  }

  function closeDialog() {
    setDialog(null);
    setNotice("");
  }

  function submitArrival(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    try {
      const result = checkIn(bays, sessions, selectedBayId, plate, vehicle, new Date().toISOString());
      const nextActivity: ParkingActivity = {
        id: `arrival-${Date.now()}`,
        type: "arrival",
        plate: formatPlate(plate),
        bayId: selectedBayId,
        time: "Just now",
      };
      updateOperations({ bays: result.bays, sessions: result.sessions, activity: [nextActivity, ...activity] });
      setNotice(`${formatPlate(plate)} checked in at ${selectedBayId}.`);
      setDialog(null);
    } catch (error) {
      setNotice(error instanceof Error ? error.message : "Unable to check in this vehicle.");
    }
  }

  function submitDeparture(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    try {
      const session = sessions.find((item) => item.id === selectedSessionId);
      if (!session) throw new Error("Choose an active parking session.");
      const result = checkOut(bays, sessions, selectedSessionId);
      updateOperations({ bays: result.bays, sessions: result.sessions, activity: [{
        id: `departure-${Date.now()}`,
        type: "departure",
        plate: session.plate,
        bayId: session.bayId,
        time: "Just now",
      }, ...activity] });
      setNotice(`${session.plate} checked out from ${session.bayId}.`);
      setDialog(null);
    } catch (error) {
      setNotice(error instanceof Error ? error.message : "Unable to check out this vehicle.");
    }
  }

  return (
    <main className="app-shell">
      <aside className="sidebar">
        <a className="brand" href="#overview" aria-label="Parkline home">
          <span className="brand-mark"><Layers3 size={19} strokeWidth={2.2} /></span>
          <span className="brand-name">parkline<span>.</span></span>
        </a>
        <div className="garage-switcher">
          <div className="garage-icon"><MapPin size={16} /></div>
          <label className="garage-copy"><span>GARAGE</span><select aria-label="Garage location" value={locationId} onChange={(event) => changeLocation(event.target.value)}>{garageLocations.map((location) => <option key={location.id} value={location.id}>{location.name}</option>)}</select></label>
          <ChevronDown size={15} className="muted-icon" />
        </div>
        <div className="side-label">OPERATIONS</div>
        <nav className="side-nav" aria-label="Main navigation">
          <a className="nav-item active" href="#overview"><Layers3 size={17} /> Overview <span className="nav-pip" /></a>
          <a className="nav-item" href="#parking-layout"><CarFront size={17} /> Parking bays</a>
          <a className="nav-item" href="#activity"><Clock3 size={17} /> Activity</a>
        </nav>
        <div className="sidebar-bottom">
          <div className="live-card"><span className="live-dot" /><span>Systems operational</span><span className="live-status">LIVE</span></div>
          <button className="profile-button" type="button" aria-label="Account menu">
            <span className="avatar">R</span>
            <span className="profile-copy"><strong>Reshma</strong><small>Garage manager</small></span>
            <ChevronDown size={15} className="muted-icon" />
          </button>
        </div>
      </aside>

      <section className="main-area" id="overview">
        <header className="topbar">
          <div className="breadcrumb"><span>{selectedLocation.name}</span><span className="crumb-slash">/</span><strong>Overview</strong></div>
          <div className="topbar-actions">
            <span className="service-pill"><span className="live-dot" /> Live operations</span>
            <button type="button" className="icon-button notification-button" aria-label="Notifications"><Bell size={18} /><i /></button>
            <span className="topbar-date">Saturday, 31 October</span>
          </div>
        </header>

        <div className="dashboard-content">
          <div className="page-heading">
            <div>
              <div className="eyebrow"><span className="eyebrow-line" /> GARAGE OVERVIEW</div>
              <h1>Good morning, Reshma<span>.</span></h1>
              <p>Here&apos;s what&apos;s happening across your garage today.</p>
            </div>
            <div className="heading-actions">
              <button type="button" className="button button-secondary" onClick={() => openCapacityManager("capacity")}><Settings2 size={16} /> Plan capacity</button>
              <button type="button" className="button button-secondary" onClick={() => openDialog("departure")}><ArrowUpRight size={16} /> Check out</button>
              <button type="button" className="button button-primary" onClick={() => openDialog("arrival")}><Plus size={17} /> New arrival</button>
            </div>
          </div>

          {notice && <div className="notice" role="status"><Check size={16} /> {notice}<button type="button" onClick={() => setNotice("")} aria-label="Dismiss"><X size={15} /></button></div>}

          <section className="metric-grid" aria-label="Garage occupancy summary">
            <article className="metric-card metric-primary">
              <div className="metric-top"><span>Total capacity</span><span className="metric-icon"><Layers3 size={17} /></span></div>
              <div className="metric-value">{totalStats.total}<small> bays</small></div>
              <div className="metric-foot"><span className="metric-dot" /> Across {selectedLocation.levels.length} levels <span className="foot-divider">·</span> Per-floor plan</div>
            </article>
            <article className="metric-card">
              <div className="metric-top"><span>Currently parked</span><span className="metric-icon occupied-icon"><CarFront size={17} /></span></div>
              <div className="metric-value">{totalStats.occupied}<small> vehicles</small></div>
              <div className="metric-foot"><span className="trend-up"><ArrowUpRight size={13} /> 8.4%</span> vs. this time yesterday</div>
            </article>
            <article className="metric-card">
              <div className="metric-top"><span>Available now</span><span className="metric-icon available-icon"><Check size={17} /></span></div>
              <div className="metric-value">{totalStats.available}<small> bays</small></div>
              <div className="metric-foot"><span className="available-text">{Math.round(totalStats.available / totalStats.total * 100)}% open</span> across all levels</div>
            </article>
            <article className="metric-card">
              <div className="metric-top"><span>Reserved</span><span className="metric-icon reserved-icon"><Clock3 size={17} /></span></div>
              <div className="metric-value">{totalStats.reserved}<small> bays</small></div>
              <div className="metric-foot">Next arrival <strong className="foot-strong">in 12 minutes</strong></div>
            </article>
          </section>

          <section className="content-grid">
            <article className="panel parking-panel" id="parking-layout">
              <div className="panel-heading">
                <div><div className="section-kicker">LIVE MAP</div><h2>Parking layout</h2><p>Select a bay to manage its session.</p></div>
                <button className="select-control" type="button" onClick={() => setLevelId(selectedLocation.levels[(selectedLocation.levels.findIndex((level) => level.id === levelId) + 1) % selectedLocation.levels.length].id)} aria-label="Select next parking level">
                  <span className="floor-number">{selectedLevel.label}</span> {selectedLevel.name}<ChevronDown size={15} />
                </button>
              </div>
              <div className="floor-tabs" role="tablist" aria-label="Parking levels">
                {selectedLocation.levels.map((level) => {
                  const stats = occupancyForLevel(bays, level.id);
                  return <button key={level.id} type="button" role="tab" aria-selected={levelId === level.id} className={`floor-tab ${levelId === level.id ? "selected" : ""}`} onClick={() => setLevelId(level.id)}>
                    <span className="floor-tab-label">{level.label}</span><span className="floor-tab-count">{stats.occupied}/{stats.total}</span>
                  </button>;
                })}
              </div>
              <div className="floor-summary">
                <div className="floor-summary-copy"><span className="floor-summary-title">{selectedLevel.name}</span><span>{levelStats.occupied} occupied <b>·</b> {levelStats.available} available</span></div>
                <div className="occupancy-track" aria-label={`${levelStats.percent}% occupied`}><span style={{ width: `${levelStats.percent}%` }} /></div>
                <span className="occupancy-percent">{levelStats.percent}%</span>
              </div>
              <div className="map-toolbar">
                <label className="search-box"><Search size={15} /><input value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Find bay or plate" aria-label="Find bay or registration" /></label>
                <label className="filter-select"><span className="sr-only">Filter bay status</span><select value={statusFilter} onChange={(event) => setStatusFilter(event.target.value as StatusFilter)}>{filterOptions.map((option) => <option value={option.value} key={option.value}>{option.label}</option>)}</select><ChevronDown size={14} /></label>
              </div>
              <div className="bay-grid" aria-label={`${selectedLevel.name} parking bays`}>
                {filteredBays.map((bay) => <button key={bay.id} type="button" className={`bay bay-${bay.status} bay-${bay.kind}`} onClick={() => bay.status === "occupied" ? openDialog("departure", bay.id) : bay.status === "available" ? openDialog("arrival", bay.id) : setNotice(`${bay.id} is reserved.`)} aria-label={`${bay.id}, ${bay.status}${bay.plate ? ` by ${bay.plate}` : ""}`}>
                  <span className="bay-number">{bay.id.slice(-2)}</span>
                  {bay.status === "occupied" && <CarFront className="bay-car" size={17} />}
                  {bay.kind === "ev" && <Zap className="bay-kind-icon" size={11} />}
                  {bay.kind === "accessible" && <Accessibility className="bay-kind-icon" size={12} />}
                  {bay.plate && <span className="bay-plate">{bay.plate}</span>}
                </button>)}
                {filteredBays.length === 0 && <div className="empty-map">No bays match this search.</div>}
              </div>
              <div className="map-legend">
                <span><i className="legend-swatch swatch-available" /> Available <b>{levelStats.available}</b></span>
                <span><i className="legend-swatch swatch-occupied" /> Occupied <b>{levelStats.occupied}</b></span>
                <span><i className="legend-swatch swatch-reserved" /> Reserved <b>{levelStats.reserved}</b></span>
                <span className="legend-special"><Zap size={12} /> EV <Accessibility size={13} /> Accessible</span>
              </div>
              <div className="driveway"><ArrowDownLeft size={15} /> ONE-WAY DRIVE LANE <ArrowDownLeft size={15} /></div>
            </article>

            <aside className="right-column">
              <article className="panel level-panel">
                <div className="panel-heading compact-heading"><div><div className="section-kicker">BY LEVEL</div><h2>Floor status</h2></div><button className="text-action" type="button" onClick={() => document.getElementById("parking-layout")?.scrollIntoView({ behavior: "smooth" })}>View map <ArrowUpRight size={14} /></button></div>
                <div className="level-list">
                  {selectedLocation.levels.map((level, index) => {
                    const stats = occupancyForLevel(bays, level.id);
                    return <button key={level.id} type="button" className={`level-row ${levelId === level.id ? "level-row-active" : ""}`} onClick={() => setLevelId(level.id)}>
                      <span className={`level-mark level-mark-${index}`}>{level.label}</span>
                      <span className="level-info"><strong>{level.name}</strong><small>{stats.available} bays available</small></span>
                      <span className="level-occupancy"><strong>{stats.percent}%</strong><small>{stats.occupied}/{stats.total}</small></span>
                      <span className="mini-track"><i style={{ width: `${stats.percent}%` }} /></span>
                    </button>;
                  })}
                </div>
                <div className="capacity-note"><span className="capacity-note-icon"><Zap size={14} /></span><span><strong>EV charging</strong><small>6 stations · 4 in use</small></span><span className="capacity-note-status">2 free</span></div>
              </article>

              <article className="panel activity-panel" id="activity">
                <div className="panel-heading compact-heading"><div><div className="section-kicker">JUST NOW</div><h2>Recent activity</h2></div><button className="icon-button small-icon-button" type="button" aria-label="Activity options"><ChevronDown size={16} /></button></div>
                <div className="activity-list">
                  {activity.slice(0, 5).map((item) => <div className="activity-row" key={item.id}>
                    <span className={`activity-icon activity-${item.type}`}>{item.type === "arrival" ? <ArrowDownLeft size={15} /> : item.type === "departure" ? <ArrowUpRight size={15} /> : <Clock3 size={15} />}</span>
                    <span className="activity-copy"><strong>{item.type === "arrival" ? "Vehicle arrived" : item.type === "departure" ? "Vehicle departed" : "Bay reserved"}</strong><small><b>{item.plate}</b> · {item.bayId}</small></span>
                    <time>{item.time}</time>
                  </div>)}
                </div>
                <button type="button" className="activity-footer" onClick={() => setNotice("Showing the latest garage activity.")}>Activity is updating live <span className="pulse-dot" /></button>
              </article>
            </aside>
          </section>
          <footer className="page-footer"><span>Parkline <b>·</b> {selectedLocation.name}</span><span>Local browser plan <b>·</b> No live sensors connected</span></footer>
        </div>
      </section>

      {managementView && <div className="modal-backdrop" role="presentation" onMouseDown={(event) => { if (event.target === event.currentTarget) setManagementView(null); }}>
        <section className="modal management-modal" role="dialog" aria-modal="true" aria-labelledby="management-title">
          <div className="modal-heading"><span className="modal-icon"><Settings2 size={19} /></span><button type="button" className="icon-button modal-close" onClick={() => setManagementView(null)} aria-label="Close capacity manager"><X size={18} /></button></div>
          <div className="section-kicker">GARAGE PLANNING</div>
          <h2 id="management-title">{managementView === "capacity" ? "Plan capacity" : "Add a location"}</h2>
          <p className="modal-description">Adjust bay counts by floor or add a garage with its own floor plan.</p>
          <div className="management-tabs" role="tablist" aria-label="Garage planning actions">
            <button type="button" role="tab" aria-selected={managementView === "capacity"} className={managementView === "capacity" ? "management-tab active" : "management-tab"} onClick={() => openCapacityManager("capacity")}>Capacity</button>
            <button type="button" role="tab" aria-selected={managementView === "add-location"} className={managementView === "add-location" ? "management-tab active" : "management-tab"} onClick={() => { setManagementError(""); setManagementView("add-location"); }}>Add location</button>
          </div>
          {managementView === "capacity" ? <form onSubmit={saveCapacity}>
            <div className="planning-location"><MapPin size={15} /><strong>{selectedLocation.name}</strong><span>{selectedLocation.levels.reduce((sum, level) => sum + level.capacity, 0)} bays total</span></div>
            <div className="capacity-list">
              {selectedLocation.levels.map((level) => {
                const stats = occupancyForLevel(bays, level.id);
                return <label className="capacity-row" key={level.id}>
                  <span className="capacity-floor"><strong>{level.label} · {level.name}</strong><small>{stats.occupied} occupied · {stats.reserved} reserved · minimum {stats.occupied + stats.reserved}</small></span>
                  <input aria-label={`${level.name} capacity`} type="number" min={stats.occupied + stats.reserved} max={99} step={1} required value={capacityDraft[level.id] ?? level.capacity} onChange={(event) => setCapacityDraft((current) => ({ ...current, [level.id]: event.target.value }))} />
                </label>;
              })}
            </div>
            {managementError && <p className="form-error" role="alert">{managementError}</p>}
            <button className="button button-primary modal-submit" type="submit"><Check size={16} /> Save capacity</button>
          </form> : <form onSubmit={addLocation}>
            <label className="form-field">Location name<input autoFocus value={newLocationName} onChange={(event) => setNewLocationName(event.target.value)} placeholder="e.g. City Centre Garage" maxLength={70} required /></label>
            <div className="planning-fields">
              <label className="form-field">Number of floors<input type="number" min={1} max={10} step={1} value={newFloorCount} onChange={(event) => setNewFloorCount(event.target.value)} required /></label>
              <label className="form-field">Bays per floor<input type="number" min={1} max={99} step={1} value={newBaysPerFloor} onChange={(event) => setNewBaysPerFloor(event.target.value)} required /></label>
            </div>
            <p className="capacity-preview">New location capacity <strong>{(Number(newFloorCount) || 0) * (Number(newBaysPerFloor) || 0)} bays</strong></p>
            {managementError && <p className="form-error" role="alert">{managementError}</p>}
            <button className="button button-primary modal-submit" type="submit"><Plus size={16} /> Add location</button>
          </form>}
          <p className="demo-note"><span className="live-dot" /> Planning changes save in this browser</p>
        </section>
      </div>}

      {dialog && <div className="modal-backdrop" role="presentation" onMouseDown={(event) => { if (event.target === event.currentTarget) closeDialog(); }}>
        <section className="modal" role="dialog" aria-modal="true" aria-labelledby="dialog-title">
          <div className="modal-heading"><span className="modal-icon">{dialog === "arrival" ? <ArrowDownLeft size={19} /> : <ArrowUpRight size={19} />}</span><button type="button" className="icon-button modal-close" onClick={closeDialog} aria-label="Close dialog"><X size={18} /></button></div>
          <div className="section-kicker">PARKING SESSION</div>
          <h2 id="dialog-title">{dialog === "arrival" ? "Check in a vehicle" : "Check out a vehicle"}</h2>
          <p className="modal-description">{dialog === "arrival" ? "Assign an available bay and start a parking session." : "Select an active session to free its bay."}</p>
          {dialog === "arrival" ? <form onSubmit={submitArrival}>
            <label className="form-field">Vehicle registration<input autoFocus value={plate} onChange={(event) => setPlate(event.target.value)} placeholder="TN01AA1234" title="TN followed by 2 digits, 2 letters, and 4 digits" autoCapitalize="characters" spellCheck={false} required maxLength={14} /></label>
            <label className="form-field">Vehicle description<input value={vehicle} onChange={(event) => setVehicle(event.target.value)} placeholder="e.g. Blue Toyota Corolla" maxLength={60} /></label>
            <label className="form-field">Parking bay<select value={selectedBayId} onChange={(event) => setSelectedBayId(event.target.value)} required><option value="" disabled>Select an available bay</option>{bays.filter((bay) => bay.status === "available").map((bay) => <option key={bay.id} value={bay.id}>{bay.id} · {selectedLocation.levels.find((level) => level.id === bay.levelId)?.name}{bay.kind === "ev" ? " · EV" : bay.kind === "accessible" ? " · Accessible" : ""}</option>)}</select></label>
            {notice && <p className="form-error" role="alert">{notice}</p>}
            <button className="button button-primary modal-submit" type="submit"><Plus size={16} /> Start parking session</button>
          </form> : <form onSubmit={submitDeparture}>
            <label className="form-field">Active parking session<select autoFocus value={selectedSessionId} onChange={(event) => setSelectedSessionId(event.target.value)} required><option value="" disabled>Select a vehicle</option>{sessions.filter((session) => session.levelId === levelId).map((session) => <option key={session.id} value={session.id}>{session.plate} · {session.bayId} · {session.vehicle}</option>)}</select></label>
            {sessions.filter((session) => session.levelId === levelId).length === 0 && <p className="form-hint">No active sessions on this level. Switch floors to check out another vehicle.</p>}
            {notice && <p className="form-error" role="alert">{notice}</p>}
            <button className="button button-primary modal-submit" type="submit" disabled={!sessions.some((session) => session.levelId === levelId)}><Check size={16} /> Complete check out</button>
          </form>}
          <p className="demo-note"><span className="live-dot" /> Demo mode · saved in this browser</p>
        </section>
      </div>}
    </main>
  );
}
