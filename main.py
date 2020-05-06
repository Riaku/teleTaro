import logging
import pymongo
from telegram.ext import Updater
from nltk.corpus import sentiwordnet as swn
from nltk.corpus import wordnet as wn
from datetime import datetime
##read files
telegramToken = open("telegramToken.txt", "r")
logfile = open("tarolog.txt", "a")
logfile.write("Starting teletaro...")

#logging specification
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)



# Telegram token and updater
updater = Updater(token=telegramToken.readline(), use_context=True)
telegramToken.close()
dispatcher = updater.dispatcher
updater.start_polling()


#mongodb connection
client = pymongo.MongoClient("mongodb://127.0.0.1:27017")
database = client['TARO']
messagesdb = database['messages']
userscoredb = database['userscore']
messages = messagesdb.find({})

###############################
##                           ##
##      static commands      ##
##                           ##
###############################

## gives the sending user their score
def myscore(update, context):
    userscore = userscoredb.find({"name": update.message.from_user.username})
    for m in userscore:
        context.bot.send_message(chat_id=update.effective_chat.id, text="Your positivity score is: "+ str(m.get('score')))

## finds the top 10 most postiive users
def top10score(update, context):
    allscore = userscoredb.find({},sort=[("score", pymongo.DESCENDING)])
    UserList = ""
    x = 0
    for m in allscore:
        UserList = UserList + str(m.get('name')) + " " + str(m.get('score')) + ", "
        x += 1
        if(x == 10):
            break
    context.bot.send_message(chat_id=update.effective_chat.id, text="**The Top Ten most positive Users Are**\n " + UserList)



from telegram.ext import CommandHandler
myscore_handler = CommandHandler('myscore', myscore)
top10score_handler = CommandHandler('top10score', top10score)
dispatcher.add_handler(myscore_handler)
dispatcher.add_handler(top10score_handler)

##############

##record messages and scores
def echo(update, context):
    print('Message from ' + str(update.message.from_user))

    words = update.message.text
    score = 0
    for w in words.split():
        ss = wn.synsets(w)
        if ss:
            tmp = wn.synsets(w)[0].pos()
            try:
                breakdown = swn.senti_synset(w + '.' + tmp + '.01')
            except:
                continue
        else:
            continue
        score = score + breakdown.pos_score() - breakdown.neg_score()
    userscored = userscoredb.find({"name": update.message.from_user.username})
    messagesdb.insert_one(
        {"time": datetime.now(), "chat id": str(update.message.chat.id), "name": update.message.from_user.username, "message": update.message.text, "score" : score})
    if userscoredb.count_documents({"name": update.message.from_user.username}) == 0:
        userscoredb.insert_one({"name": update.message.from_user.username, "score": score})
        print('new record created for '+update.message.from_user.username)
        logfile.write('new record created for '+update.message.from_user.username)
    else:
        for m in userscored:
            userscoredb.replace_one({'_id': m.get('_id')}, {"name" : update.message.from_user.username, "score": m.get('score') + score}, upsert=False)

from telegram.ext import MessageHandler, Filters
echo_handler = MessageHandler(Filters.text & (~Filters.command), echo)
dispatcher.add_handler(echo_handler)