"""
Module parse_items

Parse a list of items (e.g. movies, books, wine etc.) and support queries and a
recommendation engine.
"""

import re
import sys
import csv
import datetime
import argparse
import textwrap
import xlrd

# Use this as a default date when none is provided
default_date = datetime.date(1900, 1, 1)
todays_date = datetime.date.today()

def xl_date_to_str(xl_date):
    """"Utility to convert from date as presented by Excel to date used by Python.
    Excel represents dates as increments from 12/30/1899, so adjust that here."""
    epoch = datetime.date.toordinal(datetime.date(1899, 12, 30))
    actual_date = datetime.date.fromordinal(int(xl_date) + epoch)
    return datetime.date.strftime(actual_date, "%m/%d/%Y")


class items_list:
    """A item library with author, title, rating etc. derived from a items CSV/Excel file object."""

    def __init__(self,
                 items_file,
                 creator_field_name,
                 genre_field_names,
                 read_date_field_name,
                 added_date_field_name="",
                 file_type="csv"):
        """Initialize the items list based on a CSV file object or an Excel file name.

        The file must contain the following field names:
        * Creator of the item represented by creator_field_name
        * Genre(s) of the item represented by genre_field_names
        * Date the item was consumed represented by read_date_field_name

        In addition, the file must contain the following field names:
        * Title
        * Status
        * Average Rating
        * My Rating

        Status field may contain the values read/watched/heard or to-read/to-watch/to-hear
        or reading/watching/hearing.

        file_type may be excel or csv (default).

        The file may contain the following optional field names:
        * The date the item was added represented by added_date_field_name
          If this field is present, it is taken into account in the recommended books.
        """

        if file_type == "csv":
            with open(items_file, newline='') as f:
                blist = [row for row in csv.DictReader(f)]

        elif file_type == "excel":
            f = xlrd.open_workbook(items_file)
            sh = f.sheet_by_index(0)
            blist = []
            for i in range(1, sh.nrows):
                blist.append({})
                for j in range(sh.ncols):
                    field_name = sh.cell_value(0, j)
                    field_value = sh.cell_value(i, j)
                    field_type = sh.cell_type(i, j)
                    if field_type == xlrd.XL_CELL_DATE:
                        blist[i - 1][field_name] = xl_date_to_str(field_value)
                    else:
                        blist[i - 1][field_name] = str(field_value)

        else:
            raise "Unknown file type"

        self.items_list = []
        self.genre_read_dates = {}
        self.author_ratings = {}

        read_synonyms = ["read", "watched", "heard"]
        reading_synonyms = ["reading", "watching", "hearing"]
        for item in blist:

            # There may be multiple genre field names. Loop through them
            # and collect all the genres that apply to the item.
            genre_list = []
            for gfield in genre_field_names:
                # Genre entry could either be a singleton or could be
                # a set of genres separated by commas. Convert into a list
                # in either case. Strip out whitespace and empty string shelf names.
                genre_entry = item[gfield]
                if "," not in genre_entry:
                    glist = [genre_entry]
                else:
                    glist = genre_entry.split(",")
                genre_list.extend([x.strip() for x in glist])

            # Potential items to read consist of:
            # 1. Items with the status not marked as read, or
            # 2. Items in a genre called "books-to-read-again"
            if ((item["Status"].lower().strip() in read_synonyms) and
                ("books-to-read-again" not in genre_list)):
                item_status = "Read"
            elif (item["Status"].lower().strip() in reading_synonyms):
                item_status = "Reading"
            else:
                item_status = "Unread"

            # Update read date
            if (item["Status"].lower().strip() in read_synonyms):
                # If an item has been read, parse its read date and rating
                item_read_date = datetime.datetime.strptime(item[read_date_field_name].strip(),
                                                            "%m/%d/%Y").date()
                item_my_rating = float(item["My Rating"])
            elif (item["Status"].lower().strip() in reading_synonyms):
                # If an item is being read, set its read date to today
                item_read_date = todays_date
                item_my_rating = None
            else:
                item_read_date = default_date
                item_my_rating = None

            if (added_date_field_name):
                # If an item has an added date, save it
                item_added_date = datetime.datetime.strptime(item[added_date_field_name].strip(),
                                                            "%m/%d/%Y").date()

                # However, if the item is up for reading again, assume
                # that it was added when it was read last
                if ("books-to-read-again" in genre_list):
                    item_added_date = item_read_date
            else:
                item_added_date = default_date

            author_list = [x.strip() for x in item[creator_field_name].split(",")]

            self.items_list.append({"Title": item["Title"].strip(),
                                    "Authors": author_list,
                                    "Genre": genre_list,
                                    "Average Rating": float(item["Average Rating"]),
                                    "My Rating": item_my_rating,
                                    "Read date": item_read_date,
                                    "Added date": item_added_date,
                                    "Status": item_status})

            # If an item has been read, update the author ratings
            if item["Status"] == "read":
                for author in author_list:
                    if author not in self.author_ratings.keys():
                        # If this author hasn't appeared yet, create a new entry
                        self.author_ratings[author] = {"My Rating": float(item["My Rating"]),
                                                       "Number": 1,
                                                       "Genre": genre_list}
                    else:
                        # If this author has appeared before, update the existing entry
                        rating_entry = self.author_ratings[author]
                        old_num_items = rating_entry["Number"]
                        old_rating = rating_entry["My Rating"]
                        old_genres = rating_entry["Genre"]

                        new_rating = (old_rating * old_num_items +
                                      float(item["My Rating"])) / (old_num_items + 1)
                        new_num_items = old_num_items + 1
                        new_genres = old_genres + genre_list

                        rating_entry["Number"] = new_num_items
                        rating_entry["My Rating"] = new_rating
                        rating_entry["Genre"] = new_genres

            # Update the genre read dates
            for genre in genre_list:
                if (genre not in self.genre_read_dates.keys()):
                    # If genre hasn't been added to the list yet
                    self.genre_read_dates[genre] = item_read_date
                else:
                    # If this item has been read more recently than the last one in the genre,
                    # then update the genre's last read date
                    self.genre_read_dates[genre] = max(item_read_date,
                                                       self.genre_read_dates[genre])


    def __update_genre_ratings(self):
        """Assign a rating to each genre.
        A higher rating for a genre means that that genre was read farther in the past.
        """

        min_rating = 1.0
        max_rating = 5.0
        rating_range = max_rating - min_rating

        # Find min and max genre date
        min_read_date = min(
            [date for date in self.genre_read_dates.values()],
            default=default_date)
        max_read_date = max(
            [date for date in self.genre_read_dates.values()],
            default=default_date)

        # Create a scaled rating for the genre between min and max rating
        # Higher number implies that the genre was read farther in the past
        self.scaled_ratings = {}
        for cat in self.genre_read_dates.keys():
            rating = self.genre_read_dates[cat]

            # If genre has never been read before, assume that it was read on the last available date
            if not rating:
                rating = min_read_date

            if (min_read_date < max_read_date):
                scaled_rating = round(rating_range * ((max_read_date - rating) /
                                                      (max_read_date - min_read_date)) + min_rating,
                                      2)
            else:
                # If min and max read dates are the same, all genres were read on the same day
                # In that case, assume every genre gets max rating
                scaled_rating = max_rating

            self.scaled_ratings[cat] = scaled_rating

        return

    def __update_item_ratings(self):
        """Assign a rating values to an item.
        The item's rating values consist of the following:
        * A 1-5 rating based on the popular rating for the item
        * A 1-5 rating based on the age of the item
        * A 1-5 rating that is the min of the ratings of all genres that the item belongs to
        """

        min_rating = 1.0
        max_rating = 5.0
        rating_range = max_rating - min_rating

        # Find min and max item rating
        item_min_rating = min([item["Average Rating"]
                               for item in self.items_list if item["Status"] == "Unread"])
        item_max_rating = max([item["Average Rating"]
                               for item in self.items_list if item["Status"] == "Unread"])

        # Item's popularity rating
        for item in self.items_list:
            # If every item has the same rating, then use the max rating
            if (item_min_rating < item_max_rating):
                item["Popularity Rating"] = round(rating_range * ((item["Average Rating"] - item_min_rating) /
                                                                  (item_max_rating - item_min_rating)) + min_rating,
                                                  2)
            else:
                item["Popularity Rating"] = item_max_rating

        # Item's age rating
        item_min_rating = min([item["Added date"]
                               for item in self.items_list
                               if item["Status"] in ["Reading", "Unread"]])
        item_max_rating = max([item["Added date"]
                               for item in self.items_list
                               if item["Status"] in ["Reading", "Unread"]])

        for item in self.items_list:
            # If every item has the same rating, then use the max rating
            # Older added date => higher rating
            if (item_min_rating < item_max_rating):
                item["Age Rating"] = round(rating_range * ((item_max_rating - item["Added date"]) /
                                                           (item_max_rating - item_min_rating))
                                           + min_rating,
                                           2)
            else:
                item["Age Rating"] = max_rating

        # Item's genre rating
        for item in self.items_list:
            # Then, find the min rating in the item's genres i.e. decide the rating by the genre of the
            # item that was read most recently.
            # If there are no genres, the default rating is high.
            item["Genre Rating"] = min([self.scaled_ratings[cat] for cat in item["Genre"]],
                                       default=max_rating)

        return

    def __item_is_in_genre(self, item, genre):
        """Check if item is in genre"""

        if not(genre):
            genre = ""

        ret_val = False
        for g in item["Genre"]:
            ret_val = ret_val or re.search(genre, g, flags=re.IGNORECASE)

        return ret_val

    def __item_is_by_author(self, item, author):
        """Check if item is by author"""

        if not(author):
            author = ""

        ret_val = any([re.search(author, x, flags=re.IGNORECASE) for x in item["Authors"]])

        return ret_val

    def list_genres(self):
        """List of available genres along with the dates on which they were last read.
        If the date is None, the genre hasn't been read yet."""

        return self.genre_read_dates

    def choose_authors(self, num_authors, genre=None):
        """Return a list of authors whose books should be read.

        The selected authors match all of the following criteria:
           - Some of their books have been read
           - Their books have a high rating
           - None of their books are in the to-read list

        If genre is specified, only authors who had books in that genre are chosen."""

        # First sort author ratings from highest to lowest
        best_authors = sorted(self.author_ratings,
                              key=lambda item:
                              self.author_ratings[item]["My Rating"],
                              reverse=True)

        # Filter out authors based on selection criteria
        best_authors_no_to_read = list(filter(lambda item:
                                              (len(self.choose_items(1, author=item))==0) and
                                              (self.__item_is_in_genre(self.author_ratings[item], genre)) and
                                              (self.author_ratings[item]["Number"] >= 2),
                                              best_authors))

        if (num_authors > len(best_authors_no_to_read)):
            num_authors = len(best_authors_no_to_read)

        return best_authors_no_to_read[0:num_authors]

    def choose_items(self, num_items, genre=None, author=None):
        """Return a list of recommended items.
        The size of the list is <= num_items.
        If genre is specified and not None, items are recommended from that genre only.
        If author is specified and not None, items are recommended from that author only."""

        self.__update_genre_ratings()

        self.__update_item_ratings()

        unread_cat_items_list = list(filter(lambda item:
                                            ((item["Status"] == "Unread") and
                                             self.__item_is_in_genre(item, genre) and
                                             self.__item_is_by_author(item, author)),
                                            self.items_list))

        # Sort potential unread items by total rating (highest to lowest)
        # Don't allow age rating to be too high for books that are to be read again
        # Those are more likely to have been added a long time ago
        best_items = sorted(unread_cat_items_list,
                            key=lambda item:
                            item["Popularity Rating"] +
                            item["Genre Rating"] +
                            (1.0 - 0.75*("books-to-read-again" in item["Genre"]))*item["Age Rating"],
                            reverse=True)

        return best_items[0:num_items]

    def list_items_read(self, num_items, genre=None, author=None):
        """Return a list of the last read items.
        The size of the list is <= num_items.
        If genre is specified and not None, the list is for that genre only.
        If author is specified and not None, the list is for that author only."""

        read_items = list(filter(lambda item:
                                 ((item["Status"] == "Read") and
                                  self.__item_is_in_genre(item, genre) and
                                  self.__item_is_by_author(item, author)),
                                 self.items_list))

        # Sort read items by read date (newest to oldest)
        list_read = sorted(read_items,
                           key=lambda item:
                           item["Read date"],
                           reverse=True)

        return list_read[0:num_items]
