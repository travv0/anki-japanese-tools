# -*- coding: utf-8 -*-

import sqlite3, sys, os, requests, configparser, codecs
from shutil import copyfile
from mutagen.mp3 import MP3

# importing shared will load config file and initialize Anki
import shared

words = input("Enter word(s) to add: ")

wordList = words.replace('　', ' ').replace('\r\n', ' ').replace('\n', ' ').split(' ')

i = 0

shared.resetLastImportTag()

for word in wordList:
    shared.addToAnki(word, '')

    i += 1

    if (i % 50 == 0):
        shared.saveAnki()

shared.saveAndCloseAnki()
