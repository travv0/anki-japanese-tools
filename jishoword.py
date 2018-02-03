import requests

class JishoWord:
    def __init__(self, expression):
        self.expression = expression
        self.readings = []
        self.english = ''
        self.kanaOnly = False

    def populate(self):
        found = False

        r = requests.get("http://jisho.org/api/v1/search/words?",
                params = {'keyword': '"' + self.expression + '"'})
        json = r.json()

        if json['data']:

            entry = json['data'][0]

            for e in entry['japanese']:
                for k, v in e.items():
                    if v == self.expression:
                        found = True

                        if k == 'reading':
                            self.kanaOnly = True

                            break
                if found:
                    break

            if found:
                self.english = '<br/>'.join(list(map((lambda x: '; '.join(x['english_definitions'])),
                    entry['senses'])))
                if self.kanaOnly:
                    self.readings = []
                else:
                    for readingSection in entry['japanese']:
                        self.readings.append(readingSection['reading'])
                    self.readings = list(dict.fromkeys(self.readings))

            return found
