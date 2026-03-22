# Manuelle Testanleitung: Phase 10b-1 + 10b-2

## Voraussetzungen

- TaxAct 2025 auf Primary Monitor (1920x1080)
- Client Manager sichtbar
- Mindestens 3-4 **1040-Clients** mit leerem Fed EF Status
- Falls moeglich: mindestens 1 **gesperrter (locked) 1040-Client**
- Falls moeglich: mindestens 1 **1120S-Client** mit leerem Fed EF Status (Regression)

---

## Test 1: Preprocessing (CSV erstellen)

**Ziel:** Frische CSV als Basis fuer alle weiteren Tests

1. Bot starten, Return-Type **1040** waehlen
2. Klick auf **"Scan Client Table"**
3. Warten bis Scan abgeschlossen

**Achte auf:**
- CSV wird erstellt unter `C:\TaxActBot\logs\clients_....csv`
- GUI zeigt Counts: TODO / Done / Fail
- CSV-Pfad erscheint im File-Picker

**Danach:** CSV in einem Texteditor oeffnen und pruefen:
- Spalten: `Client, ID, Return Type, Status`
- 1040-Clients haben Status `TODO`
- Clients mit bereits eingereichtem Status haben den echten TaxAct-Status (z.B. "Submitted")

---

## Test 2: Normaler 1040-Client (Happy Path + CSV-Update)

**Ziel:** 1040-Prozess laeuft durch alle 19 Stages + CSV wird auf "Submitted" gesetzt

1. Return-Type **1040** in GUI
2. CSV ist geladen (aus Test 1)
3. Klick **"Start Bot"**, zu TaxAct wechseln

**Achte auf (Terminal-Log):**
- `"CSV loaded: X TODO clients for 1040"` — CSV wurde geladen
- Bot waehlt ersten Client mit leerem Fed EF Status
- **Stage 3** (File Extension): Checkbox wird **angeklickt** (unchecked -> checked), dann Continue
  - Kein `locked_2`-Popup -> Bot wartet max. 3s, geht dann weiter (achte auf kurze Pause hier)
- **Stages 4-11**: Durchlauf ohne Besonderheiten (Continue-Klicks)
- **Stage 12**: Acknowledgement-Screen erscheint -> Bot klickt Continue (kein Wizard)
- **Stage 13**: Consent -> Agree
- **Stage 14**: Alerts -> Start Alerts
- **Stage 15**: Third-Party Designee — entweder:
  - Screen erscheint: Bot fuellt 3 Felder (Name, Phone, PIN) + Continue + erneut Start Alerts
  - Screen erscheint nicht: Bot geht weiter
- **Stage 16**: Passed Alerts -> Continue
- **Stage 17**: Submit E-File (bis zu 30s Wartezeit normal!)
- **Stage 18**: Successful -> Continue
- **Stage 19**: Filing Complete -> Clients-Button -> zurueck zum Client Manager

**Nach Abschluss pruefen:**
- GUI: Counts aktualisiert (TODO -1, Done +1)
- CSV oeffnen: Client hat Status **`Submitted`** statt `TODO`

---

## Test 3: Mehrere 1040-Clients im Loop

**Ziel:** Bot verarbeitet 2-3 Clients nacheinander, CSV wird pro Client aktualisiert

1. Bot nochmal starten (gleiche CSV)
2. Laufen lassen fuer 2-3 Clients

**Achte auf:**
- Client aus Test 2 wird **uebersprungen** (nicht mehr TODO in CSV)
- Jeder neue Client: CSV wird sofort nach Abschluss aktualisiert
- Am Ende: GUI-Counts stimmen mit CSV ueberein

---

## Test 4: Locked Client Handling (falls verfuegbar)

**Ziel:** Bot erkennt gesperrten Client und handhabt ihn korrekt

**Voraussetzung:** Ein 1040-Client muss von einem anderen Benutzer gesperrt sein (in TaxAct)

1. Bot starten, 1040 waehlen

**Achte auf nach Doppelklick auf gesperrten Client:**
- **locked_1 Dialog** erscheint (Text enthaelt "Practice Administrator")
  - Bot erkennt `locked_1.png` -> Log: `"Client is locked, dismissing dialog..."`
  - Bot klickt **OK** -> Dialog schliesst sich
- **Stage 3**: Checkbox ist **bereits checked** -> Bot ueberspringt Klick (kein unchecked sichtbar)
  - Continue wird geklickt
  - **locked_2 Popup** erscheint (bis 3s Wartezeit)
  - Bot klickt **"Unlock and Save"**
- Prozess geht normal weiter ab Stage 4

**Falls kein locked Client vorhanden:**
- Ueberspringe diesen Test, notiere es. Kann spaeter nachgeholt werden.

---

## Test 5: Wizard-Abbruch (Stage 12)

**Ziel:** Bot bricht sauber ab wenn statt Acknowledgement der Wizard erscheint

**Voraussetzung:** Ein 1040-Client, bei dem nach E-File der Preparer EF Wizard statt Acknowledgement erscheint (typisch: Client hat noch keine EF-Einrichtung)

1. Bot starten mit solchem Client

**Achte auf bei Stage 12:**
- Bot sucht `12_acknowledgement.png` -> **findet es nicht**
- Log zeigt: abort mit Reason
- Bot klickt **Clients-Button** (oben links, via `search_region [0,0,300,80]`)
- Falls "Save Changes?"-Dialog erscheint: Bot erkennt `no_default.png` und klickt **No**
- Bot kehrt zum Client Manager zurueck

**Nach Abschluss pruefen:**
- CSV: Client hat Status **`FAIL: Wizard (Stage 12)`**
- GUI: Fail-Count +1
- Bot verarbeitet naechsten Client weiter (kein Totalabbruch)

**Falls kein Wizard-Client verfuegbar:**
- Ueberspringe, notiere es.

---

## Test 6: Alerts fehlgeschlagen (Stage 16)

**Ziel:** Bot bricht sauber ab wenn Alerts nicht bestehen

**Voraussetzung:** Ein 1040-Client, bei dem Alerts fehlschlagen (z.B. fehlende Pflichtfelder)

**Achte auf bei Stage 16:**
- Bot sucht `passed_alerts.png` -> **findet es nicht** (Error/Omission statt Passed)
- Bot klickt **Clients-Button** -> zurueck zum Client Manager
- Log zeigt abort_reason

**Nach Abschluss pruefen:**
- CSV: Status **`FAIL: Alerts not passed`**

**Falls kein solcher Client verfuegbar:**
- Ueberspringe, notiere es.

---

## Test 7: Auto-Status-Update aus TaxAct

**Ziel:** Wenn TaxAct einen neueren Status zeigt als die CSV, wird die CSV automatisch aktualisiert

**Voraussetzung:** Clients aus Test 2/3 haben in TaxAct jetzt z.B. "Ext. Accepted" statt "Submitted"

1. CSV oeffnen: Client hat `Submitted`
2. In TaxAct pruefen: gleicher Client zeigt z.B. `Ext. Accepted` in Fed EF Status
3. Bot erneut starten

**Achte auf im Log:**
- `"Status updated: CLIENT_NAME -> Ext. Accepted"` fuer Clients, wo TaxAct-Status neuer ist
- CSV wird aktualisiert ohne dass der Client nochmal verarbeitet wird

**Falls kein Status-Unterschied vorhanden:**
- Ueberspringe — dieser Test ergibt sich oft erst nach einigen Stunden/Tagen, wenn TaxAct den Status aktualisiert.

---

## Test 8: Bot-Restart mit bestehender CSV

**Ziel:** Bereits bearbeitete Clients werden uebersprungen

1. Bot stoppen
2. Bot **erneut starten** (gleiche CSV, gleicher Return-Type)

**Achte auf:**
- TODO-Count ist reduziert (nur verbleibende Clients)
- Bereits als "Submitted" markierte Clients werden **nicht** nochmal verarbeitet
- Bereits als "FAIL: ..." markierte Clients werden **nicht** nochmal verarbeitet

---

## Test 9: 1120S Regression

**Ziel:** 1120S-Prozess funktioniert weiterhin mit CSV

1. Return-Type auf **1120S** umschalten
2. Neues Preprocessing durchfuehren (oder bestehende CSV nutzen — sie enthaelt alle Return Types)
3. Bot starten

**Achte auf:**
- Bot filtert nur 1120S-TODO-Clients aus der CSV
- 1040-Clients werden ignoriert
- 1120S-Prozess laeuft normal (20 Stages)
- CSV wird korrekt aktualisiert

---

## Test 10: Kein CSV geladen

**Ziel:** Fehlermeldung wenn ohne CSV gestartet wird

1. Bot neu starten (frische Sitzung)
2. **Kein** Preprocessing durchfuehren, keinen CSV-Pfad waehlen
3. Klick "Start Bot"

**Achte auf:**
- GUI zeigt Fehlermeldung: `"ERROR: No CSV file loaded"` (oder aehnlich)
- Bot startet **nicht**

---

## Priorisierung

| # | Test | Prioritaet | Braucht spezielle Clients? |
|---|------|-----------|---------------------------|
| 1 | Preprocessing | **Pflicht** | Nein |
| 2 | Normaler 1040 + CSV | **Pflicht** | Nein |
| 3 | Loop (mehrere Clients) | **Pflicht** | Nein |
| 8 | Bot-Restart | **Pflicht** | Nein |
| 10 | Kein CSV | **Pflicht** | Nein |
| 4 | Locked Client | Wenn verfuegbar | Ja (gesperrter Client) |
| 5 | Wizard-Abbruch | Wenn verfuegbar | Ja (Wizard-Client) |
| 6 | Alerts fehlgeschlagen | Wenn verfuegbar | Ja (Alerts-Fail-Client) |
| 7 | Auto-Status-Update | Wenn verfuegbar | Erst nach Statusaenderung in TaxAct |
| 9 | 1120S Regression | Empfohlen | Ja (1120S-Client) |

---

## Ergebnisse

| # | Test | Ergebnis | Notizen |
|---|------|----------|---------|
| 1 | Preprocessing | | |
| 2 | Normaler 1040 + CSV | | |
| 3 | Loop | | |
| 4 | Locked Client | | |
| 5 | Wizard-Abbruch | | |
| 6 | Alerts fehlgeschlagen | | |
| 7 | Auto-Status-Update | | |
| 8 | Bot-Restart | | |
| 9 | 1120S Regression | | |
| 10 | Kein CSV | | |
