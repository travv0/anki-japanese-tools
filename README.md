# anki-japanese-tools
A collection of tools to make adding Japanese flashcards to Anki easier.  Import from Kindle, add missing audio, and quickly add cards by providing a list of words.

## Usage
Run either k2a.py (import into Anki from Kindle), add_audio.py (add audio clips from the web to Anki cards that don't have audio yet), or quickadd.py (provide a list of words to quickly add to Anki).

Each script can take a parameter to tell it where the configuration file is, otherwise it assumes 'config.ini' in the current working directory.

The most recently imported cards will have the tag "lastimport" in Anki for easy verification of imported cards.  Cards will not be made out of single kana to avoid adding accidental clicks from a Kindle.
