import unittest

from compare_lists import _find_similar_entries, compare_lists


def member(nachname, vorname, strasse, pnr=""):
    return {
        "Nachname": nachname,
        "Vorname": vorname,
        "Straße": strasse,
        "PNr": pnr,
    }


class SimilarEntriesTest(unittest.TestCase):
    def test_verified_entries_are_excluded_from_similarity_search(self):
        verified_list1 = member("Meyer", "Anna", "Hauptstr. 1", "1")
        verified_list2 = member("Meyer", "Anna", "Hauptstrasse 1")
        only_list1 = member("Meier", "Anna", "Hauptstr. 1", "2")
        only_list2 = member("Schmidt", "Bernd", "Nebenweg 2")

        only_in_1, only_in_2, in_both, _ = compare_lists(
            [verified_list1, only_list1],
            [verified_list2, only_list2],
        )
        similar_entries = _find_similar_entries(only_in_1, only_in_2)

        self.assertEqual(in_both, [verified_list1])
        self.assertEqual(similar_entries, [])

    def test_unverified_entries_can_still_be_similar(self):
        list1 = [member("Meyer", "Anna", "Hauptstr. 1", "1")]
        list2 = [member("Meier", "Anna", "Hauptstr. 1")]

        only_in_1, only_in_2, in_both, _ = compare_lists(list1, list2)
        similar_entries = _find_similar_entries(only_in_1, only_in_2)

        self.assertEqual(in_both, [])
        self.assertEqual(len(similar_entries), 1)


class ParenthesizedStreetInLastNameTest(unittest.TestCase):
    def test_matching_street_word_is_ignored(self):
        list1_entry = member("Meyer (Hauptstraße)", "Anna", "Hauptstraße 12", "1")
        list2_entry = member("Meyer", "Anna", "Hauptstr. 12")

        only_in_1, only_in_2, in_both, _ = compare_lists(
            [list1_entry], [list2_entry]
        )

        self.assertEqual(only_in_1, [])
        self.assertEqual(only_in_2, [])
        self.assertEqual(in_both, [list1_entry])

    def test_nonmatching_word_remains_part_of_last_name(self):
        list1_entry = member("Meyer (Berlin)", "Anna", "Hauptstraße 12", "1")
        list2_entry = member("Meyer", "Anna", "Hauptstr. 12")

        only_in_1, only_in_2, in_both, _ = compare_lists(
            [list1_entry], [list2_entry]
        )

        self.assertEqual(only_in_1, [list1_entry])
        self.assertEqual(only_in_2, [list2_entry])
        self.assertEqual(in_both, [])

    def test_multiple_words_in_parentheses_are_not_ignored(self):
        list1_entry = member("Meyer (Am Markt)", "Anna", "Am Markt 12", "1")
        list2_entry = member("Meyer", "Anna", "Am Markt 12")

        only_in_1, only_in_2, in_both, _ = compare_lists(
            [list1_entry], [list2_entry]
        )

        self.assertEqual(only_in_1, [list1_entry])
        self.assertEqual(only_in_2, [list2_entry])
        self.assertEqual(in_both, [])


if __name__ == "__main__":
    unittest.main()
