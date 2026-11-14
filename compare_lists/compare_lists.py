#!/usr/bin/env python3
"""
Compare two member lists and produce three result lists:

                1. Members only in source list 1 (CSV)
    2. Members only in source list 2 (CSV)
  3. Members in both lists

Both source lists are CSV files that must contain the columns
    "Nachname", "Vorname" and "Straße" as header names.

Both lists are compared case-insensitively on (Nachname, Vorname, Straße).
"""

import argparse
import csv
import re
import sys
from collections import defaultdict
from pathlib import Path


def _levenshtein_distance_limited(a: str, b: str, max_distance: int) -> int:
    """Return Levenshtein distance, aborting early when distance exceeds max_distance."""
    if a == b:
        return 0
    if abs(len(a) - len(b)) > max_distance:
        return max_distance + 1

    # Keep the dynamic programming row short by iterating on the shorter string.
    if len(a) > len(b):
        a, b = b, a

    previous = list(range(len(a) + 1))
    for i, char_b in enumerate(b, start=1):
        current = [i] + [0] * len(a)
        row_min = current[0]
        for j, char_a in enumerate(a, start=1):
            cost = 0 if char_a == char_b else 1
            current[j] = min(
                previous[j] + 1,
                current[j - 1] + 1,
                previous[j - 1] + cost,
            )
            if current[j] < row_min:
                row_min = current[j]
        if row_min > max_distance:
            return max_distance + 1
        previous = current
    return previous[-1]


def _street_key(value: str) -> str:
    """Normalize street values so Straße, Str, Str. and Strasse compare equal."""
    normalized = value.strip().casefold()
    normalized = normalized.replace("ß", "ss")
    normalized = normalized.replace("strasse", "str")
    normalized = normalized.replace("str.", "str")
    return normalized


def _street_key_without_house_number(value: str) -> str:
    """Return the normalized street name without a trailing house number."""
    street_without_number = re.sub(
        r"\s+\d+[\w/-]*(?:\s*-\s*\d+[\w/-]*)?\s*$",
        "",
        value.strip(),
        flags=re.IGNORECASE,
    )
    return _street_key(street_without_number)


def _comparison_last_name(member: dict) -> str:
    """Ignore a matching parenthesized street word at the end of a last name."""
    last_name = member["Nachname"].strip()
    match = re.search(r"\s*\(([^()\s]+)\)\s*$", last_name)
    if match and _street_key(match.group(1)) == _street_key_without_house_number(
        member["Straße"]
    ):
        last_name = last_name[: match.start()].rstrip()
    return last_name.casefold()

def read_csv_list(
    filepath: str,
    street_column: str = "Straße",
    skipped_lines: list[str] | None = None,
    require_numeric_first_column: bool = True,
) -> list[dict]:
    """Read a CSV file that contains 'Nachname', 'Vorname' and a street column.

    Encoding is tried as UTF-8-with-BOM first, then Latin-1 as a fallback
    (common for files exported from German-language systems).
    """
    encodings = ("utf-8-sig", "cp1252", "latin-1")
    for encoding in encodings:
        try:
            with open(filepath, newline="", encoding=encoding) as fh:
                sample = fh.read(4096)
                fh.seek(0)
                if sample.count(";") > sample.count(","):
                    dialect = csv.excel()
                    dialect.delimiter = ";"
                else:
                    try:
                        dialect = csv.Sniffer().sniff(sample, delimiters=",;\t|")
                    except csv.Error:
                        dialect = csv.excel

                rows = list(csv.reader(fh, dialect=dialect))
                street_aliases = {street_column}
                if street_column.casefold().startswith("stra"):
                    street_aliases.update({"Straße", "Straße, Nr."})

                header_index = None
                fields: list[str] = []
                for index, candidate in enumerate(rows):
                    candidate_fields = [field.strip() for field in candidate]
                    if (
                        "Nachname" in candidate_fields
                        and "Vorname" in candidate_fields
                        and street_aliases.intersection(candidate_fields)
                    ):
                        header_index = index
                        fields = candidate_fields
                        break

                if header_index is None:
                    print(
                        f"Warning: CSV file '{filepath}' does not contain 'Nachname', "
                        f"'Vorname' and/or '{street_column}' columns.",
                        file=sys.stderr,
                    )
                    return []

                if skipped_lines is not None:
                    for line_number, row in enumerate(rows[:header_index], start=1):
                        skipped_lines.append(
                            f"{filepath} (Zeile {line_number}): "
                            + dialect.delimiter.join(row)
                        )

                field_positions = {
                    field: position for position, field in enumerate(fields) if field
                }
                street_field = next(field for field in fields if field in street_aliases)
                pnr_position = next(
                    (
                        field_positions[name]
                        for name in ("PNr", "Personalnummer", "Mitgl-Nr")
                        if name in field_positions
                    ),
                    0,
                )
                members: list[dict] = []
                for line_number, values in enumerate(
                    rows[header_index + 1 :], start=header_index + 2
                ):
                    first_column = values[0].strip() if values else ""
                    if require_numeric_first_column and not first_column.isdecimal():
                        if skipped_lines is not None:
                            skipped_lines.append(
                                f"{filepath} (Zeile {line_number}): "
                                + dialect.delimiter.join(values)
                            )
                        continue

                    def value_at(position: int) -> str:
                        return values[position].strip() if position < len(values) else ""

                    nachname = value_at(field_positions["Nachname"])
                    vorname = value_at(field_positions["Vorname"])
                    strasse = value_at(field_positions[street_field])
                    pnr = value_at(pnr_position)
                    if nachname or vorname or strasse:
                        members.append({"Nachname": nachname, "Vorname": vorname, "Straße": strasse, "PNr": pnr})
                return members
        except UnicodeDecodeError:
            continue
    print(f"Error: Could not decode '{filepath}' with {encodings}.", file=sys.stderr)
    sys.exit(1)


# ---------------------------------------------------------------------------
# Comparison
# ---------------------------------------------------------------------------

def _key(member: dict) -> tuple[str, str, str]:
    """Case-insensitive (Nachname, Vorname, Straße) tuple used as comparison key."""
    return (
        _comparison_last_name(member),
        member["Vorname"].casefold(),
        _street_key(member["Straße"]),
    )


def _name_key(member: dict) -> tuple[str, str]:
    """Case-insensitive (Nachname, Vorname) tuple used for name-level grouping."""
    return (_comparison_last_name(member), member["Vorname"].casefold())


def _entry_text(member: dict) -> str:
    """Create one normalized compare text for fuzzy matching across both lists."""
    return " ".join(
        [
            _comparison_last_name(member),
            member["Vorname"].strip(),
            member["Straße"].strip(),
        ]
    ).casefold()


def _find_similar_entries(
    list1: list[dict], list2: list[dict], max_distance: int = 4
) -> list[dict]:
    """Find unequal entries that are still similar (edit distance <= max_distance)."""
    rows: list[dict] = []
    for m1 in list1:
        text1 = _entry_text(m1)
        for m2 in list2:
            text2 = _entry_text(m2)
            if text1 == text2:
                continue
            distance = _levenshtein_distance_limited(text1, text2, max_distance)
            if distance <= max_distance:
                rows.append(
                    {
                        "PNr_Liste1": m1.get("PNr", ""),
                        "Nachname_Liste1": m1["Nachname"],
                        "Vorname_Liste1": m1["Vorname"],
                        "Straße_Liste1": m1["Straße"],
                        "Nachname_Liste2": m2["Nachname"],
                        "Vorname_Liste2": m2["Vorname"],
                        "Straße_Liste2": m2["Straße"],
                        "Zeichen_Differenz": distance,
                    }
                )

    rows.sort(
        key=lambda r: (
            int(r["Zeichen_Differenz"]),
            r["Nachname_Liste1"].casefold(),
            r["Vorname_Liste1"].casefold(),
            r["Straße_Liste1"].casefold(),
            r["Nachname_Liste2"].casefold(),
            r["Vorname_Liste2"].casefold(),
            r["Straße_Liste2"].casefold(),
        )
    )
    return rows


def compare_lists(
    list1: list[dict], list2: list[dict]
) -> tuple[list[dict], list[dict], list[dict], list[dict]]:
    """Compare two member lists.

    Returns:
        only_in_1: members only in list1
        only_in_2: members only in list2
        in_both:   members present in both lists (data taken from list1)
        same_name_different_street: rows with same name in both lists but differing street
    """
    members_by_key_1: dict[tuple[str, str, str], list[dict]] = defaultdict(list)
    members_by_key_2: dict[tuple[str, str, str], list[dict]] = defaultdict(list)

    for m in list1:
        members_by_key_1[_key(m)].append(m)
    for m in list2:
        members_by_key_2[_key(m)].append(m)

    keys1 = set(members_by_key_1)
    keys2 = set(members_by_key_2)

    only_in_1: list[dict] = []
    only_in_2: list[dict] = []
    in_both: list[dict] = []

    for k in sorted(keys1 | keys2):
        rows1 = members_by_key_1.get(k, [])
        rows2 = members_by_key_2.get(k, [])
        common_count = min(len(rows1), len(rows2))

        in_both.extend(rows1[:common_count])
        only_in_1.extend(rows1[common_count:])
        only_in_2.extend(rows2[common_count:])

    name_to_streets_1: dict[tuple[str, str], set[str]] = {}
    name_to_streets_2: dict[tuple[str, str], set[str]] = {}
    street_display_1: dict[tuple[str, str], dict[str, str]] = {}
    pnr_display_1: dict[tuple[str, str], dict[str, str]] = {}
    street_display_2: dict[tuple[str, str], dict[str, str]] = {}
    canonical_names: dict[tuple[str, str], tuple[str, str]] = {}

    for m in list1:
        nk = _name_key(m)
        canonical_names.setdefault(nk, (m["Nachname"], m["Vorname"]))
        street_key = _street_key(m["Straße"])
        name_to_streets_1.setdefault(nk, set()).add(street_key)
        street_display_1.setdefault(nk, {}).setdefault(street_key, m["Straße"])
        pnr_display_1.setdefault(nk, {}).setdefault(street_key, m.get("PNr", ""))
    for m in list2:
        nk = _name_key(m)
        canonical_names.setdefault(nk, (m["Nachname"], m["Vorname"]))
        street_key = _street_key(m["Straße"])
        name_to_streets_2.setdefault(nk, set()).add(street_key)
        street_display_2.setdefault(nk, {}).setdefault(street_key, m["Straße"])

    same_name_different_street: list[dict] = []
    for nk in sorted(set(name_to_streets_1) & set(name_to_streets_2)):
        streets1 = sorted(name_to_streets_1[nk], key=str.casefold)
        streets2 = sorted(name_to_streets_2[nk], key=str.casefold)
        if {s.casefold() for s in streets1} == {s.casefold() for s in streets2}:
            continue

        nachname, vorname = canonical_names[nk]
        for s1_key in streets1:
            for s2_key in streets2:
                if s1_key.casefold() == s2_key.casefold():
                    continue
                same_name_different_street.append(
                    {
                        "PNr": pnr_display_1[nk].get(s1_key, ""),
                        "Nachname": nachname,
                        "Vorname": vorname,
                        "Straße_Bank_Datei": street_display_1[nk][s1_key],
                        "Straße_Ame_Datei": street_display_2[nk][s2_key],
                    }
                )

    return only_in_1, only_in_2, in_both, same_name_different_street


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
            print(f"  {m['Nachname']}, {m['Vorname']}, {m['Straße']}")
    else:
        print("  (keine)")


def _write_csv(members: list[dict], path: Path) -> None:
    # UTF-8 with BOM improves compatibility with Excel on Windows.
    with open(path, "w", newline="", encoding="utf-8-sig") as fh:
        writer = csv.DictWriter(fh, fieldnames=["PNr", "Nachname", "Vorname", "Straße"])
        writer.writeheader()
        writer.writerows(members)


def _print_street_diff_section(title: str, rows: list[dict]) -> None:
    width = 60
    print(f"\n{'=' * width}")
    print(f"{title}  ({len(rows)} Einträge)")
    print("=" * width)
    if rows:
        for r in rows:
            print(
                f"  PNr: {r.get('PNr', '')} | {r['Nachname']}, {r['Vorname']} | "
                f"Bank: {r['Straße_Bank_Datei']} | Ame: {r['Straße_Ame_Datei']}"
            )
    else:
        print("  (keine)")


def _write_street_diff_csv(rows: list[dict], path: Path) -> None:
    with open(path, "w", newline="", encoding="utf-8-sig") as fh:
        writer = csv.DictWriter(
            fh,
            fieldnames=["PNr", "Nachname", "Vorname", "Straße_Bank_Datei", "Straße_Ame_Datei"],
        )
        writer.writeheader()
        writer.writerows(rows)


def _print_similar_section(title: str, rows: list[dict]) -> None:
    width = 60
    print(f"\n{'=' * width}")
    print(f"{title}  ({len(rows)} Einträge)")
    print("=" * width)
    if rows:
        for r in rows:
            print(
                "  "
                f"L1: {r['Nachname_Liste1']}, {r['Vorname_Liste1']}, {r['Straße_Liste1']}"
                " | "
                f"L2: {r['Nachname_Liste2']}, {r['Vorname_Liste2']}, {r['Straße_Liste2']}"
                " | "
                f"Diff: {r['Zeichen_Differenz']}"
            )
    else:
        print("  (keine)")


def _write_similar_csv(rows: list[dict], path: Path) -> None:
    with open(path, "w", newline="", encoding="utf-8-sig") as fh:
        writer = csv.DictWriter(
            fh,
            fieldnames=[
                "PNr_Liste1",
                "Nachname_Liste1",
                "Vorname_Liste1",
                "Straße_Liste1",
                "Nachname_Liste2",
                "Vorname_Liste2",
                "Straße_Liste2",
                "Zeichen_Differenz",
            ],
        )
        writer.writeheader()
        writer.writerows(rows)


def _write_header_log(skipped_lines: list[str], path: Path) -> None:
    """Overwrite the log with all non-data rows skipped during this run."""
    with open(path, "w", encoding="utf-8-sig", newline="") as fh:
        for line in skipped_lines:
            fh.write(f"{line}\n")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Compare two member lists (CSV and CSV) by Nachname, Vorname and Straße. "
            "Produces five result CSV files."
        )
    )
    parser.add_argument(
        "csv_file1",
        help=(
            "Source list 1: CSV file with Nachname, Vorname and Straße columns. "
            "Preamble and repeated headers are ignored automatically."
        ),
    )
    parser.add_argument(
        "csv_file2",
        help="Source list 2: CSV file with Nachname, Vorname and Postanschrift2 columns",
    )
    parser.add_argument(
        "--output-dir",
        default=".",
        metavar="DIR",
        help="Directory for the five output CSV files (default: current directory)",
    )
    args = parser.parse_args()

    out = Path(args.output_dir)
    out.mkdir(parents=True, exist_ok=True)
    skipped_lines: list[str] = []

    # --- Read ---
    print(f"Lese CSV-Datei 1: {args.csv_file1}")
    list1 = read_csv_list(
        args.csv_file1,
        street_column="Straße",
        skipped_lines=skipped_lines,
    )
    print(f"  {len(list1)} Einträge gefunden")

    print(f"Lese CSV-Datei 2: {args.csv_file2}")
    list2 = read_csv_list(
        args.csv_file2,
        street_column="Postanschrift2",
        skipped_lines=skipped_lines,
        require_numeric_first_column=False,
    )
    print(f"  {len(list2)} Einträge gefunden")

    # --- Compare ---
    only_in_1, only_in_2, in_both, same_name_different_street = compare_lists(list1, list2)
    # Search only among entries that were not already verified as exact matches.
    # Otherwise an entry from "in beiden Listen" could appear a second time in
    # the similarity output because it happens to resemble another entry.
    similar_entries = _find_similar_entries(only_in_1, only_in_2, max_distance=4)

    # --- Print to terminal ---
    _print_section("Nur in Liste 1 (CSV)", only_in_1)
    _print_section("Nur in Liste 2 (CSV)", only_in_2)
    _print_section("In beiden Listen", in_both)
    _print_street_diff_section(
        "Gleicher Name in beiden Listen, aber unterschiedliche Straße",
        same_name_different_street,
    )
    _print_similar_section(
        "Aehnliche Eintraege zwischen Liste 1 und Liste 2 (Zeichen-Differenz <= 4)",
        similar_entries,
    )

    # --- Write CSV output ---
    _write_csv(only_in_1, out / "nur_in_Bank_Datei.csv")
    _write_csv(only_in_2, out / "nur_in_Ame_Datei.csv")
    _write_csv(in_both, out / "in_beiden_listen.csv")
    _write_street_diff_csv(
        same_name_different_street,
        out / "gleicher_name_unterschiedliche_strasse.csv",
    )
    _write_similar_csv(
        similar_entries,
        out / "aehnliche_eintraege_beide_listen.csv",
    )
    _write_header_log(skipped_lines, out / "header.log")

    print(f"\nAusgabedateien und header.log wurden in '{out}/' gespeichert.")


if __name__ == "__main__":
    main()
