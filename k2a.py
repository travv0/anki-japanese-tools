# -*- coding: utf-8 -*-

import sqlite3, sys, os, requests, configparser, codecs
from shutil import copyfile
from mutagen.mp3 import MP3

# importing shared will load config file and initialize Anki
import shared

# set up sqlite
try:
    conn = sqlite3.connect(os.path.expanduser(shared.dbPath))
except sqlite3.OperationalError as e:
    print("Unable to connect to Kindle database.  Please ensure your Kindle is plugged in and in USB mode.\nError: %s" % e)
    exit()

conn.row_factory = sqlite3.Row

c = conn.cursor()
c.execute('''
select word, stem, usage, lang
from words
join lookups on words.id = lookups.word_key;
''')

shared.resetLastImportTag()

for row in c.fetchall():
    shared.addToAnki(row['word'], row['usage'])

shared.saveAndCloseAnki()

if os.path.isfile(shared.dbPath + '.bak'):
    os.remove(shared.dbPath + '.bak')

print("Backing up Kindle vocabulary database...")
copyfile(shared.dbPath, shared.dbPath + '.bak')

if os.path.isfile(shared.dbPath + '.bak'):

    print("Removing words from Kindle vocabulary database...")
    c.execute('delete from words;')
    c.execute('delete from lookups;')

    conn.commit()
    print("Complete.  Please restart your Kindle to ensure database doesn't become corrupt.")

else:

    print("Unable to backup database, skipping Kindle flashcard deletion.")
    print("Complete.")

conn.close()

input("Press Enter to exit...")
