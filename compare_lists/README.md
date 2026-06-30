# compare_lists

Vergleicht zwei Mitgliederlisten im CSV-Format anhand von **Vorname**, **Nachname** und **Straße** und gibt vier Ergebnislisten aus.

## Ergebnisse

| Ausgabedatei | Inhalt |
|---|---|
| `nur_in_Bank_Datei.csv` | Mitglieder nur in Liste 1 (CSV) |
| `nur_in_Ame_Datei.csv` | Mitglieder nur in Liste 2 (CSV) |
| `in_beiden_listen.csv` | Mitglieder in beiden Listen |
| `gleicher_name_unterschiedliche_strasse.csv` | Gleicher Nachname/Vorname in beiden Listen, aber unterschiedliche Straße (zeigt Straße aus beiden Quellen) |

## Voraussetzungen

```bash
pip install -r requirements.txt
```

## Eingabedateien

### Liste 1 – CSV-Datei

Die CSV-Datei muss eine Kopfzeile mit den Spalten **`Nachname`**, **`Vorname`** und **`Straße`** enthalten (in beliebiger Reihenfolge, weitere Spalten werden ignoriert).

### Liste 2 – CSV-Datei

Die CSV-Datei muss eine Kopfzeile mit den Spalten **`Nachname`**, **`Vorname`** und **`Postanschrift2`** enthalten (in beliebiger Reihenfolge, weitere Spalten werden ignoriert).

Die Spalte **`Postanschrift2`** wird intern als **`Straße`** verwendet.

Unterstützte Encodings: UTF-8 (mit oder ohne BOM), CP1252, Latin-1.
Das Trennzeichen wird automatisch erkannt (z. B. `,` oder `;`).

Die Ausgabedateien werden als **UTF-8 mit BOM** gespeichert, damit Umlaute in Excel unter Windows korrekt angezeigt werden.

## Verwendung

```bash
python compare_lists.py LISTE1.csv LISTE2.csv
```

### Optionen

```
positional arguments:
  csv_file1             Source list 1: CSV file with Nachname, Vorname and Straße columns. The header row is read from the first line.
  csv_file2             Source list 2: CSV file with Nachname, Vorname and Postanschrift2 columns

options:
  --output-dir DIR      Directory for the four output CSV files (default: current directory)
  -h, --help            show this help message and exit
```

### Beispiel

```bash
python compare_lists.py bank.csv ame.csv --output-dir ergebnisse/
```

Der Vergleich erfolgt **groß-/kleinschreibungsunabhängig** auf der Kombination (Nachname, Vorname, Straße).
