#!/usr/bin/env python
"""
Module recommend_book.

Recommend the next book to read based on an input list of books.
"""

import sys
import csv
import datetime
import argparse
import textwrap

import parse_items

__default_num_books = 20

def shorten(str, width):
    # Clean up string for printing: ensure it's exactly of width length with
    # ellipsis as needed
    return textwrap.shorten(str, width=width, placeholder="...").ljust(width)


description_str = "Search for and recommend books using books_file.\nBy default, show the %d best books to read next." % (__default_num_books)

parser = argparse.ArgumentParser(description=description_str)
parser.add_argument('-l', '--list_genres',
                    action='store_true',
                    default=False)
parser.add_argument('-s', '--list_read_books',
                    type=int,
                    dest='num_read_books',
                    default=None)
parser.add_argument('-r', '--recommend_books',
                    type=int,
                    dest='num_recommend_books',
                    default=None)
parser.add_argument('-a', '--list_best_authors',
                    type=int,
                    dest='num_authors',
                    default=None)
parser.add_argument(dest = 'books_file', type = str)
parser.add_argument('-g', '--restrict_by_genre',
                    type=str,
                    dest='genre',
                    default=None)
parser.add_argument('-ra', '--restrict_by_author',
                    dest='author',
                    default=None)
args = parser.parse_args()

books_file = args.books_file
if ("." in books_file) and (books_file.split("."))[1] == "xlsx":
    file_type = "excel"
else:
    file_type = "csv"

blist = parse_items.items_list(books_file,
                               creator_field_name="Author",
                               genre_field_names=["Genre"],
                               read_date_field_name="Date Read",
                               added_date_field_name="Date Added",
                               file_type=file_type)

# If no actions are picked, recommend books as the default action
if not (args.list_genres or
        args.num_authors or
        args.num_recommend_books or
        args.num_read_books):
    args.num_recommend_books = __default_num_books

if args.list_genres:
    print("List of categories and read-dates:")
    clist = blist.list_genres()
    clist_sorted = sorted(clist.keys(),
                          key=lambda g: ((clist[g]) or (datetime.date(1969, 12, 31))),
                          reverse=True)
    for cat in clist_sorted:
        if clist[cat]:
            print("%s: %s" % (shorten(cat, 30),
                              clist[cat].strftime("%d-%b-%y")))
        else:
            print("%s: Unread" % (shorten(cat, 30)))

if args.num_authors:
    if args.genre:
        print("List of best authors in genre %s:\n" % (args.genre))
    else:
        print("List of best authors:\n")

    for author in blist.choose_authors(args.num_authors, args.genre):
        print(author)

if args.num_read_books:
    print("List of read books:\n")
    hlist = blist.list_items_read(num_items=args.num_read_books,
                                  genre=args.genre,
                                  author=args.author)
    for book in hlist:
        print("%s: %s (%s, %.1f)" % (shorten(book["Title"], 50),
                                     shorten(", ".join(book["Authors"]), 20),
                                     book["Read date"].strftime("%d-%b-%y"),
                                     book["My Rating"]))

if args.num_recommend_books:
    print("List of recommended books:\n")

    # Choose best books based on an algorithm
    best_books = blist.choose_items(num_items=args.num_recommend_books,
                                    genre=args.genre,
                                    author=args.author)

    for book in best_books:
        print("%s: %s (%.1f, %s)" % (shorten(book["Title"], 50),
                                     shorten(", ".join(book["Authors"]), 20),
                                     book["Average Rating"],
                                     ",".join(book["Genre"])))
