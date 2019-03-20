# sovietmoviesonline-scrape
Python script for downloading films from sovietmoviesonline.com

Usage: $python3 flickscrape.py input.xml

Takes a single XML file that contains a sitemap of movie urls, gets relevant information (year, title, director, etc), exports information to a CSV, and then presents the option to download files.
 
Typically whenever an error is presented from a particular film link, it is merely skipped.

Bugs: 
Some films on the site are broken into separate parts and thus have appended characters that are not taken into account.

Some CSV entries are not proper.
