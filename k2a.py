#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sqlite3, sys, os, requests
from shutil import copyfile

dbPath = 'd:/system/vocabulary/vocab.db' # configurable

# set up anki
sys.path.append("anki")
from anki.storage import Collection

wd = os.getcwd()

PROFILE_HOME = os.path.expanduser("~/AppData/Roaming/Anki2/ユーザー 1") # configurable
cpath = os.path.join(PROFILE_HOME, "collection.anki2")

col = Collection(cpath, log=True)

model = col.models.byName('Japanese Vocab') # configurable
col.decks.current()['mid'] = model['id']

deck = col.decks.byName('Japanese Vocab::Additional Japanese Vocab') # configurable

# set up sqlite
os.chdir(wd)
conn = sqlite3.connect(dbPath)
conn.row_factory = sqlite3.Row

c = conn.cursor()
c.execute('''
select word, stem, usage, lang
from words
join lookups on words.id = lookups.word_key;
''')

for row in c.fetchall():

    expression = row['word']

    if row['lang'] == 'ja' and not col.findNotes('"expression:%s"' % row['word']):

        r = requests.get("http://jisho.org/api/v1/search/words?",
                         params = {'keyword': '"' + expression + '"'})
        json = r.json()

        if json['data']:

            entry = json['data'][0]
            note = col.newNote()
            note.model()['did'] = deck['id']

            english = '<br/>'.join(list(map((lambda x: '; '.join(x['english_definitions'])),
                                            entry['senses'])))
            reading = entry['japanese'][0]['reading']
            sentence = row['usage']

            note.fields[0] = expression
            note.fields[3] = reading
            note.fields[4] = english
            note.fields[7] = reading
            note.fields[8] = sentence

            tags = 'k2a'
            note.tags = col.tags.canonify(col.tags.split(tags))
            m = note.model()
            m['tags'] = note.tags
            col.models.save(m)

            col.addNote(note)

            print("Added %s (%s) to Anki." % (expression, reading))

print("Finished adding cards, saving collection...")
col.save()

print("Backing up Kindle vocabulary database...")
copyfile(dbPath, dbPath + '.bak')

if os.path.isfile(dbPath + '.bak'):

    print("Removing words from Kindle vocabulary database...")
    c.execute('delete from words;')
    c.execute('delete from lookups;')

    conn.commit()
    print("Complete.  Please restart your Kindle if you can still see flashcards on it.")

else:

    print("Unable to backup database, skipping Kindle flashcard deletion.")
    print("Complete.")
