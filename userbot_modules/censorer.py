# Replacer if swear in text
import re

censored = "#!$@><"


def replacer(message: str, swear_words, replacement):
    messageReturn = message
    for word in swear_words:
        if messageReturn.lower().__contains__(word):
            if replacement[swear_words.index(word)] != "NULL":
                print("SWEAR IS " + replacement[swear_words.index(word)])
                messageReturn = re.sub(word, replacement[swear_words.index(word)], messageReturn, flags=re.IGNORECASE)
                print(messageReturn)
            else:
                messageReturn = re.sub(word, swearGen(word), messageReturn, flags=re.IGNORECASE)

    return messageReturn


def swearGen(word: str):
    toGen = len(word)
    censorChars = censored
    while toGen >= len(censorChars):
        censorChars += censored
    return censorChars[0:toGen]


def test(message: str, swear_words):
    for word in swear_words:
        if message.lower().__contains__(word):
            return True
    return False
