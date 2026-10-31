#!/usr/bin/env python3
"""Generate source-grounded report diagrams; no stock or synthetic UI images."""
from pathlib import Path
from math import atan2, cos, sin, pi
import textwrap
import pymupdf
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph
from reportlab.lib.styles import ParagraphStyle

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs/project-report/assets/diagrams"
CACHE = ROOT / ".cache/report-diagrams"
OUT.mkdir(parents=True, exist_ok=True)
CACHE.mkdir(parents=True, exist_ok=True)
FONTS = ROOT / "docs/project-report/assets/fonts"
pdfmetrics.registerFont(TTFont("STIX", str(FONTS / "STIXGeneral.ttf")))
pdfmetrics.registerFont(TTFont("STIXB", str(FONTS / "STIXGeneralBol.ttf")))
NAVY, GREEN, PALE, LINE, INK = "#18324D", "#157B5B", "#F0F4F8", "#91A3B3", "#243446"

class Diagram:
    def __init__(self, name, height=460):
        self.name, self.w, self.h = name, 740, height
        self.pdf = CACHE / (name + ".pdf")
        self.c = canvas.Canvas(str(self.pdf), pagesize=(self.w, self.h))
        self.c.setFillColor(HexColor("#FFFFFF"))
        self.c.rect(0, 0, self.w, self.h, fill=1, stroke=0)
    def line(self, points, dashed=False):
        c = self.c
        c.setStrokeColor(HexColor(LINE)); c.setLineWidth(1.6)
        c.setDash(5, 4) if dashed else c.setDash()
        p = c.beginPath(); p.moveTo(points[0][0], self.h-points[0][1])
        for x,y in points[1:]: p.lineTo(x,self.h-y)
        c.drawPath(p)
        c.setDash()
    def arrow(self, points, label=None, label_at=None, dashed=False):
        self.line(points, dashed)
        x,y=points[-1]; px,py=points[-2]; angle=atan2(y-py,x-px)
        c=self.c; c.setFillColor(HexColor(LINE)); p=c.beginPath(); p.moveTo(x,self.h-y)
        for a in [angle+pi-0.45,angle+pi+0.45]: p.lineTo(x+10*cos(a),self.h-(y+10*sin(a)))
        p.close(); c.drawPath(p,fill=1,stroke=0)
        if label:
            lx,ly=label_at or ((x+px)/2,(y+py)/2-5)
            self.text(lx,ly,label,size=13,center=True,bg=True)
    def text(self, x, y, text, size=15, bold=False, center=False, bg=False, color=INK):
        c=self.c; font="STIXB" if bold else "STIX"
        for i,line in enumerate(text.split("\n")):
            yy=self.h-y-i*(size+4)
            width=pdfmetrics.stringWidth(line,font,size)
            if bg:
                c.setFillColor(HexColor("#FFFFFF")); c.rect(x-width/2-3,yy-2,width+6,size+3,fill=1,stroke=0)
            c.setFillColor(HexColor(color)); c.setFont(font,size)
            c.drawCentredString(x,yy,line) if center else c.drawString(x,yy,line)
    def box(self, x,y,w,h,title,detail="",fill=PALE,stroke=NAVY,size=16):
        c=self.c; c.setStrokeColor(HexColor(stroke)); c.setFillColor(HexColor(fill)); c.setLineWidth(1.4)
        c.roundRect(x,self.h-y-h,w,h,8,fill=1,stroke=1)
        self.text(x+w/2,y+23,title,size=size,bold=True,center=True,color=stroke)
        if detail:
            lines=[]
            for part in detail.split("\n"): lines.extend(textwrap.wrap(part,max(18,int(w/7.3))))
            self.text(x+w/2,y+45,"\n".join(lines),size=14,center=True)
    def ellipse(self,x,y,w,h,label):
        c=self.c; c.setStrokeColor(HexColor(NAVY)); c.setFillColor(HexColor(PALE)); c.ellipse(x,self.h-y-h,x+w,self.h-y,fill=1,stroke=1)
        self.text(x+w/2,y+h/2+5,label,size=16,center=True)
    def note(self,text): self.text(370,self.h-14,text,size=13,center=True,color="#536679")
    def finish(self):
        self.c.save()
        with pymupdf.open(self.pdf) as doc:
            doc[0].get_pixmap(matrix=pymupdf.Matrix(2.5,2.5),alpha=False).save(OUT/(self.name+".png"))

# 4.1 Layered architecture.
d=Diagram("04-01-architecture",520)
d.box(205,10,330,56,"Operator in a web browser","Clicks, form entry and local feedback")
d.box(45,105,650,62,"Next.js route and root layout","page.tsx / layout.tsx: initial application composition")
d.box(45,210,650,68,"ParkingDashboard — React client component","Selected scope, operational state, dialogs and derived output")
d.box(30,330,325,79,"Pure domain helpers","Counts, TN validation, check-in/out, safe resize")
d.box(385,330,325,79,"Typed fixtures and creation","Initial locations; createManagedLocation")
d.box(205,452,330,52,"Browser local storage","Device-local saved JSON; no shared database")
d.arrow([(370,66),(370,105)])
d.arrow([(370,167),(370,210)])
d.arrow([(200,278),(200,330)])
d.arrow([(545,330),(545,278)])
d.arrow([(370,278),(370,452)],label="save / restore",label_at=(370,432),dashed=True)
d.finish()

# 4.2 Context DFD.
d=Diagram("04-02-context-dfd",390)
d.box(22,115,170,85,"Operator","Manual observations and decisions")
d.ellipse(267,90,220,140,"0. Parkline MVP")
d.box(555,115,163,85,"Local storage","Saved plan JSON")
d.arrow([(192,137),(267,137)],"input",(230,126))
d.arrow([(267,183),(192,183)],"feedback",(230,207))
d.arrow([(487,137),(555,137)],"write",(521,125))
d.arrow([(555,183),(487,183)],"restore",(521,207))
d.text(370,286,"All parking state is local to this browser and origin.",size=17,center=True)
d.note("No gate, sensor, payment network or parking API is connected.")
d.finish()

# 4.3 Functional decomposition.
d=Diagram("04-03-level-one-dfd",500)
d.box(270,8,200,54,"Operator input","Location, floor, form values")
d.box(20,115,210,65,"1. Select / inspect","Location, floor, search, filter")
d.box(265,115,210,65,"2. Start session","Validate plate and available bay")
d.box(510,115,210,65,"3. End session","Find session and release bay")
d.box(20,250,210,65,"4. Plan inventory","Resize floors; add a location")
d.box(265,250,455,65,"D1. React application state","Locations + operationsByLocation + view selections")
d.box(20,390,300,65,"5. Render derived output","Metric cards, floor map, recent activity")
d.box(440,390,280,65,"D2. Browser local storage","One origin-scoped serialized snapshot")
for x in [125,370,615]: d.arrow([(370,62),(x,92),(x,115)])
d.arrow([(125,180),(125,250)])
d.arrow([(370,180),(370,250)])
d.arrow([(615,180),(615,250)])
d.arrow([(230,282),(265,282)])
d.arrow([(390,315),(390,350),(170,350),(170,390)])
d.arrow([(580,315),(580,390)],dashed=True)
d.note("D1 is the working state; D2 is a local copy, not an authoritative multi-user store.")
d.finish()

# 4.4 Arrival decomposition.
d=Diagram("04-04-arrival-dfd",590)
d.box(180,8,380,55,"Arrival form","Plate, vehicle description, selected bay ID")
d.box(180,100,380,63,"2.1 Normalize and validate plate","Strip spaces/hyphens; uppercase; match TN format")
d.box(180,205,380,63,"2.2 Validate transition guards","Bay exists and is available; registration not active")
d.box(180,310,380,63,"2.3 Construct next collections","Mark bay occupied; append normalized active session")
d.box(180,415,380,63,"2.4 Commit UI state and activity","Prepend arrival event; show confirmation; close dialog")
d.box(180,520,380,50,"2.5 Save local snapshot","Persistence effect; no server transaction")
for y1,y2 in [(63,100),(163,205),(268,310),(373,415),(478,520)]: d.arrow([(370,y1),(370,y2)])
d.line([(560,132),(677,132),(677,237),(560,237)])
d.text(655,185,"Failure:\nshow error;\nno commit",size=13,center=True)
d.finish()

# 4.5 Use cases.
d=Diagram("04-05-use-cases",530)
d.c.setStrokeColor(HexColor(LINE)); d.c.roundRect(240,40,465,470,8,fill=0,stroke=1)
d.text(470,43,"Parkline local application",size=17,bold=True,center=True)
d.ellipse(45,195,125,70,"Operator")
labels=["UC-01 Inspect occupancy","UC-02 Search / filter bays","UC-03 Check in vehicle","UC-04 Check out vehicle","UC-05 Resize floor capacity","UC-06 Add / switch location"]
for i,label in enumerate(labels):
 y=60+i*72
 d.ellipse(305,y,340,50,label)
 d.line([(170,230),(270,y+25),(305,y+25)])
d.note("One operator actor is modeled; the static manager profile is not authentication.")
d.finish()

# 4.6 Domain classes.
d=Diagram("04-06-domain-model",650)
d.box(215,8,310,90,"ParkingLocation","id, name\nlevels[], bays[], sessions[], activity[]")
d.box(20,175,300,105,"ParkingLevel","id, label, name\ncapacity: number")
d.box(420,175,300,125,"ParkingBay","id, levelId, status, kind\nplate?, since?")
d.box(20,390,325,125,"ParkingSession","id, bayId, levelId, plate\nvehicle, startedAt")
d.box(415,390,305,125,"ParkingActivity","id, type, plate, bayId, time\narrival | departure | reservation")
d.arrow([(270,98),(170,175)],"levels[]",(175,145))
d.arrow([(470,98),(570,175)],"bays[]",(570,145))
d.arrow([(20,220),(5,220),(5,450),(20,450)],"levelId",(44,339),dashed=True)
d.arrow([(570,300),(570,345),(180,345),(180,390)],"bayId / levelId",(367,338),dashed=True)
d.line([(370,98),(370,555),(180,555),(180,515)])
d.line([(370,555),(565,555),(565,515)])
d.text(370,589,"Status and kind are independent unions; optional fields are not runtime validation.",size=14,center=True)
d.note("Solid grouping lines show collections; dashed references are resolved within a location.")
d.finish()

# 4.7 Arrival sequence.
d=Diagram("04-07-arrival-sequence",545)
xs=[78,263,455,655]
for x,label in zip(xs,["Operator","Dashboard","checkIn helper","Local storage"]):
 d.box(x-70,8,140,45,label,size=15)
 d.line([(x,53),(x,490)],True)
d.arrow([(78,100),(263,100)],"submit arrival",(169,90))
d.arrow([(263,167),(455,167)],"bays, sessions, input",(360,155))
d.text(455,218,"normalize plate\ncheck availability\nreject duplicates",size=14,center=True,bg=True)
d.arrow([(455,295),(263,295)],"new bays + sessions",(359,283),True)
d.text(263,345,"commit state\nprepend activity",size=14,center=True,bg=True)
d.arrow([(263,405),(655,405)],"effect serializes snapshot",(466,392),True)
d.arrow([(263,465),(78,465)],"status confirmation",(171,454),True)
d.note("Failure returns through an exception and leaves operational collections uncommitted.")
d.finish()

# 4.8 Status machine.
d=Diagram("04-08-bay-state-machine",410)
d.ellipse(40,140,190,100,"AVAILABLE")
d.ellipse(505,140,190,100,"OCCUPIED")
d.ellipse(270,12,200,84,"RESERVED")
d.arrow([(230,165),(505,165)],"checkIn: valid plate; no active duplicate",(369,143))
d.arrow([(505,213),(230,213)],"checkOut: active session exists",(369,244))
d.text(370,302,"Reserved sample bays cannot be checked in or removed by resizing.",size=16,center=True)
d.text(370,332,"There is no implemented reserve / cancel / expire transition.",size=16,center=True)
d.note("BayKind (standard / ev / accessible) is preserved and is not a lifecycle state.")
d.finish()

# 4.9 Conceptual ER.
d=Diagram("04-09-conceptual-er",490)
d.box(260,10,220,65,"LOCATION","Location-scoped inventory")
d.box(30,155,270,80,"LEVEL","(location, level ID)\nplanned capacity")
d.box(440,155,270,80,"BAY","(location, bay ID)\nlevel reference; status; kind")
d.box(30,345,300,85,"ACTIVE SESSION","(location, session ID)\nbay reference; registration; start")
d.box(440,345,270,85,"ACTIVITY ITEM","Location collection\nbay reference as text")
d.arrow([(310,75),(165,155)],"1 to many",(198,119))
d.arrow([(435,75),(575,155)],"1 to many",(547,119))
d.arrow([(300,190),(440,190)],"1 to many",(370,178))
d.arrow([(575,235),(575,285),(180,285),(180,345)],"bay to active session: intended 0..1",(371,275))
d.arrow([(575,235),(575,345)],"event references",(641,304),True)
d.note("Conceptual relationships only: no SQL database, migrations or enforced foreign keys exist.")
d.finish()

# 4.10 Persistence flow.
d=Diagram("04-10-storage-lifecycle",520)
d.box(210,8,320,55,"Initial render","Seed locations and working collections")
d.box(210,105,320,65,"Read local-storage snapshot","Parse JSON; shallow shape checks")
d.box(210,220,320,65,"Schedule restored React state","startTransition; selected location / first level")
d.box(210,335,320,65,"Set storageReady; write effect","Serialize current state when enabled")
d.box(210,445,320,55,"Later operator changes","Trigger another local snapshot save")
for a,b in [(63,105),(170,220),(285,335),(400,445)]: d.arrow([(370,a),(370,b)])
d.text(95,256,"Invalid JSON:\nremove key;\nuse seeds",size=14,center=True)
d.arrow([(210,138),(95,138),(95,308),(210,308)],dashed=True)
d.text(645,345,"Review concern:\nrestoration and\nwrite timing need\ncoordination",size=14,center=True,color="#9C4A29")
d.finish()

# 4.11 Resize algorithm.
d=Diagram("04-11-capacity-workflow",580)
d.box(190,10,360,55,"Requested capacity","Integer within 1–99; known level")
d.box(190,100,360,65,"Count protected inventory","Occupied + reserved cannot be removed")
d.box(190,210,360,55,"Compute capacity difference","requested − current level bay count")
d.box(10,330,220,90,"Negative difference","Remove highest-numbered\navailable bays only")
d.box(260,330,220,90,"Zero difference","Return the original\nbay collection")
d.box(510,330,220,90,"Positive difference","Fill unused suffixes\n01–99 with standard bays")
d.box(190,495,360,60,"Commit a complete valid plan","Update level capacities and operational bays")
d.arrow([(370,65),(370,100)])
d.arrow([(370,165),(370,210)])
for x in [120,370,620]:
 d.arrow([(370,265),(x,298),(x,330)])
 d.arrow([(x,420),(x,459),(370,459),(370,495)])
d.finish()
print(f"Generated {len(list(OUT.glob('*.png')))} diagrams in {OUT}")
