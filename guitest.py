import codecs

from appJar import gui
from jishoword import JishoWord

linenum = 0

app = gui()

def getWordsFromFile(file):
    file = codecs.open(file, 'r', 'utf8')
    lines = file.read().replace("\r\n", "\n").split("\n")
    for i in range(0, len(lines)):
        lines[i] = lines[i].split("\t")
    return lines

lines = getWordsFromFile('words.txt')
print(lines)

def submit(btn):
    for i in range(0, linenum):
        print(lines[i])
        print(app.getOptionBox("reading" + str(i)))
        print(app.getEntry("def" + str(i)))

with app.scrollPane("vocabList"):
    for line in lines:
        word = JishoWord(line[0])

        if word.populate():
            app.addCheckBox(word.expression, linenum, 0)
            if word.english:
                app.setCheckBox(word.expression)

            app.addOptionBox("reading" + str(linenum), word.readings, linenum, 1)

            app.addEntry("def" + str(linenum), linenum, 2)
            app.setEntry("def" + str(linenum), word.english)

            app.addEntry("sentence" + str(linenum), linenum, 3)
            app.setEntry("sentence" + str(linenum), line[2])

            linenum += 1

app.addButton("submit", submit)

app.go()
