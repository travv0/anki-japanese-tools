import sqlite3, sys, os, requests, configparser, codecs
from shutil import copyfile
from mutagen.mp3 import MP3

configPath = sys.argv[1] if len(sys.argv) > 1 else 'config.ini'

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

try:
    expressionIndex = int(config['NOTE_FIELD_INDICES']['expression'])
    readingIndex = int(config['NOTE_FIELD_INDICES']['reading'])
    englishIndex = int(config['NOTE_FIELD_INDICES']['english'])
    sentenceIndex = int(config['NOTE_FIELD_INDICES']['sentence'])
    audioIndex = int(config['NOTE_FIELD_INDICES']['audio'])
except ValueError as e:
    print("Note field indices must be integers.\nError: %s" % e)
    exit()

def addToAnki(expression, sentence):
    found = False
    kanaOnly = False

    if not col.findNotes('"%s:%s"' % (expressionFieldName, expression)):

        r = requests.get("http://jisho.org/api/v1/search/words?",
                         params = {'keyword': '"' + expression + '"'})
        json = r.json()

        if json['data']:

            entry = json['data'][0]

            for e in entry['japanese']:
                for k, v in e.items():
                    if v == expression:
                        found = True

                        if k == 'reading':
                            kanaOnly = True

                        break
                if found:
                    break

            if found:

                note = col.newNote()
                note.model()['did'] = deck['id']

                english = '<br/>'.join(list(map((lambda x: '; '.join(x['english_definitions'])),
                                                entry['senses'])))

                if not ('reading' not in entry['japanese'][0] or (kanaOnly and len(expression) == 1)):

                    if kanaOnly:
                        reading = ''
                    else:
                        reading = entry['japanese'][0]['reading']

                    sentence = ''

                    audio = requests.get("https://assets.languagepod101.com/dictionary/japanese/audiomp3.php?",
                                         params = {'kanji': expression,
                                                   'kana': reading if reading else expression})

                    audioFileName = 'k2a_%s_%s.mp3' % (expression, reading if reading else expression)
                    audioFilePath = '%s/%s.media/%s' % (PROFILE_HOME, collectionName, audioFileName)
                    with open(audioFilePath, 'wb') as f:
                        f.write(audio.content)

                    mp3 = MP3(audioFilePath)

                    note.fields[expressionIndex] = expression
                    note.fields[readingIndex] = reading
                    note.fields[englishIndex] = english
                    note.fields[sentenceIndex] = sentence
                    if mp3.info.length < 5:
                        note.fields[audioIndex] = '[sound:' + audioFileName + ']'
                    else:
                        os.remove(audioFilePath)

                    tags = 'k2a lastimport'
                    note.tags = col.tags.canonify(col.tags.split(tags))
                    m = note.model()
                    m['tags'] = note.tags
                    col.models.save(m)

                    col.addNote(note)

                    print("Added %s " % expression, end='')
                    if reading:
                        print("(%s) " % reading, end='')
                    print("to Anki: %s" %
                          ((english[:50] + '...') if len(english) > 53 else english).replace('<br/>', '; '))

def saveAndCloseAnki():
    print("Finished adding cards, saving collection...")
    col.close(save=True)

def resetLastImportTag():
    for noteid in col.findNotes('tag:k2a tag:lastimport'):
        note = col.getNote(noteid)
        note.delTag('lastimport')
        note.flush()

def saveAnki():
    print('\nSaving collection...\n')
    col.save()
