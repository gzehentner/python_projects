# compare_lists

Vergleicht zwei Mitgliederlisten (eine im ODT-Format, eine im CSV-Format) anhand von **Vorname** und **Nachname** und gibt drei Ergebnislisten aus.

## Ergebnisse

| Ausgabedatei | Inhalt |
|---|---|
| `nur_in_liste1.csv` | Mitglieder nur in Liste 1 (ODT) |
| `nur_in_liste2.csv` | Mitglieder nur in Liste 2 (CSV) |
| `in_beiden_listen.csv` | Mitglieder in beiden Listen |

## Voraussetzungen

```bash
pip install -r requirements.txt
```

## Eingabedateien

### Liste 1 – ODT-Datei (LibreOffice Writer Tabelle)

Die ODT-Datei muss eine Tabelle enthalten. Es werden keine Spaltenüberschriften erwartet:

- **Spalte 2** → Nachname
- **Spalte 3** → Vorname

### Liste 2 – CSV-Datei

Die CSV-Datei muss eine Kopfzeile mit den Spalten **`Nachname`** und **`Vorname`** enthalten (in beliebiger Reihenfolge, weitere Spalten werden ignoriert).

Unterstützte Encodings: UTF-8 (mit oder ohne BOM), Latin-1.

## Verwendung

```bash
python compare_lists.py LISTE1.odt LISTE2.csv
```

### Optionen

```
positional arguments:
  odt_file              Source list 1: ODT file (col 2 = Nachname, col 3 = Vorname)
  csv_file              Source list 2: CSV file with Nachname and Vorname columns

options:
  --output-dir DIR      Directory for the three output CSV files (default: current directory)
  -h, --help            show this help message and exit
```

### Beispiel

```bash
python compare_lists.py mitglieder.odt export.csv --output-dir ergebnisse/
```

Der Vergleich erfolgt **groß-/kleinschreibungsunabhängig** auf der Kombination (Nachname, Vorname).
