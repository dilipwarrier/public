#!/usr/bin/env python
"""
Module recommend_movie.

Recommend the next movie to watch based on an input list of movies.
"""

import sys
import csv
import datetime
import argparse
import textwrap

import parse_items

__default_num_movies = 20

def shorten(str, width):
    # Clean up string for printing: ensure it's exactly of width length with
    # ellipsis as needed
    return textwrap.shorten(str, width=width, placeholder="...").ljust(width)


movies_xlsx_file = "C:/Users/Dilip/Google Drive/Personal/Movies_list.xlsx"
movie_list = parse_items.items_list(movies_xlsx_file,
                                    creator_field_name="Director",
                                    genre_field_names=["Genre",
                                                       "Language",
                                                       "Type"],
                                    read_date_field_name="Date Watched",
                                    file_type="excel")

description_str = "Search for and recommend movies.\nBy default, show the %d best movies to watch next." % (__default_num_movies)

parser = argparse.ArgumentParser(description=description_str)
parser.add_argument('-l', '--list_genres',
                    action='store_true',
                    default=False)
parser.add_argument('-w', '--list_watched_movies',
                    type=int,
                    dest='num_watched_movies',
                    default=None)
parser.add_argument('-r', '--recommend_movies',
                    type=int,
                    dest='num_recommend_movies',
                    default=None)
parser.add_argument('-g', '--restrict_by_genre',
                    dest='genre',
                    default=None)
parser.add_argument('-d', '--restrict_by_director',
                    dest='director',
                    default=None)
args = parser.parse_args()

# If no actions are picked, recommend movies as the default action
if not (args.list_genres or args.num_recommend_movies or args.num_watched_movies):
    args.num_recommend_movies = __default_num_movies

if args.list_genres:
    print("List of genres and watched-dates:")
    clist = movie_list.list_genres()
    clist_sorted = sorted(clist.keys(),
                          key=lambda g: clist[g] or datetime.date.min,
                          reverse=True)
    for cat in clist_sorted:
        if clist[cat]:
            print("%s: %s" % (shorten(cat, 30),
                              clist[cat].strftime("%d-%b-%y")))
        else:
            print("%s: Not watched" % (shorten(cat, 30)))

if args.num_watched_movies:
    print("List of watched movies:\n")
    hlist = movie_list.list_items_read(num_items=args.num_watched_movies,
                                       genre=args.genre,
                                       author=args.director)
    for movie in hlist:
        print("%s: %s (%s, %.1f)" % (shorten(movie["Title"], 50),
                                     shorten(movie["Author"], 20),
                                     movie["Read date"].strftime("%d-%b-%y"),
                                     movie["My Rating"]))

if args.num_recommend_movies:
    print("List of recommended movies:\n")
    # Choose best movies based on an algorithm
    best_movies = movie_list.choose_items(num_items=args.num_recommend_movies,
                                          genre=args.genre,
                                          author=args.director)

    for movie in best_movies:
        print("%s: %s (%.1f, %s)" % (shorten(movie["Title"], 50),
                                     shorten(movie["Author"], 20),
                                     movie["Average Rating"],
                                     ",".join(movie["Genre"])))
