#!/usr/bin/env python
import unittest
import parse_items

csv_file = "test_parse_items_file.csv"
file2 = "test_old_added_items.csv"

class inputFileTests(unittest.TestCase):
    def setUp(self):
        # Test items file with exactly 1 read, unread and currently-reading item each
        # Each item has a different author and a different category
        self.test_blist = parse_items.items_list(csv_file,
                                                 creator_field_name="Author",
                                                 genre_field_names=[
                                                     "Genre"],
                                                 read_date_field_name="Date Read",
                                                 file_type="csv")

        # Test that less recently added books get priority (all other things being equal)
        self.test2 = parse_items.items_list(file2,
                                            creator_field_name="Author",
                                            genre_field_names=[
                                                "Genre"],
                                            read_date_field_name="Date Read",
                                            added_date_field_name="Date Added",
                                            file_type="csv")

    def tearDown(self):
        self.test_blist = None
        self.test2 = None

    def test_genres(self):
        # 3 genres in the original list
        self.assertEqual(len(self.test_blist.list_genres()), 3)

    def test_books_read(self):
        # Only 1 item in the list has been read
        self.assertEqual(len(self.test_blist.list_items_read(num_items=10)),
                         1)

        # Only 1 item has a valid read date
        clist = self.test_blist.list_genres()
        read_dates = [item for item in clist.values() if item]
        self.assertEqual(len(read_dates), 1)

    def test_recommendation(self):
        # Only 2 items should be recommended since only two are in unread status
        self.assertEqual(len(self.test_blist.choose_items(num_items=10)),
                         2)

    def test_recommendation_higher_rating(self):
        # Item with higher average rating should be recommended when only 1 rating is asked
        # In the input file, item "Reading book" has higher average rating than "Unread book"
        self.assertEqual(self.test_blist.choose_items(num_items=1)[0]["Title"],
                         "Reading book")

    def test_date_added(self):
        # "Unread book 2" is the book that has aged most in the wait list
        self.assertEqual(self.test2.choose_items(num_items=1)[0]["Title"],
                         "Unread book 2")

if __name__ == '__main__':
    unittest.main()
