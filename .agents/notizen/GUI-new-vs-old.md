# GUI Redesign: Alt vs. Neu

## Aktuelle GUI (Alt)

```
+--------------------------------------------------+
|  TaxAct E-File Extension Bot          - [] X     |
+--------------------------------------------------+
|                                                   |
|  TaxAct E-File Extension Bot                      |  <- Titel, links, 18px
|                                                   |
+--------------------------------------------------+
|  +----------------------------------------------+ |
|  |                                              | |
|  |       [====  Scan Client Table  ====]        | |  <- Grosser blauer Button, h=48
|  |                                              | |
|  |  .../clients_2026-03-21-16-03-24.csv Browse  | |  <- Kleine Schrift + Mini-Button
|  |                                              | |
|  |  47 TODO, 375 Done, 1 FAIL                   | |  <- Kleine Counts, eine Zeile
|  |                                              | |
|  +----------------------------------------------+ |  <- Card: Preprocessing
|                                                   |
+--------------------------------------------------+
|  +----------------------------------------------+ |
|  |          SELECT RETURN TYPE                   | |  <- Label zentriert, 12px
|  |  +----------+----------+----------+          | |
|  |  |   1120   |  1120S   | >>1040<< |          | |  <- Segmented Button, h=42
|  |  +----------+----------+----------+          | |
|  +----------------------------------------------+ |  <- Card: Return Type
|                                                   |
+--------------------------------------------------+
|  +----------------------------------------------+ |
|  |                                              | |
|  |       [====   Start Bot   ====]              | |  <- Gruener Button, h=48
|  |                                              | |
|  +----------------------------------------------+ |  <- Card: Control
|                                                   |
+--------------------------------------------------+
|  +----------------------------------------------+ |
|  |  Status: Ready                                | |  <- Body 13px
|  |  TaxAct: Validation skipped (Dev)             | |  <- Caption 12px, gelb
|  |                                              | |
|  +----------------------------------------------+ |  <- Card: Status
|                                                   |
+--------------------------------------------------+
|  +----------------------------------------------+ |
|  |  Log:                                         | |
|  |  +------------------------------------------+ | |
|  |  | > CSV loaded: clients_2026-...csv (423)  | | |
|  |  | > Application started                    | | |
|  |  | > TaxAct validation skipped              | | |
|  |  |                                          | | |  <- Textbox, h=200
|  |  |                                          | | |
|  |  |                                          | | |
|  |  |                                          | | |
|  |  +------------------------------------------+ | |
|  +----------------------------------------------+ |  <- Card: Log (expandiert)
|                                                   |
+--------------------------------------------------+
```

### Probleme

| Problem | Detail |
|---------|--------|
| **CSV versteckt** | Dateipfad in Caption-Groesse (12px) unter dem Scan-Button, wirkt als Sub-Element des Preprocessing |
| **Browse zu klein** | Winziger 70x28px Button, rechts angequetscht |
| **Scan dominiert** | "Scan Client Table" ist visuell prominenter als "Start Bot", obwohl es eine einmalige Aktion ist |
| **Counts unauffaellig** | `47 TODO, 375 Done, 1 FAIL` als einzeiliger grauer Text — keine farbige Differenzierung |
| **Zu viele gleichwertige Cards** | 5 Cards gleicher Breite, gleicher Rahmen — keine klare Hierarchie |
| **Status-Card redundant** | "Status: Ready" und TaxAct-Info koennten kompakter integriert werden |

---

## Vorgeschlagene GUI (Neu)

```
+--------------------------------------------------+
|  TaxAct E-File Extension Bot          - [] X     |
+--------------------------------------------------+
|                                                   |
|  TaxAct E-File Extension Bot                      |  <- Titel, links, 18px
|  TaxAct: Found                                    |  <- Inline unter Titel, klein, gruen
|                                                   |
+==================================================+
|  +----------------------------------------------+ |
|  |                                              | |
|  |  CLIENT FILE                                  | |  <- Section-Label, 11px, muted
|  |                                              | |
|  |  clients_2026-03-21-16-03-24.csv    [Browse] | |  <- Dateiname GROSS (15px bold)
|  |                                              | |     Browse-Button prominent (h=32)
|  |  C:\TaxActBot\logs\                           | |  <- Voller Pfad, klein, muted
|  |                                              | |
|  |  +----------+  +----------+  +----------+   | |
|  |  | 47       |  | 375      |  | 1        |   | |
|  |  | TODO     |  | Done     |  | FAIL     |   | |  <- 3 Stat-Badges nebeneinander
|  |  +----------+  +----------+  +----------+   | |     Zahl gross, Label klein
|  |                                              | |
|  +----------------------------------------------+ |  <- Card: Client File (PROMINENT)
|                                                   |
+--------------------------------------------------+
|  +----------------------------------------------+ |
|  |                                              | |
|  |  RETURN TYPE                                  | |  <- Section-Label, 11px
|  |  +----------+----------+----------+          | |
|  |  |   1120   |  1120S   | >>1040<< |          | |  <- Segmented Button, h=42
|  |  +----------+----------+----------+          | |
|  |                                              | |
|  |  [============  Start Bot  ============]     | |  <- Gruener Button, h=52, GROESSER
|  |                                              | |
|  +----------------------------------------------+ |  <- Card: Controls (zusammengefasst)
|                                                   |
+--------------------------------------------------+
|  +----------------------------------------------+ |
|  |                                              | |
|  |  [  Scan Client Table  ]                      | |  <- Sekundaerer Button, h=36
|  |                                              | |     Outline-Style, kleiner
|  +----------------------------------------------+ |  <- Card: Preprocessing (KLEINER)
|                                                   |
+--------------------------------------------------+
|  +----------------------------------------------+ |
|  |  Status: Ready                                | |  <- Body, links
|  +----------------------------------------------+ |  <- Kompakte Status-Zeile
|                                                   |
+--------------------------------------------------+
|  +----------------------------------------------+ |
|  |  Log:                                         | |
|  |  +------------------------------------------+ | |
|  |  | > CSV loaded: clients_2026-...csv (423)  | | |
|  |  | > Application started                    | | |
|  |  | > TaxAct validation skipped              | | |
|  |  |                                          | | |  <- Textbox, expandiert
|  |  |                                          | | |
|  |  |                                          | | |
|  |  |                                          | | |
|  |  |                                          | | |
|  |  +------------------------------------------+ | |
|  +----------------------------------------------+ |  <- Card: Log (expandiert)
|                                                   |
+--------------------------------------------------+
```

### Aenderungen im Detail

#### 1. Client File Card — NEU, Tier 1 (ganz oben, prominent)

```
  CLIENT FILE                                   <- Muted Section-Label
  clients_2026-03-21-16-03-24.csv    [Browse]   <- 15px bold + prominenter Button
  C:\TaxActBot\logs\                            <- Pfad in klein, muted

  +----------+  +----------+  +----------+
  | 47       |  | 375      |  | 1        |
  | TODO     |  | Done     |  | FAIL     |      <- Farbige Stat-Badges
  +----------+  +----------+  +----------+
```

- **Dateiname** ist das prominenteste Element (grosse Schrift, bold)
- **Browse** ist ein sichtbarer Button (nicht versteckt)
- **Stat-Badges** als 3 Boxen nebeneinander mit Farben:
  - TODO: Accent-Blau (#2563eb)
  - Done: Gruen (#22c55e)
  - FAIL: Rot (#ef4444)
- **Zahl oben gross** (18-20px), **Label unten klein** (11px)

#### 2. Controls Card — Return Type + Start Bot zusammengefasst

```
  RETURN TYPE
  +----------+----------+----------+
  |   1120   |  1120S   | >>1040<< |
  +----------+----------+----------+

  [============  Start Bot  ============]        <- h=52, etwas groesser
```

- Return Type und Start Bot gehoeren logisch zusammen: "Was" + "Los"
- Spart eine Card-Ebene
- Start Bot ist jetzt die einzige primaere Aktion in seinem visuellen Bereich
- **Start Bot wird etwas groesser** (h=52 statt h=48) fuer mehr Gewicht

#### 3. Scan Client Table — Herabgestuft zu sekundaerem Button

```
  [  Scan Client Table  ]                       <- Outline-Style, h=36
```

- **Visuell kleiner** als vorher (h=36 statt h=48)
- **Outline-Style** statt filled: Border in Accent-Farbe, transparenter Hintergrund
- Kommuniziert: "Ich bin eine Aktion, aber nicht die Hauptaktion"
- Eigene kleine Card oder sogar nur ein Button-Row

#### 4. Status — Kompakter

```
  Status: Ready                                  <- Eine Zeile
```

- TaxAct-Info wandert nach oben unter den Titel (inline, klein)
- Status-Card wird auf eine Zeile reduziert
- Progress-Info erscheint hier nur waehrend Bot laeuft

#### 5. Log — Unveraendert, expandiert

- Bleibt am unteren Rand
- Bekommt mehr Platz weil die anderen Sections kompakter sind
- Visuell am dunkelsten (recessed Surface)

---

## Farbvergleich

### Stat-Badges (Neu)

| Badge | Hintergrund | Text (Zahl) | Text (Label) |
|-------|-------------|-------------|--------------|
| TODO  | `#1e3a5f` (dunkles Blau) | `#60a5fa` (helles Blau) | `#999999` |
| Done  | `#14532d` (dunkles Gruen) | `#4ade80` (helles Gruen) | `#999999` |
| FAIL  | `#7f1d1d` (dunkles Rot) | `#f87171` (helles Rot) | `#999999` |

### Button-Hierarchie (Neu)

| Button | Typ | Farbe | Hoehe |
|--------|-----|-------|-------|
| Start Bot | Primary (filled) | `#22c55e` (Gruen) | 52px |
| Browse | Secondary (filled) | `#2e2e2e` (Neutral) | 32px |
| Scan Client Table | Tertiary (outline) | Border: `#2563eb`, BG: transparent | 36px |

### Scan-Button Outline-Style

```
  Vorher (Alt):                    Nachher (Neu):
  +========================+       +------------------------+
  ||  Scan Client Table   ||       |  Scan Client Table     |
  +========================+       +------------------------+
   Filled blau, h=48                Outline blau, h=36
   Prominent, dominiert             Zurueckhaltend, sekundaer
```

---

## Zusammenfassung der Hierarchie

```
Alt:                              Neu:

1. Scan Client Table  (blau)      1. Client File + Counts  (PROMINENT)
2. Return Type                    2. Return Type + Start Bot
3. Start Bot          (gruen)     3. Scan Client Table     (sekundaer)
4. Status                         4. Status                (kompakt)
5. Log                            5. Log                   (expandiert)
```

**Kern-Verschiebung:** Die CSV-Datei wird von einem versteckten Sub-Element zur prominentesten Information. "Scan Client Table" wird von der visuell dominanten Position zur sekundaeren Aktion herabgestuft.
