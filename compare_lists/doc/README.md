# compare_lists

Vergleicht zwei Mitgliederlisten im CSV-Format anhand von **Vorname**, **Nachname** und **Straße** und gibt fuenf Ergebnislisten aus.

## Ergebnisse

| Ausgabedatei | Inhalt |
| --- | --- |
| `nur_in_Bank_Datei.csv` | Mitglieder nur in Liste 1 (CSV) |
| `nur_in_Ame_Datei.csv` | Mitglieder nur in Liste 2 (CSV) |
| `in_beiden_listen.csv` | Mitglieder in beiden Listen |
| `gleicher_name_unterschiedliche_strasse.csv` | Gleicher Nachname/Vorname in beiden Listen, aber unterschiedliche Straße (zeigt Straße aus beiden Quellen) |
| `aehnliche_eintraege_beide_listen.csv` | Unequal entries from list 1 and list 2 with max. 4 character differences (edit distance), both entries in one line |
| `header.log` | Beim Einlesen übersprungene Seiten-Header und andere ungültige Zeilen |

## Voraussetzungen

```
pip install -r requirements.txt
```

## Eingabedateien

### Liste 1 – CSV-Datei

Die CSV-Datei muss eine Kopfzeile mit den Spalten **`Nachname`**, **`Vorname`** und **`Straße`** enthalten (in beliebiger Reihenfolge, weitere Spalten werden ignoriert).

### Liste 2 – CSV-Datei

Die CSV-Datei muss eine Kopfzeile mit den Spalten **`Nachname`**, **`Vorname`** und **`Postanschrift2`** enthalten (in beliebiger Reihenfolge, weitere Spalten werden ignoriert).

Die Spalte **`Postanschrift2`** wird intern als **`Straße`** verwendet.

In Liste 1 muss die erste Spalte jeder gültigen Datenzeile eine rein numerische
Mitgliedsnummer enthalten. Vorspannzeilen vor der eigentlichen Kopfzeile sowie
spätere Zeilen mit einem anderen Inhalt in der ersten Spalte werden automatisch
ignoriert. Dadurch werden auch wiederholte Seiten-Header aus exportierten
Dateien herausgefiltert. Die Spaltennamen `Mitgl-Nr` und `Straße, Nr.` werden
automatisch als `PNr` und `Straße` erkannt. Die ignorierten Zeilen werden mit
Quelldatei und Zeilennummer in `header.log` im Ausgabeordner protokolliert; die
Logdatei wird bei jedem Programmstart neu geschrieben. Liste 2 wird nicht nach
einer numerischen ersten Spalte gefiltert, da dort die PK-Kennung stehen kann.

Unterstützte Encodings: UTF-8 (mit oder ohne BOM), CP1252, Latin-1.
Das Trennzeichen wird automatisch erkannt (z. B. `,` oder `;`).

Die Ausgabedateien werden als **UTF-8 mit BOM** gespeichert, damit Umlaute in Excel unter Windows korrekt angezeigt werden.

## Verwendung

```
python compare_lists.py LISTE1.csv LISTE2.csv
```

### Optionen

```text
positional arguments:
  csv_file1             Source list 1: CSV file with Nachname, Vorname and Straße columns. Preamble and repeated headers are ignored automatically.
  csv_file2             Source list 2: CSV file with Nachname, Vorname and Postanschrift2 columns

options:
  --output-dir DIR      Directory for the four output CSV files (default: current directory). This parameter has to be set as the first parameter, bevor the list-file-names are set

  -h, --help            show this help message and exit
```

### Beispiel

```bash
python compare_lists.py bank.csv ame.csv --output-dir ergebnisse/
```

Der Vergleich erfolgt **groß-/kleinschreibungsunabhängig** auf der Kombination (Nachname, Vorname, Straße).

Zusätzlich wird eine Aehnlichkeitsliste erzeugt: Zwei Eintraege gelten als aehnlich, wenn ihre Zeichen-Differenz (Levenshtein/Edit-Distance) ueber den kombinierten Text aus Nachname, Vorname und Straße **nicht groesser als 4** ist.
