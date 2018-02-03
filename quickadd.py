# -*- coding: utf-8 -*-

import sqlite3, sys, os, requests, configparser, codecs, chardet, shared
from shutil import copyfile
from mutagen.mp3 import MP3

# configPath = sys.argv[1] if len(sys.argv) > 1 else 'config.ini'
configPath = 'config.ini'
wordsPath = sys.argv[1] if len(sys.argv) > 1 else None

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
collectionName = config['SETTINGS']['collectionName']
cardTypeName = config['SETTINGS']['cardTypeName']
deckName = config['SETTINGS']['deckName']
expressionFieldName = config['SETTINGS']['expressionFieldName']

try:
    expressionIndex = int(config['NOTE_FIELD_INDICES']['expression'])
    readingIndex = int(config['NOTE_FIELD_INDICES']['reading'])
    englishIndex = int(config['NOTE_FIELD_INDICES']['english'])
    sentenceIndex = int(config['NOTE_FIELD_INDICES']['sentence'])
    audioIndex = int(config['NOTE_FIELD_INDICES']['audio'])
except ValueError as e:
    print("Note field indices must be integers.\nError: %s" % e)
    exit()

# set up anki
sys.path.append("anki")
from anki.storage import Collection

wd = os.getcwd()

PROFILE_HOME = os.path.expanduser(profilePath)
cpath = os.path.join(PROFILE_HOME, collectionName + ".anki2")

try:
    col = Collection(cpath, log=True)
except sqlite3.OperationalError as e:
    print("Unable to connect to Anki database.  Please ensure Anki is not open and try again.\nError: %s" % e)
    exit()

model = col.models.byName(cardTypeName)
col.decks.current()['mid'] = model['id']

deck = col.decks.byName(deckName)

for noteid in col.findNotes('tag:k2a tag:lastimport'):
    note = col.getNote(noteid)
    note.delTag('lastimport')
    note.flush()

os.chdir(wd)

if wordsPath:
    file = open(wordsPath, 'r',
            encoding=chardet.detect(open(wordsPath, 'rb').read())['encoding'])
    words = file.read()
else:
    words = input("Enter word(s) to add: ")

wordList = words.replace('　', ' ').replace('\r\n', ' ').replace('\n', ' ').split(' ')

i = 0

for word in wordList:
    shared.addToAnki(col, deck, word, '')

    if (i % 50 == 0):
        print('\nSaving collection...\n')
        col.save()

    i += 1

print("Finished adding cards, saving collection...")
col.close(save=True)

input("Press Enter to exit...")
