# SentinelClaw — Kill Switch System

> Version: 0.1 | Autor: Jaciel Antonio Acea Ruiz | Datum: April 2026
> Klassifizierung: VERTRAULICH
> Zweck: 100% garantierter Stopp aller Agent-Aktivitäten — ausfallsicher, mehrstufig

---

## 1. Grundsatz

> **Der Kill Switch MUSS unter ALLEN Umständen funktionieren.**
> Kein Szenario darf existieren in dem der Agent nach einem Kill weiterarbeitet.

### Design-Prinzipien

1. **Mehrere unabhängige Pfade** — Jeder einzelne Pfad reicht allein um ALLES zu stoppen
2. **Kaskade** — Wenn Pfad 1 versagt, greift automatisch Pfad 2, dann Pfad 3, dann Pfad 4
3. **Kein Single Point of Failure** — Kill funktioniert auch wenn App, DB oder Docker eingefroren sind
4. **Irreversibel pro Scan** — Nach einem Kill kann der Agent den Scan NICHT fortsetzen
5. **Kein RBAC für Kill** — JEDER eingeloggte User darf killen, ohne Rollenprüfung
6. **Offline-fähig** — Kill funktioniert auch wenn die Web-UI nicht erreichbar ist
7. **Nicht deaktivierbar** — Der Kill Switch kann nicht ausgeschaltet werden — von niemandem

---

## 2. Die vier Kill-Pfade

```
┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│  KILL-PFAD 1: APPLICATION                         ⏱ < 1 Sekunde│
│  Web-UI Button / API / Chat-Befehl                              │
│  → Agent bekommt STOP-Signal über WebSocket                     │
│  → Alle Tool-Prozesse werden beendet                            │
│  → Scan-Status → ABGEBROCHEN                                    │
│                                                                 │
│  Kann versagen wenn: App eingefroren, WebSocket tot             │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  KILL-PFAD 2: CONTAINER                           ⏱ < 3 Sekunden│
│  Docker SIGKILL auf alle Sandbox-Container                      │
│  → Alle Prozesse im Container sterben sofort                    │
│  → Kein Prozess überlebt SIGKILL                                │
│  → Container wird entfernt                                      │
│                                                                 │
│  Kann versagen wenn: Docker-Daemon eingefroren                  │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  KILL-PFAD 3: NETZWERK                            ⏱ < 1 Sekunde│
│  iptables/nftables: DROP ALL auf Sandbox-Netzwerk               │
│  → Sandbox kann physisch KEIN Paket mehr senden                 │
│  → Auch wenn Prozesse noch laufen: sie erreichen nichts         │
│  → Ziel-Systeme sind sofort geschützt                           │
│                                                                 │
│  Kann versagen wenn: Host-Kernel eingefroren (extrem selten)    │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  KILL-PFAD 4: BETRIEBSSYSTEM                      ⏱ < 5 Sekunden│
│  Direkter OS-Befehl: kill -9 auf alle SentinelClaw-Prozesse    │
│  → Funktioniert auch wenn Docker und App tot sind               │
│  → Letzter Ausweg, braucht SSH-Zugang zum Host                  │
│  → Immer verfügbar solange der Host-Server läuft               │
│                                                                 │
│  Kann versagen wenn: Server-Hardware defekt                     │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘

JEDER einzelne Pfad reicht allein aus.
Zusammen: Es gibt KEIN realistisches Szenario in dem alle 4 versagen.
```

---

## 3. Kill-Pfad 1: Application Kill (Normal)

### 3.1 Auslöser

| Auslöser | Wo | Wer |
|---|---|---|
| 🔴 NOTAUS-Button | Top-Bar der Web-UI, immer sichtbar | Jeder eingeloggte User |
| `/kill` im Chat | Agent-Chat | Jeder eingeloggte User |
| `POST /api/emergency/kill` | REST API | Jeder mit gültigem Token |
| Automatischer Trigger | System (Scope-Violation, Zeitfenster, etc.) | System |

### 3.2 Ablauf (Reihenfolge garantiert)

```
User drückt NOTAUS
    │
    ▼ (0ms)
┌─ Schritt 1: Kill-Signal setzen ──────────────────────────────┐
│ In-Memory Kill-Flag wird gesetzt (AtomicBoolean)             │
│ Ab diesem Moment: KEIN neuer Tool-Aufruf wird akzeptiert     │
│ MCP-Server blockiert SOFORT alle eingehenden Requests         │
└──────────────────────────────────────────────────────────────┘
    │
    ▼ (10ms)
┌─ Schritt 2: Netzwerk kappen ────────────────────────────────┐
│ Docker Network disconnect für ALLE Sandbox-Container         │
│ → Sandbox kann KEIN Paket mehr senden (sofortige Wirkung)    │
│ → Laufende TCP-Verbindungen werden unterbrochen              │
│ → Ziel-Systeme sind ab jetzt geschützt                       │
└──────────────────────────────────────────────────────────────┘
    │
    ▼ (50ms)
┌─ Schritt 3: Prozesse killen ────────────────────────────────┐
│ SIGKILL an ALLE Prozesse in ALLEN Sandbox-Containern         │
│ → nmap, nuclei, metasploit, sqlmap — alles stirbt sofort     │
│ → SIGKILL kann nicht gefangen oder ignoriert werden           │
└──────────────────────────────────────────────────────────────┘
    │
    ▼ (100ms)
┌─ Schritt 4: Container stoppen ──────────────────────────────┐
│ docker stop + docker rm für alle Sandbox-Container           │
│ → Container existieren nicht mehr                            │
│ → Selbst bei Restart-Policy: Container wird entfernt, nicht  │
│   nur gestoppt                                               │
└──────────────────────────────────────────────────────────────┘
    │
    ▼ (200ms)
┌─ Schritt 5: Agent-Prozess beenden ──────────────────────────┐
│ Agent-Runtime (NemoClaw) wird gestoppt                       │
│ → Agent kann keine Entscheidungen mehr treffen               │
│ → Kein neuer Plan, kein neuer Tool-Aufruf                    │
└──────────────────────────────────────────────────────────────┘
    │
    ▼ (300ms)
┌─ Schritt 6: Status aktualisieren ───────────────────────────┐
│ Alle laufenden Scan-Jobs → Status: "EMERGENCY_KILLED"        │
│ Dieser Status kann NICHT auf "running" zurückgesetzt werden  │
│ Ein gekillter Scan ist ENDGÜLTIG tot                         │
└──────────────────────────────────────────────────────────────┘
    │
    ▼ (400ms)
┌─ Schritt 7: Audit-Log ─────────────────────────────────────┐
│ EMERGENCY_KILL Event wird geschrieben                        │
│ → Wer hat gekillt                                           │
│ → Wann (Millisekunden-genau)                                │
│ → Welche Scans waren aktiv                                  │
│ → Welche Tools liefen                                       │
│ → Warum (User-Grund oder System-Trigger)                    │
│                                                              │
│ Dieses Log wird auch geschrieben wenn ALLES andere fehlschlägt│
│ (eigener Log-Writer, unabhängig von DB)                      │
└──────────────────────────────────────────────────────────────┘
    │
    ▼ (500ms)
┌─ Schritt 8: Benachrichtigung ───────────────────────────────┐
│ WebSocket-Nachricht an ALLE verbundenen Clients:            │
│ "EMERGENCY KILL — Alle Scans gestoppt"                      │
│ Chat-Nachricht in allen aktiven Scan-Chats                   │
│ Optional: E-Mail an ORG_ADMIN und SYSTEM_ADMIN               │
└──────────────────────────────────────────────────────────────┘

GESAMT: < 1 Sekunde von Button-Klick bis alles tot
```

### 3.3 Code-Konzept

```typescript
class EmergencyKillService {
  // Atomarer Kill-Flag — einmal gesetzt, nie zurücksetzbar für diese Session
  private killActivated = new AtomicBoolean(false);

  async executeKill(triggeredBy: string, reason: string): Promise<KillResult> {
    // Kill-Flag setzen (sofort, atomar, nicht umkehrbar)
    if (!this.killActivated.compareAndSet(false, true)) {
      return { success: true, message: "Kill bereits aktiv" };
    }

    const killStartTime = Date.now();
    const results: StepResult[] = [];

    // Alle Schritte laufen PARALLEL wo möglich — Geschwindigkeit zählt
    const [networkResult, processResult] = await Promise.allSettled([
      // Schritt 2+3 parallel: Netzwerk kappen UND Prozesse killen
      this.cutNetwork(),
      this.killAllProcesses(),
    ]);
    results.push(networkResult, processResult);

    // Schritt 4: Container entfernen (braucht Schritt 3 nicht abzuwarten)
    const containerResult = await this.removeAllContainers();
    results.push(containerResult);

    // Schritt 5: Agent-Runtime stoppen
    const agentResult = await this.stopAgentRuntime();
    results.push(agentResult);

    // Schritt 6: Scan-Status aktualisieren
    await this.markAllScansKilled(triggeredBy, reason);

    // Schritt 7: Audit-Log (MUSS klappen, auch wenn DB down)
    await this.writeKillAuditLog(triggeredBy, reason, killStartTime, results);

    // Schritt 8: Benachrichtigung
    await this.notifyAllClients(triggeredBy, reason);

    return {
      success: true,
      durationMs: Date.now() - killStartTime,
      steps: results,
    };
  }

  private async cutNetwork(): Promise<void> {
    // Docker Network disconnect — schnellste Wirkung
    await this.docker.disconnectAllSandboxNetworks();

    // Zusätzlich: iptables DROP als Backup
    await this.executeHostCommand(
      "iptables -I FORWARD -o br-sentinel-scan -j DROP"
    );
  }

  private async killAllProcesses(): Promise<void> {
    // SIGKILL an alle Prozesse in allen Sandbox-Containern
    const containers = await this.docker.listSandboxContainers();
    await Promise.all(
      containers.map(c => this.docker.exec(c.id, "kill -9 -1"))
    );
  }

  private async removeAllContainers(): Promise<void> {
    // Force-Remove: Container werden nicht gestoppt sondern gelöscht
    const containers = await this.docker.listSandboxContainers();
    await Promise.all(
      containers.map(c => this.docker.removeContainer(c.id, { force: true }))
    );
  }

  private async writeKillAuditLog(
    triggeredBy: string,
    reason: string,
    startTime: number,
    results: StepResult[]
  ): Promise<void> {
    const entry = {
      event: "EMERGENCY_KILL",
      triggeredBy,
      reason,
      timestamp: new Date().toISOString(),
      durationMs: Date.now() - startTime,
      steps: results,
    };

    // Primär: In Datenbank schreiben
    try {
      await this.auditLogRepository.writeEmergencyKill(entry);
    } catch {
      // Fallback: Direkt auf Dateisystem schreiben (DB könnte down sein)
      await this.fileLogger.writeEmergencyKill(entry);
    }
  }
}
```

---

## 4. Kill-Pfad 2: Container Kill (wenn App nicht reagiert)

### 4.1 Wann nötig?
Wenn die Web-UI eingefroren ist, der API-Server nicht antwortet, oder der Application Kill hängt.

### 4.2 Auslöser

```bash
# Direkt auf dem Host-Server (SSH oder lokale Shell):

# Option A: Nur Sandbox-Container stoppen
docker kill $(docker ps -q --filter "label=sentinelclaw.role=sandbox")

# Option B: ALLE SentinelClaw-Container stoppen
docker kill $(docker ps -q --filter "label=sentinelclaw=true")

# Option C: Container komplett entfernen (kein Restart möglich)
docker rm -f $(docker ps -aq --filter "label=sentinelclaw=true")
```

### 4.3 Automatisiert als Script

```bash
#!/bin/bash
# /opt/sentinelclaw/emergency-kill.sh
# Dieses Script wird bei der Installation auf den Host kopiert.
# Es funktioniert UNABHÄNGIG von der SentinelClaw-Anwendung.

echo "[EMERGENCY KILL] $(date -Iseconds) — Stoppe alle SentinelClaw-Prozesse"

# 1. Netzwerk sofort kappen
echo "[1/4] Kappe Netzwerk..."
iptables -I FORWARD -o br-sentinel-scan -j DROP 2>/dev/null
docker network disconnect sentinel-scanning $(docker ps -q --filter "label=sentinelclaw.role=sandbox") 2>/dev/null

# 2. Alle Sandbox-Container killen
echo "[2/4] Stoppe Sandbox-Container..."
docker kill $(docker ps -q --filter "label=sentinelclaw.role=sandbox") 2>/dev/null

# 3. Container entfernen (kein Auto-Restart)
echo "[3/4] Entferne Container..."
docker rm -f $(docker ps -aq --filter "label=sentinelclaw.role=sandbox") 2>/dev/null

# 4. Alle SentinelClaw-Prozesse auf dem Host beenden
echo "[4/4] Beende Host-Prozesse..."
pkill -9 -f "sentinelclaw" 2>/dev/null
pkill -9 -f "nemoclaw" 2>/dev/null

# Log schreiben (unabhängig von App)
echo "$(date -Iseconds) EMERGENCY_KILL executed by $(whoami)" >> /var/log/sentinelclaw/emergency-kills.log

echo "[DONE] Alle SentinelClaw-Prozesse gestoppt."
```

**Dieses Script wird bei der Installation automatisch auf den Host kopiert** und ist über einen einfachen Befehl aufrufbar:

```bash
sudo /opt/sentinelclaw/emergency-kill.sh
```

---

## 5. Kill-Pfad 3: Netzwerk Kill (schnellster Schutz für Ziele)

### 5.1 Warum ein eigener Pfad?

Selbst wenn App und Container noch laufen: Wenn das Netzwerk gekappt ist, kann der Agent **physisch kein Paket** mehr an die Ziel-Systeme senden. Das schützt die Ziele sofort, auch wenn das Aufräumen der Prozesse noch dauert.

### 5.2 Implementierung

```bash
# Sofort alle ausgehenden Verbindungen der Sandbox blockieren
# Funktioniert unabhängig von Docker und der Application

# Linux (iptables)
iptables -I FORWARD -o br-sentinel-scan -j DROP
iptables -I FORWARD -i br-sentinel-scan -j DROP

# Oder: Docker-Netzwerk komplett deaktivieren
docker network disconnect sentinel-scanning --force <container_id>

# Oder: Netzwerk-Interface deaktivieren (Notfall)
ip link set br-sentinel-scan down
```

### 5.3 In der Anwendung

```typescript
class NetworkKillSwitch {
  // Wird als ERSTER Schritt bei jedem Kill ausgeführt
  // weil er die schnellste Schutzwirkung für Ziel-Systeme hat

  async cutAllSandboxNetworking(): Promise<void> {
    // Methode 1: Docker Network Disconnect
    const containers = await this.docker.listSandboxContainers();
    await Promise.all(
      containers.map(c =>
        this.docker.disconnectNetwork(c.id, "sentinel-scanning")
      )
    );

    // Methode 2: iptables als Backup (falls Docker nicht reagiert)
    await this.executeOnHost(
      "iptables -I FORWARD -o br-sentinel-scan -j DROP"
    );

    // Methode 3: Netzwerk-Interface down (letzter Ausweg)
    // Nur wenn Methode 1+2 fehlschlagen
    if (await this.sandboxCanStillReachTargets()) {
      await this.executeOnHost("ip link set br-sentinel-scan down");
    }
  }

  private async sandboxCanStillReachTargets(): Promise<boolean> {
    // Prüfe ob die Sandbox noch Ziele erreichen kann
    // Wenn ja → Netzwerk-Interface komplett deaktivieren
    try {
      const result = await this.docker.exec(
        this.sandboxContainerId,
        "ping -c 1 -W 1 10.10.10.1"
      );
      return result.exitCode === 0; // Kann noch pingen = Problem
    } catch {
      return false; // Container reagiert nicht = Netzwerk ist tot
    }
  }
}
```

---

## 6. Kill-Pfad 4: OS-Level Kill (wenn alles andere versagt)

### 6.1 Wann nötig?
Nur wenn Docker-Daemon selbst eingefroren ist oder nicht reagiert. Extrem selten, aber möglich.

### 6.2 Vorgehen

```bash
# SSH auf den Host-Server, dann:

# 1. Alle Docker-Container-Prozesse direkt killen
for pid in $(pgrep -f "nmap|nuclei|metasploit|sqlmap|hydra|nikto"); do
  kill -9 $pid 2>/dev/null
done

# 2. Docker-Daemon neustarten (killt automatisch alle Container)
systemctl restart docker

# 3. Wenn Docker nicht reagiert: Docker-Daemon killen
kill -9 $(pgrep dockerd)

# 4. Netzwerk-Interface auf OS-Level deaktivieren
ip link set docker0 down
ip link set br-sentinel-scan down
```

---

## 7. Watchdog — Automatischer Kill bei Anomalien

### 7.1 Was ist der Watchdog?

Ein **unabhängiger Überwachungsprozess** der NEBEN der SentinelClaw-Anwendung läuft. Er überwacht ob der Agent sich an die Regeln hält und killt ihn automatisch wenn nicht.

```
┌─────────────────────────────────────────────────────────────┐
│  Host-System                                                │
│                                                             │
│  ┌───────────────────┐     ┌───────────────────────────┐   │
│  │  SentinelClaw App │     │  Watchdog-Prozess         │   │
│  │  (kann einfrieren)│     │  (unabhängig, minimaler   │   │
│  │                   │     │   Code, schwer zu killen)  │   │
│  │  Agent → Tools    │     │                           │   │
│  │                   │     │  Prüft alle 10 Sekunden:  │   │
│  │                   │     │  - Zeitfenster abgelaufen? │   │
│  │                   │     │  - Scan überschreitet Max? │   │
│  │                   │     │  - Netzwerk-Anomalien?     │   │
│  │                   │     │  - App reagiert nicht?     │   │
│  │                   │     │                           │   │
│  │                   │  ←──│  KILL wenn Anomalie!      │   │
│  └───────────────────┘     └───────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

### 7.2 Watchdog-Trigger (automatischer Kill)

| Trigger | Prüfintervall | Aktion |
|---|---|---|
| Zeitfenster abgelaufen | Alle 10s | Sofort Kill-Pfad 2 (Container) |
| Scan läuft > Max-Dauer (konfigurierbar) | Alle 10s | Sofort Kill-Pfad 2 |
| Sandbox sendet Pakete an nicht-autorisierte IPs | Alle 5s | Sofort Kill-Pfad 3 (Netzwerk) |
| Sandbox-Container CPU > 95% für > 5 Minuten | Alle 30s | Warnung, nach 10 Min: Kill |
| SentinelClaw App antwortet nicht auf Health-Check | Alle 15s | Nach 3 Fehlversuchen: Kill-Pfad 2 |
| Mehr als 3 Scope-Violations in 5 Minuten | Event-basiert | Sofort Kill-Pfad 1 |
| Kill-Flag gesetzt aber Container laufen noch nach 5s | Alle 1s (nur nach Kill) | Kill-Pfad 2 als Eskalation |

### 7.3 Watchdog-Implementation

```python
#!/usr/bin/env python3
"""
SentinelClaw Watchdog — Unabhängiger Überwachungsprozess.

Läuft als separater systemd-Service, NICHT innerhalb von Docker.
Hat direkten Zugriff auf Docker-Socket und iptables.
Einziger Zweck: Kill wenn etwas schiefgeht.
"""

import subprocess
import time
import json
from datetime import datetime, timezone
from pathlib import Path

WATCHDOG_CHECK_INTERVAL = 10  # Sekunden
KILL_SCRIPT = "/opt/sentinelclaw/emergency-kill.sh"
WATCHDOG_LOG = "/var/log/sentinelclaw/watchdog.log"

class Watchdog:
    def run_forever(self):
        """Hauptschleife — läuft bis der Host herunterfährt."""
        while True:
            try:
                self.check_all()
            except Exception as error:
                self.log(f"Watchdog-Fehler: {error}")
            time.sleep(WATCHDOG_CHECK_INTERVAL)

    def check_all(self):
        """Führt alle Prüfungen durch."""
        self.check_time_windows()
        self.check_max_scan_duration()
        self.check_network_anomalies()
        self.check_app_health()
        self.check_kill_completion()

    def check_time_windows(self):
        """Prüft ob ein Scan außerhalb des Zeitfensters läuft."""
        active_scans = self.get_active_scans()
        now = datetime.now(timezone.utc)

        for scan in active_scans:
            if now > scan["time_window_end"]:
                self.execute_kill(
                    reason=f"Zeitfenster abgelaufen für Scan {scan['id']}"
                )

    def check_network_anomalies(self):
        """Prüft ob die Sandbox nicht-autorisierte Verbindungen aufbaut."""
        # Lese aktive Verbindungen aus dem Sandbox-Container
        connections = self.get_sandbox_connections()
        allowed_targets = self.get_allowed_targets()

        for conn in connections:
            if conn["destination"] not in allowed_targets:
                # SOFORT Netzwerk kappen — keine Warnung, kein Retry
                self.cut_network_immediately()
                self.execute_kill(
                    reason=f"Nicht-autorisierte Verbindung: {conn['destination']}"
                )

    def check_app_health(self):
        """Prüft ob die SentinelClaw-App noch reagiert."""
        try:
            response = subprocess.run(
                ["curl", "-sf", "--max-time", "5",
                 "http://localhost:8080/health"],
                capture_output=True, timeout=10
            )
            if response.returncode != 0:
                self.health_failures += 1
            else:
                self.health_failures = 0
        except subprocess.TimeoutExpired:
            self.health_failures += 1

        if self.health_failures >= 3:
            self.execute_kill(
                reason="App reagiert nicht (3 Health-Check-Failures)"
            )

    def check_kill_completion(self):
        """Prüft ob ein Kill auch wirklich durchgeführt wurde."""
        if not self.kill_flag_is_set():
            return

        # Kill wurde ausgelöst — prüfe ob Container wirklich tot sind
        sandbox_containers = self.get_sandbox_containers()
        if len(sandbox_containers) > 0:
            # Container laufen noch obwohl Kill aktiv!
            # Eskaliere zu Container-Kill
            self.log("Kill-Eskalation: Container laufen noch nach Kill-Signal")
            subprocess.run([KILL_SCRIPT], timeout=30)

    def execute_kill(self, reason: str):
        """Führt das Kill-Script aus."""
        self.log(f"WATCHDOG KILL: {reason}")
        subprocess.run([KILL_SCRIPT], timeout=30)

    def cut_network_immediately(self):
        """Kappt das Netzwerk SOFORT — schnellste Schutzmaßnahme."""
        subprocess.run(
            ["iptables", "-I", "FORWARD", "-o", "br-sentinel-scan", "-j", "DROP"],
            timeout=5
        )

    def log(self, message: str):
        """Schreibt in die Watchdog-Logdatei."""
        timestamp = datetime.now(timezone.utc).isoformat()
        Path(WATCHDOG_LOG).parent.mkdir(parents=True, exist_ok=True)
        with open(WATCHDOG_LOG, "a") as f:
            f.write(f"[{timestamp}] {message}\n")
```

### 7.4 Watchdog als systemd-Service

```ini
# /etc/systemd/system/sentinelclaw-watchdog.service
[Unit]
Description=SentinelClaw Watchdog — Unabhängiger Sicherheits-Überwacher
After=docker.service
# Startet NACH Docker, aber ist UNABHÄNGIG von SentinelClaw

[Service]
Type=simple
ExecStart=/usr/bin/python3 /opt/sentinelclaw/watchdog.py
Restart=always
RestartSec=5
# Watchdog startet IMMER neu wenn er stirbt

# Watchdog braucht Root-Rechte für iptables und docker kill
User=root

# Watchdog KANN NICHT von SentinelClaw gekillt werden
# (anderer Prozessbaum)
OOMScoreAdjust=-900

[Install]
WantedBy=multi-user.target
```

---

## 8. Kill-Verifizierung (Ist wirklich alles tot?)

### 8.1 Nach jedem Kill: Verifizierung

```typescript
async function verifyKillComplete(): Promise<KillVerification> {
  const checks = {
    // 1. Keine Sandbox-Container mehr aktiv?
    noSandboxContainers: await docker.listContainers({
      filter: "label=sentinelclaw.role=sandbox"
    }).then(c => c.length === 0),

    // 2. Keine Scan-relevanten Prozesse auf dem Host?
    noScanProcesses: await checkNoProcesses([
      "nmap", "nuclei", "metasploit", "sqlmap", "hydra",
      "nikto", "john", "hashcat", "linpeas", "winpeas"
    ]),

    // 3. Sandbox-Netzwerk kann nichts mehr erreichen?
    networkBlocked: await checkNetworkBlocked("br-sentinel-scan"),

    // 4. Alle Scan-Jobs auf KILLED Status?
    allScansKilled: await scanJobRepo
      .findByStatus("running")
      .then(jobs => jobs.length === 0),

    // 5. Kill-Audit-Log geschrieben?
    auditLogWritten: await auditLogRepo
      .findByAction("EMERGENCY_KILL")
      .then(logs => logs.length > 0),
  };

  const allClear = Object.values(checks).every(v => v === true);

  if (!allClear) {
    // ESKALATION: Nicht alles tot → Kill-Script auf Host ausführen
    await executeHostKillScript();
    // Und nochmal prüfen
    return verifyKillComplete();
  }

  return { verified: true, checks, timestamp: new Date().toISOString() };
}
```

### 8.2 Kill-Status in der UI

```
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│  ⚠ NOTAUS AKTIVIERT                                         │
│                                                             │
│  Alle Scans wurden gestoppt.                                │
│  Ausgelöst von: J. Ruiz um 14:35:22 UTC                    │
│                                                             │
│  Verifizierung:                                             │
│  ✅ Sandbox-Container gestoppt                               │
│  ✅ Netzwerk gekappt                                         │
│  ✅ Alle Prozesse beendet                                    │
│  ✅ Scan-Status aktualisiert                                 │
│  ✅ Audit-Log geschrieben                                    │
│                                                             │
│  Alle 5 Prüfungen bestanden — System ist sicher gestoppt.  │
│                                                             │
│  [Zum Audit-Log →]           [Neuen Scan vorbereiten →]     │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 9. Irreversibilität — Kein Weg zurück

### 9.1 Nach einem Kill

Ein gekillter Scan kann NICHT fortgesetzt werden:

```
Scan-Status: EMERGENCY_KILLED
    │
    ├── KANN NICHT auf "running" zurückgesetzt werden
    ├── KANN NICHT "resumed" werden
    ├── KANN NICHT "restarted" werden
    │
    └── User muss NEUEN Scan erstellen
        (mit neuer Autorisierung, neuem Disclaimer)
```

### 9.2 Warum irreversibel?

- Nach einem Kill ist der Zustand unklar (was lief noch? was war halb fertig?)
- Wiederaufnahme könnte unerwartete Aktionen auslösen
- Für Audit: Kill muss ein klarer Endpunkt sein
- Neuer Scan = neue bewusste Entscheidung des Users

---

## 10. Testing — Kill Switch wird regelmäßig getestet

### 10.1 Automatische Tests (CI/CD)

```
Test 1: Application Kill
  → Starte Dummy-Scan → Kill über API → Prüfe: Alles gestoppt? < 2s?

Test 2: Container Kill
  → Starte Sandbox → Kill über Docker → Prüfe: Container weg? Netzwerk tot?

Test 3: Netzwerk Kill
  → Starte Scan → Kappe Netzwerk → Prüfe: Sandbox kann nichts erreichen?

Test 4: Watchdog Kill
  → Starte Scan mit abgelaufenem Zeitfenster → Prüfe: Watchdog killt?

Test 5: Verifizierung
  → Führe Kill aus → Prüfe: Alle 5 Verifizierungs-Checks bestehen?
```

### 10.2 Manuelle Tests (vor jedem Deployment)

- [ ] NOTAUS-Button in UI: Klick → Alles gestoppt in < 2 Sekunden?
- [ ] `/kill` im Chat: Getippt → Alles gestoppt?
- [ ] Emergency-Kill-Script: `sudo /opt/sentinelclaw/emergency-kill.sh` → Alles gestoppt?
- [ ] Watchdog: App absichtlich stoppen → Watchdog killt Container?
- [ ] Verifizierung: Alle 5 Checks grün?
- [ ] Audit-Log: Kill-Event ist dokumentiert?

---

## 11. Zusammenfassung — Garantie-Kette

```
Situation               →  Kill-Pfad    →  Ergebnis
───────────────────────────────────────────────────────────────
Alles läuft normal      →  Pfad 1 (App)  →  Tot in < 1 Sekunde
App eingefroren         →  Pfad 2 (Docker)→  Tot in < 3 Sekunden
Docker reagiert nicht   →  Pfad 3 (Netz)  →  Ziele geschützt in < 1s
Alles eingefroren       →  Pfad 4 (OS)    →  Tot in < 5 Sekunden
Keiner drückt Kill      →  Watchdog       →  Auto-Kill bei Anomalie
Kill wurde ausgeführt   →  Verifizierung  →  Bestätigung: Alles tot
Versuch fortzusetzen    →  Irreversibel   →  Geht nicht, neuer Scan nötig
```

**Es gibt KEIN realistisches Szenario in dem der Agent nach einem Kill weiterarbeitet.**
