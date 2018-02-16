# -*- coding: utf-8 -*-

import sys, os, requests, configparser, codecs, sqlite3
from shutil import copyfile
from mutagen.mp3 import MP3

# importing shared will load config file and initialize Anki
import shared

shared.addAudio()

print("Finished adding audio, saving collection...")
shared.saveAndCloseAnki()

shared.printErrors()
