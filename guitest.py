import codecs, sys, os, configparser, sqlite3, requests

from appJar import gui
from jishoword import JishoWord
from mutagen.mp3 import MP3

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
collectionName = config['SETTINGS']['collectionName']
cardTypeName = config['SETTINGS']['cardTypeName']
deckName = config['SETTINGS']['deckName']
expressionFieldName = config['SETTINGS']['expressionFieldName']
wordsFile = 'words.txt'

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

PROFILE_HOME = os.path.expanduser(profilePath)
cpath = os.path.join(PROFILE_HOME, collectionName + ".anki2")

# end anki initialization

app = gui()
app.setSize(600, 400)

def getWordsFromFile(file):
    file = codecs.open(file, 'r', 'utf8')
    lines = file.read().replace("\r\n", "\n").split("\n")
    file.close()
    words = {}
    for i in range(0, len(lines)):
        lines[i] = lines[i].split("\t")
        while len(lines[i]) < 3:
            lines[i].append('')
        words[lines[i][0]] = lines[i][1:]
    return words


def vocabPane(words):
    linenum = 0
    with app.scrollPane("vocabList", 0, 0, 3):
        app.setSticky('nesw')

        for fword, data in words.items():
            word = JishoWord(fword)

            if word.populate():
                app.addCheckBox(word.expression, linenum, 0)
                if word.english:
                    app.setCheckBox(word.expression)

                app.addOptionBox("reading" + str(linenum), word.readings, linenum, 1)

                app.addEntry("def" + str(linenum), linenum, 2)
                app.setEntry("def" + str(linenum), word.english)

                app.addEntry("sentence" + str(linenum), linenum, 3)
                app.setEntry("sentence" + str(linenum), data[1])

                linenum += 1

def resetApp():
    app.removeAllWidgets()
    drawApp(app)

def submit(btn):
    wd = os.getcwd()

    try:
        col = Collection(cpath, log=True)

        model = col.models.byName(cardTypeName)
        col.decks.current()['mid'] = model['id']

        deck = col.decks.byName(deckName)

        os.chdir(wd)

        for noteid in col.findNotes('tag:k2a tag:lastimport'):
            note = col.getNote(noteid)
            note.delTag('lastimport')
            note.flush()

        i = 0
        for word, checked in app.getAllCheckBoxes().items():
            if checked and not col.findNotes('"%s:%s"' % (expressionFieldName, word)):
                note = col.newNote()
                note.model()['did'] = deck['id']

                expression = word
                reading = app.getOptionBox("reading" + str(i))
                english = app.getEntry("def" + str(i))

                audio = requests.get("https://assets.languagepod101.com/dictionary/japanese/audiomp3.php?",
                                     params = {'kanji': expression,
                                               'kana': reading if reading else expression})

                audioFileName = 'k2a_%s_%s.mp3' % (expression, reading if reading else expression)
                audioFilePath = '%s/%s.media/%s' % (PROFILE_HOME, collectionName, audioFileName)
                with open(audioFilePath, 'wb') as f:
                    f.write(audio.content)

                mp3 = MP3(audioFilePath)

                note.fields[expressionIndex] = expression
                note.fields[readingIndex] = '' if reading == None else reading
                note.fields[englishIndex] = english
                note.fields[sentenceIndex] = words[expression][1]
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
                      ((english[:50] + '..;') if len(english) > 53 else english).replace('<br/>', '; '))

                i += 1
        col.close(save=True)

        file = codecs.open(wordsFile, 'w', 'utf8')
        file.write("")
        file.close()

        resetApp()

    except sqlite3.OperationalError as e:
        print("Unable to connect to Anki database.  Please ensure Anki is not open and try again.\nError: %s" % e)

def runScript(file):
    os.system(sys.executable + ' import/' + file)
    resetApp()

def quickAdd(btn):
    file = codecs.open(wordsFile, 'a', 'utf8')
    file.write(app.getEntry("quickAddEntry") + '\n')
    file.close()

    resetApp()

files = os.listdir('import/')

app.addMenuList("File", ["Exit"], app.stop)
app.addMenuList("Import", files, runScript)

def drawApp(app):

    words = getWordsFromFile(wordsFile)

    vocabPane(words)

    app.addEntry("quickAddEntry", 1, 0, 2)
    app.addButton("Quick Add", quickAdd, 1, 2)

    app.setEntrySubmitFunction("quickAddEntry", quickAdd)

    app.addButton("Import into Anki and clear list", submit, 2, 1)

    app.go()

drawApp(app)
