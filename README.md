# 💸 Personal Finance Dashboard

Ein interaktives, leichtgewichtiges Dashboard zur Analyse privater Finanzen. Entwickelt mit Python und Streamlit, optimiert für den Einsatz als Docker-Container auf einem Home-Server.

Dieses Tool visualisiert Einnahmen und Ausgaben aus einer einfachen CSV-Datei, berechnet die Sparquote und ermöglicht detaillierte Drill-Downs in einzelne Buchungskategorien.

![Python](https://img.shields.io/badge/Python-3.11-blue?logo=python)
![Streamlit](https://img.shields.io/badge/Streamlit-App-red?logo=streamlit)
![Docker](https://img.shields.io/badge/Docker-Ready-blue?logo=docker)

## ✨ Funktionen

* **360° Finanzübersicht:** Unterscheidung zwischen Einnahmen (Grün) und Ausgaben (Rot).
* **Interaktive Grafiken:** Kuchendiagramme für Kategorien und Balkendiagramme für den monatlichen Trend (Plotly).
* **KPIs:** Automatische Berechnung von Gesamtausgaben, Einnahmen und Sparquote.
* **CSV-Upload:** Einfacher Upload neuer Monatsabrechnungen direkt über die Web-Oberfläche.
* **Daten-Persistenz:** Alle Daten werden in einer lokalen `master_ausgaben.csv` gespeichert und gemerged.
* **Filter:** Zeiträume und Kategorien lassen sich dynamisch filtern.

## 🚀 Installation & Start

### Variante 1: Mit Docker (Empfohlen)

Das Projekt enthält eine `docker-compose.yml` für den schnellen Start.

1.  **Repository klonen:**
    ```bash
    git clone [https://github.com/DEIN_USERNAME/DEIN_REPOSITORY.git](https://github.com/DEIN_USERNAME/DEIN_REPOSITORY.git)
    cd DEIN_REPOSITORY
    ```

2.  **Initiale Daten-Datei erstellen:**
    Damit Docker das Volume korrekt mountet, muss die CSV-Datei existieren (auch wenn sie leer ist).
    ```bash
    touch master_ausgaben.csv
    ```

3.  **Container starten:**
    ```bash
    docker compose up -d --build
    ```

4.  **Zugriff:**
    Öffne deinen Browser und gehe auf `http://localhost:8501` (oder die IP deines Servers).

### Variante 2: Lokal mit Python

Voraussetzung: Python 3.10 oder höher.

1.  **Abhängigkeiten installieren:**
    ```bash
    pip install -r requirements.txt
    ```

2.  **App starten:**
    ```bash
    streamlit run app.py
    ```

## 📂 Datenstruktur

Das Dashboard erwartet CSV-Dateien (beim Upload und in der `master_ausgaben.csv`) mit folgendem Format. 
**Trennzeichen:** Komma (`,`).

| Spalte | Format | Beschreibung |
| :--- | :--- | :--- |
| **Datum** | `DD.MM.YYYY` | Buchungsdatum (z.B. 24.11.2025) |
| **Detail** | Text | Beschreibung der Buchung / Händler |
| **Betrag CHF** | Zahl (Float) | `50.00` (Ausgabe) oder `-5000.00` (Einnahme). Keine Tausendertrennzeichen! |
| **Kategorie** | Text | z.B. "Lebensmittel", "Mobilität", "Wohnen" |

> **Hinweis:** Einnahmen müssen als **negative** Werte importiert werden, damit die Logik der App (Einnahmen vs. Ausgaben) korrekt funktioniert.

## ⚠️ Datenschutz & Sicherheit

Dies ist ein öffentliches Repository. **Lade NIEMALS deine echte `master_ausgaben.csv` mit echten Finanzdaten hier hoch!**

1.  Die Datei `master_ausgaben.csv` ist bereits in der `.gitignore` hinterlegt, um versehentliche Uploads zu verhindern.
2.  Wenn du das Repository forkst oder klonst, arbeite lokal mit deinen echten Daten, aber pushe nur den Code.

## 🛠 Tech Stack

* **Frontend/Backend:** [Streamlit](https://streamlit.io/)
* **Datenverarbeitung:** [Pandas](https://pandas.pydata.org/)
* **Visualisierung:** [Plotly Express](https://plotly.com/python/plotly-express/)
* **Deployment:** Docker & Docker Compose

## 📝 Lizenz

Dieses Projekt ist lizenziert unter der MIT Lizenz.