#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sqlite3, sys, os, requests, configparser, codecs
from shutil import copyfile

configPath =  sys.argv[1] if len(sys.argv) > 1 else 'config.ini'

config = configparser.ConfigParser()

try:
    config.readfp(codecs.open(configPath, "r", "utf8"))
except FileNotFoundError as e:
    print('''Error loading config file "%s".  You can specify the path as the first command line argument.
Error: %s''' % (configPath, e))
    exit()

if not config.sections():
    print('Error loading config file "%s".  You can specify the path as the first command line argument.' % configPath)
    exit()

dbPath = os.path.expanduser(config['SETTINGS']['dbPath'])
profilePath = config['SETTINGS']['profilePath']
collectionFileName = config['SETTINGS']['collectionFileName']
cardTypeName = config['SETTINGS']['cardTypeName']
deckName = config['SETTINGS']['deckName']
expressionFieldName = config['SETTINGS']['expressionFieldName']

try:
    expressionIndex = int(config['NOTE_FIELD_INDICES']['expression'])
    readingIndex = int(config['NOTE_FIELD_INDICES']['reading'])
    englishIndex = int(config['NOTE_FIELD_INDICES']['english'])
    sentenceIndex = int(config['NOTE_FIELD_INDICES']['sentence'])
except ValueError as e:
    print("Note field indices must be integers.\nError: %s" % e)
    exit()

# set up anki
sys.path.append("anki")
from anki.storage import Collection

wd = os.getcwd()

PROFILE_HOME = os.path.expanduser(profilePath)
cpath = os.path.join(PROFILE_HOME, collectionFileName)

try:
    col = Collection(cpath, log=True)
except sqlite3.OperationalError as e:
    print("Unable to connect to Anki database.  Please ensure Anki is not open and try again.\nError: %s" % e)
    exit()

model = col.models.byName(cardTypeName)
col.decks.current()['mid'] = model['id']

deck = col.decks.byName(deckName)

# set up sqlite
os.chdir(wd)

try:
    conn = sqlite3.connect(os.path.expanduser(dbPath))
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

for row in c.fetchall():

    expression = row['word']

    found = False

    if row['lang'] == 'ja' and not col.findNotes('"%s:%s"' % (expressionFieldName, expression)):

        r = requests.get("http://jisho.org/api/v1/search/words?",
                         params = {'keyword': '"' + expression + '"'})
        json = r.json()

        if json['data']:

            entry = json['data'][0]

            for e in entry['japanese']:
                for k in e.values():
                    if k == expression:
                        found = True

            if found:

                note = col.newNote()
                note.model()['did'] = deck['id']

                english = '<br/>'.join(list(map((lambda x: '; '.join(x['english_definitions'])),
                                                entry['senses'])))
                reading = entry['japanese'][0]['reading']
                sentence = row['usage']

                note.fields[int(config['NOTE_FIELD_INDICES']['expression'])] = expression
                note.fields[int(config['NOTE_FIELD_INDICES']['reading'])] = reading
                note.fields[int(config['NOTE_FIELD_INDICES']['english'])] = english
                note.fields[int(config['NOTE_FIELD_INDICES']['sentence'])] = sentence

                tags = 'k2a'
                note.tags = col.tags.canonify(col.tags.split(tags))
                m = note.model()
                m['tags'] = note.tags
                col.models.save(m)

                col.addNote(note)

                print("Added %s (%s) to Anki." % (expression, reading))

print("Finished adding cards, saving collection...")
col.save()

if os.path.isfile(dbPath + '.bak'):
    os.remove(dbPath + '.bak')

print("Backing up Kindle vocabulary database...")
copyfile(dbPath, dbPath + '.bak')

if os.path.isfile(dbPath + '.bak'):

    print("Removing words from Kindle vocabulary database...")
    c.execute('delete from words;')
    c.execute('delete from lookups;')

    conn.commit()
    print("Complete.  Please restart your Kindle.")

else:

    print("Unable to backup database, skipping Kindle flashcard deletion.")
    print("Complete.")

input("Press Enter to exit...")
