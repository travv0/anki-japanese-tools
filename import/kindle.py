import sqlite3, sys, os, requests, configparser, codecs

configPath =  sys.argv[1] if len(sys.argv) > 1 else '../config.ini'

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
wordsFile = '../words.txt'

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

file = codecs.open(configPath, "a", "utf8")
for row in c.fetchall():
	file.write(row['word'] + '\t\t' + row['usage'])
file.close()