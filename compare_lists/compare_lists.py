#!/usr/bin/env python3
"""
Compare two member lists and produce three result lists:

  1. Members only in source list 1 (ODT)
  2. Members only in source list 2 (CSV)
  3. Members in both lists

Source list 1 is an ODT file (LibreOffice Writer table) where
  column 2 = Nachname  and  column 3 = Vorname  (1-based indexing).

Source list 2 is a CSV file that must contain the columns
  "Nachname" and "Vorname" as header names.

Both lists are compared case-insensitively on (Nachname, Vorname).
"""

import argparse
import csv
import sys
from pathlib import Path

try:
    from odf import teletype
    from odf.opendocument import load
    from odf.table import Table, TableCell, TableRow
except ImportError:
    print("Error: odfpy is required. Install it with:  pip install odfpy", file=sys.stderr)
    sys.exit(1)


# ---------------------------------------------------------------------------
# Reading
# ---------------------------------------------------------------------------

def _expand_cells(row: TableRow) -> list[TableCell]:
    """Return cells of a row with repeated cells expanded."""
    expanded: list[TableCell] = []
    for cell in row.getElementsByType(TableCell):
        repeat = cell.getAttribute("numbercolumnsrepeated")
        count = int(repeat) if repeat else 1
        expanded.extend([cell] * count)
    return expanded


def read_odt_list(filepath: str) -> list[dict]:
    """Read an ODT file and return members from column 2 (Nachname) and column 3 (Vorname).

    Columns are 1-based: column 2 → index 1, column 3 → index 2.
    Empty rows are skipped.
    """
    doc = load(filepath)
    members: list[dict] = []

    for table in doc.getElementsByType(Table):
        for row in table.getElementsByType(TableRow):
            cells = _expand_cells(row)
            if len(cells) < 3:
                continue
            nachname = teletype.extractText(cells[1]).strip()
            vorname = teletype.extractText(cells[2]).strip()
            if nachname or vorname:
                members.append({"Nachname": nachname, "Vorname": vorname})

    return members


def read_csv_list(filepath: str) -> list[dict]:
    """Read a CSV file that contains 'Nachname' and 'Vorname' columns.

    Encoding is tried as UTF-8-with-BOM first, then Latin-1 as a fallback
    (common for files exported from German-language systems).
    """
    encodings = ("utf-8-sig", "latin-1")
    for encoding in encodings:
        try:
            with open(filepath, newline="", encoding=encoding) as fh:
                reader = csv.DictReader(fh)
                if reader.fieldnames is None:
                    continue
                # Check required columns exist (case-sensitive)
                fields = [f.strip() for f in reader.fieldnames]
                if "Nachname" not in fields or "Vorname" not in fields:
                    print(
                        f"Warning: CSV file '{filepath}' does not contain 'Nachname' "
                        f"and/or 'Vorname' columns. Found: {fields}",
                        file=sys.stderr,
                    )
                    return []
                members: list[dict] = []
                for row in reader:
                    # Normalize keys so whitespace in header names doesn't break lookup
                    row = {k.strip(): v for k, v in row.items() if k is not None}
                    nachname = row.get("Nachname", "").strip()
                    vorname = row.get("Vorname", "").strip()
                    if nachname or vorname:
                        members.append({"Nachname": nachname, "Vorname": vorname})
                return members
        except UnicodeDecodeError:
            continue
    print(f"Error: Could not decode '{filepath}' with {encodings}.", file=sys.stderr)
    sys.exit(1)


# ---------------------------------------------------------------------------
# Comparison
# ---------------------------------------------------------------------------

def _key(member: dict) -> tuple[str, str]:
    """Case-insensitive (Nachname, Vorname) tuple used as comparison key."""
    return (member["Nachname"].casefold(), member["Vorname"].casefold())


def _build_map(members: list[dict], source_name: str) -> dict[tuple[str, str], dict]:
    """Build a (key → member) map and warn about duplicate entries."""
    result: dict[tuple[str, str], dict] = {}
    for m in members:
        k = _key(m)
        if k in result:
            print(
                f"Warning: Duplicate entry in {source_name} — "
                f"'{m['Nachname']}, {m['Vorname']}' appears more than once. "
                "Only the first occurrence is used.",
                file=sys.stderr,
            )
        else:
            result[k] = m
    return result


def compare_lists(
    list1: list[dict], list2: list[dict]
) -> tuple[list[dict], list[dict], list[dict]]:
    """Compare two member lists.

    Returns:
        only_in_1: members only in list1
        only_in_2: members only in list2
        in_both:   members present in both lists (data taken from list1)
    """
    map1 = _build_map(list1, "Liste 1 (ODT)")
    map2 = _build_map(list2, "Liste 2 (CSV)")

    keys1 = set(map1)
    keys2 = set(map2)

    only_in_1 = [map1[k] for k in sorted(keys1 - keys2)]
    only_in_2 = [map2[k] for k in sorted(keys2 - keys1)]
    in_both = [map1[k] for k in sorted(keys1 & keys2)]

    return only_in_1, only_in_2, in_both


# ---------------------------------------------------------------------------
# Output helpers
# ---------------------------------------------------------------------------

def _print_section(title: str, members: list[dict]) -> None:
    width = 60
    print(f"\n{'=' * width}")
    print(f"{title}  ({len(members)} Einträge)")
    print("=" * width)
    if members:
        for m in members:
            print(f"  {m['Nachname']}, {m['Vorname']}")
    else:
        print("  (keine)")


def _write_csv(members: list[dict], path: Path) -> None:
    with open(path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=["Nachname", "Vorname"])
        writer.writeheader()
        writer.writerows(members)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Compare two member lists (ODT table and CSV) by Nachname and Vorname. "
            "Produces three result CSV files."
        )
    )
    parser.add_argument("odt_file", help="Source list 1: ODT file (col 2 = Nachname, col 3 = Vorname)")
    parser.add_argument("csv_file", help="Source list 2: CSV file with Nachname and Vorname columns")
    parser.add_argument(
        "--output-dir",
        default=".",
        metavar="DIR",
        help="Directory for the three output CSV files (default: current directory)",
    )
    args = parser.parse_args()

    # --- Read ---
    print(f"Lese ODT-Datei: {args.odt_file}")
    list1 = read_odt_list(args.odt_file)
    print(f"  {len(list1)} Einträge gefunden")

    print(f"Lese CSV-Datei: {args.csv_file}")
    list2 = read_csv_list(args.csv_file)
    print(f"  {len(list2)} Einträge gefunden")

    # --- Compare ---
    only_in_1, only_in_2, in_both = compare_lists(list1, list2)

    # --- Print to terminal ---
    _print_section("Nur in Liste 1 (ODT)", only_in_1)
    _print_section("Nur in Liste 2 (CSV)", only_in_2)
    _print_section("In beiden Listen", in_both)

    # --- Write CSV output ---
    out = Path(args.output_dir)
    out.mkdir(parents=True, exist_ok=True)

    _write_csv(only_in_1, out / "nur_in_liste1.csv")
    _write_csv(only_in_2, out / "nur_in_liste2.csv")
    _write_csv(in_both, out / "in_beiden_listen.csv")

    print(f"\nAusgabedateien wurden in '{out}/' gespeichert.")


if __name__ == "__main__":
    main()
