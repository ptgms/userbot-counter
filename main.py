import json
import logging
import os
import random
import sys
import threading
import time
from json import JSONDecodeError

import praw
import requests
import wget
from flask import Flask
from flask_cors import CORS
from telethon import TelegramClient, events
from telethon.events import NewMessage
from telethon.tl.functions.users import GetFullUserRequest

from userbot_modules import censorer
from userbot_modules import jpeg
from userbot_modules import utils

log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)


def get_env(name, message, cast=str):
    if name in os.environ:
        return os.environ[name]
    while True:
        value = input(message)
        try:
            return cast(value)
        except ValueError as exc:
            print(exc, file=sys.stderr)
            time.sleep(1)


banned_chars = ",.!?`"

app = Flask(__name__)
CORS(app)

session = os.environ.get('TG_SESSION', 'printer')
api_id = 0
api_hash = ""
proxy = None

last_message = "Nothing sent since last start, please wait!"
bio = "Nothing sent since last start, please wait!"

reddit_client = ""
reddit_secret = ""
reddit_user = ""

swear_dis = True

allowed_list = []

try:
    with open("config.json", 'r') as outfile:
        settings = json.load(outfile)
        for row in settings:
            if "api_id" in row:
                api_id = row[1]
            elif "api_hash" in row:
                api_hash = row[1]
            elif "allowed" in row:
                allowed_list = row[1].split(" ")
                print(allowed_list)
            elif "reddit_client" in row:
                reddit_client = row[1]
            elif "reddit_secret" in row:
                reddit_secret = row[1]
            elif "reddit_user" in row:
                reddit_user = row[1]
        if api_id == 0 or api_hash == "":
            print("Configs couldn't be loaded, will store dummy configs. Replace them with your data!")
            exit(1)
except (JSONDecodeError, FileNotFoundError) as e:
    print("Configs couldn't be loaded, will store dummy configs. Replace them with your data!")
    settings = [["api_id", "1234"], ["api_hash", "1234"]]
    with open("config.json", "w") as outfileSave:
        json.dump(settings, outfileSave)
    exit(1)

mentions = [["DefaultPlaceHolderValue", 0]]
mentions_all = [["DefaultPlaceHolderValue", 0]]

try:
    with open("stats.json", 'r') as outfile:
        mentions = json.load(outfile)
except (JSONDecodeError, FileNotFoundError) as e:
    settings = [["DefaultPlaceHolderValue", 0]]
    with open("stats.json", "w") as outfileSave:
        json.dump(mentions, outfileSave)
    mentions = [["DefaultPlaceHolderValue", 0]]

try:
    with open("stats_all.json", 'r') as outfileAll:
        mentions_all = json.load(outfileAll)
except (JSONDecodeError, FileNotFoundError) as e:
    settings = [["DefaultPlaceHolderValue", 0]]
    with open("stats_all.json", "w") as outfileSaveAll:
        json.dump(mentions, outfileSaveAll)
    mentions_all = [["DefaultPlaceHolderValue", 0]]


@app.route('/getMentions')
def getMentions():
    return app.response_class(json.dumps(mentions), mimetype='application/json')


@app.route('/getAll')
def getAll():
    if len(mentions_all) <= 10:
        return app.response_class(json.dumps([["NOTENOUGHERROR", 0]]), mimetype='application/json')
    sorted_all = sorted(mentions_all, key=lambda x: x[1], reverse=True)[:10]
    return app.response_class(json.dumps(sorted_all), mimetype='application/json')


@app.route('/lastMessage')
def lastMessage():
    if last_message == "Nothing sent since last start, please wait!":
        return app.response_class(last_message, mimetype='application/text')
    return app.response_class(last_message.strftime("%m/%d/%Y, %H:%M:%S"), mimetype='application/text')


@app.route('/getBio')
def getBio():
    return app.response_class(bio, mimetype='application/text')


def runApp():
    app.run(host="0.0.0.0", port="5000")


threading.Thread(target=runApp).start()

client = TelegramClient(session, api_id, api_hash, proxy=proxy).start()

reddit_enable = False

if reddit_client != "" and reddit_secret != "" and reddit_user != "":
    reddit = praw.Reddit(
        client_id=reddit_client,
        client_secret=reddit_secret,
        user_agent=reddit_user
    )
    reddit_enable = True

swear_words = []
replacement = []


@client.on(events.NewMessage(outgoing=True))
async def handler(event):
    global bio
    global last_message
    full = await client(GetFullUserRequest('me'))
    bio = full.about
    last_message = event.date
    global mentions
    message = event.text
    message_filter = message
    for bannedChar in banned_chars:
        message_filter = message_filter.replace(bannedChar, "")
    for word in message_filter.split(" "):
        if word == "" or len(word) == 1:
            continue
        # print("GOT WORD: " + word)
        done = False
        for row in mentions_all:
            if row[0] == word.lower():
                row[1] = int(row[1]) + 1
                with open("stats_all.json", "w") as outfileSaveAll:
                    json.dump(mentions_all, outfileSaveAll)
                done = True
        if done:
            continue
        mentions_all.append([word, 1])
        with open("stats_all.json", "w") as outfileSaveAll:
            json.dump(mentions_all, outfileSaveAll)

    if message.startswith("!"):
        await event.edit(message[1:len(message)])
    elif censorer.test(message, swear_words):
        if not swear_dis:
            if not message.startswith("yo bro gimme "):
                await event.edit(censorer.replacer(message, swear_words, replacement))
    elif message.lower() == "jpeg this":
        if event.reply_to_msg_id:
            pic_event = await event.get_reply_message()
            if not await _is_picture_event(pic_event):
                await event.answer("`Invalid message type!`")
                return
            download_res = await client.download_media(pic_event)
            send = jpeg.jpegify(download_res)
            if send != "NULL":
                await event.reply(file=send)
            else:
                await event.reply("Unsupported image!")
            utils.cleanup(download_res)
    elif message.startswith("pls count this: "):
        toAdd = message[16:len(message)]
        mentions.append([toAdd, 0])
        with open("stats.json", "w") as outfileSave:
            json.dump(mentions, outfileSave)
        await event.reply("Added " + toAdd + " to the counting list!")
        return
    elif message.startswith("pls delete this: "):
        toRemove = message[17:len(message)]
        for row in mentions:
            if row[0].lower() == toRemove.lower():
                mentions.pop(mentions.index(row))
                await event.reply("Removed " + toRemove + " from the counting list!")
                with open("stats.json", "w") as outfileSave:
                    json.dump(mentions, outfileSave)
                return
        await event.reply("I am not counting a thing called " + toRemove + ".")
    elif message.split(" ")[0].lower() == "show":
        if message.split(" ")[1].lower() == "stats":
            toSend = "**Total mentions:**\n"
            for row in mentions:
                toSend += "**" + str(row[0]) + "** has **" + str(row[1]) + "** mentions\n"
            await event.reply(toSend)
        elif message.split(" ")[1].lower() == "all":
            toSend = "**Total mentions of all words (top 10):**\n"
            sorted_all = sorted(mentions_all, key=lambda x: x[1], reverse=True)
            print(sorted_all[:10])
            if len(sorted_all) <= 10:
                toSend += "Not enough words in the database! Please wait a bit!"
            else:
                for row in sorted_all[:10]:
                    # print(row[1])
                    toSend += "**" + str(row[0]) + "** has **" + str(row[1]) + "** mentions\n"
            await event.reply(toSend)
    if message.startswith("yo bro gimme "):
        toSearch = message[13:len(message)]
        if reddit_enable:
            submissions = list(reddit.subreddit(toSearch).hot(limit=50))
            submission = reddit.submission(random.choice(submissions))
            while submission.is_self and not submission.url.endswith(".jpg"):
                while not submission.url.endswith(".jpg"):
                    submission = reddit.submission(random.choice(submissions))
            download = submission.url
            save_as = download.split("/")[-1]
            # print(save_as)
            wget.download(download, save_as + ".jpg")
            await event.reply(file=save_as + ".jpg")
            # await event.delete()
            os.remove(save_as + ".jpg")
        else:
            await event.reply("nahw bro sorry")
    for mentionRow in mentions:
        mention = mentionRow[0]
        send = ""
        if message_filter.lower().__contains__(mention.lower()):
            print("FOUND " + mention)
            if " " in mention.lower():
                mentions[mentions.index(mentionRow)][1] = int(mentions[mentions.index(mentionRow)][1]) + 1
                if int(mentions[mentions.index(mentionRow)][1]) % 10 == 0:
                    send = '**CONGRATULATIONS!**\nThe word \"' + mention + '\" has been mentioned ' + str(
                        mentions[mentions.index(mentionRow)][1]) + ' times now! You should feel proud!'
            else:
                occurrences = count_occurrences(mention.lower(), message_filter.lower())
                print(occurrences)
                for i in range(0, occurrences):
                    mentions[mentions.index(mentionRow)][1] = int(mentions[mentions.index(mentionRow)][1]) + 1
                    if int(mentions[mentions.index(mentionRow)][1]) % 10 == 0:
                        send = '**CONGRATULATIONS!**\nThe word \"' + mention + '\" has been mentioned ' + str(
                            mentions[mentions.index(mentionRow)][1]) + ' times now! You should feel proud!'

            if send != "":
                await event.reply(send)

            with open("stats.json", "w") as outfile_save:
                json.dump(mentions, outfile_save)


@client.on(events.NewMessage(outgoing=False))
async def handler_extern(event):
    from_user = event.to_id.user_id
    # print(from_user)
    if allowed_list.__contains__(str(from_user)):
        # print("User " + str(from_user) + " sent a message")
        if event.text.lower() == "i hate myself" or event.text.lower() == "i need support":
            if reddit_enable:
                submissions = list(reddit.subreddit('wholesomememes').hot(limit=50))
                submission = reddit.submission(random.choice(submissions))
                while submission.is_self:
                    submission = reddit.submission(random.choice(submissions))
                download = submission.url
                save_as = download.split("/")[-1]
                print(save_as)
                wget.download(download, save_as)
                await event.reply(file=save_as)
                os.remove(save_as)
            else:
                await event.reply("No you don't")


def is_url_image(image_url):
    image_formats = ("image/png", "image/jpeg", "image/jpg")
    r = requests.head(image_url)
    if r.headers["content-type"] in image_formats:
        return True
    return False


def count_occurrences(word, sentence):
    return sentence.lower().split().count(word)


async def _is_picture_event(event: NewMessage.Event) -> bool:
    if event.sticker or event.photo:
        return True
    if event.document and "image" in event.document.mime_type:
        return True

    return False


try:
    filepath = 'swear.txt'
    with open(filepath) as fp:
        for cnt, line in enumerate(fp):
            swear_words.append(line.split(",")[0])
            replacement.append(line.split(",")[1].replace("\n", ""))
    if len(swear_words) != len(replacement):
        print("No replacement for every word!")
        exit(1)
    # print(swear_words)
    print("The bot is now running!")
    print('(Press Ctrl+C to stop this)')
    client.run_until_disconnected()
finally:
    client.disconnect()
