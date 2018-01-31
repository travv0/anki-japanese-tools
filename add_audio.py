#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys, os, requests, configparser, codecs
from shutil import copyfile
from mutagen.mp3 import MP3

configPath =  sys.argv[1] if len(sys.argv) > 1 else 'config.ini'

config = configparser.ConfigParser()

save_interval = 50

errors = []

try:
    config.readfp(codecs.open(configPath, "r", "utf8"))
except FileNotFoundError as e:
    print('''Error loading config file "%s".  You can specify the path as the first command line argument.
Error: %s''' % (configPath, e))
    exit()

if not config.sections():
    print('Error loading config file "%s".  You can specify the path as the first command line argument.' % configPath)
    exit()

profilePath = config['SETTINGS']['profilePath']
collectionName = config['SETTINGS']['collectionName']
cardTypeName = config['SETTINGS']['cardTypeName']
deckName = config['SETTINGS']['deckName']
audioFieldName = config['SETTINGS']['audioFieldName']

try:
    expressionIndex = int(config['NOTE_FIELD_INDICES']['expression'])
    readingIndex = int(config['NOTE_FIELD_INDICES']['reading'])
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

i = j = 0

notes = col.findNotes('"deck:%s" %s:' % (deckName, audioFieldName))
notecnt = len(notes)

for noteid in notes:
    note = col.getNote(noteid)

    i += 1
    if not note.fields[audioIndex]:
        expression = note.fields[expressionIndex]
        reading = note.fields[readingIndex]

        audio = requests.get("https://assets.languagepod101.com/dictionary/japanese/audiomp3.php?",
                             params = {'kanji': expression,
                                       'kana': reading if reading else expression})

        audioFileName = 'k2a_%s_%s.mp3' % (expression, reading if reading else expression)
        audioFilePath = '%s/%s.media/%s' % (PROFILE_HOME, collectionName, audioFileName)
        try:
            with open(audioFilePath, 'wb') as f:
                f.write(audio.content)
        except OSError as e:
            errors.append((expression, e))

        mp3 = MP3(audioFilePath)

        if mp3.info.length < 5:
            note.fields[audioIndex] = '[sound:' + audioFileName + ']'

            print('%d/%d\tAdding audio "%s" for %s' % (i, notecnt, audioFileName, expression))
        else:
            os.remove(audioFilePath)

        note.flush()

        j += 1
        if j % save_interval == 0:
            col.save()
            print("\nCollection saved\n")

print("Finished adding audio, saving collection...")
col.close(save=True)

print("The following errors occurred:")

for error in errors:
    print("%s - %s" % (error[0], error[1]))

input("Press Enter to exit...")
