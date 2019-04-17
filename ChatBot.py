from wxpy import *
from rasa_nlu.training_data import load_data
from rasa_nlu.config import RasaNLUModelConfig
from rasa_nlu.model import Trainer
from rasa_nlu import config
import random
import re
from dateutil.parser import parse
import datetime
import csv
from iexfinance.stocks import Stock
from iexfinance.stocks import get_historical_data
import pandas as pd

INIT = 0
PEND = 1
DO_OPERATION = 2
END = 3


def getTrainer():
    trainer = Trainer(config.load("config_spacy.yml"))
    # Load the training data
    training_data = load_data('testData.json')
    # Create an interpreter by training the model
    interpreter = trainer.train(training_data)
    return interpreter

#load symbol data as dictionary with stock symbol as key and company name as value
def getSymbolData():
    reader = csv.DictReader(open('nyse-listed_csv.csv'))
    reader2 = csv.DictReader(open('nasdaq-listed_csv.csv'))
    result1 = {}
    result2 = {}
    for row in reader:
        result1[row['ACT Symbol']] = row['Company Name']

    for row in reader2:
        result2[row['Symbol']] = row['Security Name']
    result1.update(result2)
    return result1

#trainer set up
trainer = getTrainer()
#load local symbol data, so that we can find stock symbol given company name
symbolData = getSymbolData()

def interperat(message, interpreter):
    data = interpreter.parse(message)
    entity = []
    for i in data['entities']:
        entity.append((i['entity'], i['value']))
    return data['intent']['name'], entity


def greeting_respond(entities):
    greetingWithName = ['Hello, {0}', 'Hi, {0}', 'How are you, {0}']
    greetingWithoutName = ['Hello', 'Hi', 'How are you']

    for name, value in entities:
        #if user provided his name, call him with his name
        if name == 'name':
            #store the user name
            global user_name
            user_name = value.capitalize()
    if user_name == "unknown":
        response = random.choice(greetingWithoutName)
    else:
        response = random.choice(greetingWithName).format(user_name)
    return response

def goodbye_respond(name):
    goodbyeWithName = ['Bye {0}!', 'See you {0}', 'Goodbye {0}!']
    goodbyeWithouName = ['Bye', 'Goodbye', 'See you']
    if name == "unknown":
        response = random.choice(goodbyeWithouName)
    else:
        response = random.choice(goodbyeWithName).format(name)
    return response

#find all satisfied stock name and symbol as dictionary and let user pick one
def get_symbol(name):
    r = {}
    global symbolData
    for key, value in symbolData.items():
        # if user provide exact stock symbol, stop searching
        if name.lower() == key.lower():
            tp = {}
            tp[value] = key
            return tp
        #else search all
        if re.search(r'\b'+name+r'\b', value, re.IGNORECASE):
            r[value] = key
    return r

#
def user_selection(companies):
    global candidates
    candidates = companies
    response = "{} satisfied companies found:\n".format(len(companies))
    index = 1
    for key in companies:
        tp = "{0}. {1}( {2} )\n".format(index, key, companies[key])
        index += 1
        response += tp
    response += "Which one do you refer to?"
    global state
    state = PEND
    return response

def target_respond(entities):
    responses = 'What would you like to know about {0}?'
    global target_stock
    for name, value in entities:
        if name == 'company':
            target = value

    symbols = get_symbol(target)
    if len(symbols) == 0:
        #no symbol found
        target_stock = None
        return "Sorry, I cannot find a company named {}".format(target_stock)
    if len(symbols) == 1:
        #only one stock found
        target_stock = (list(symbols.keys())[0], list(symbols.values())[0])
        return responses.format(target_stock[0])
    else:
        #more than one symbols found
        global NEXT
        NEXT = "pickStock"
        response = user_selection(symbols)
        return response

#user select one company from candidates
#return the formal name of the company
def get_selection(user_choice):
    global candidates
    # format 1: given string order
    nth = {
        "first": 1,
        "second": 2,
        "third": 3,
        "fourth": 4,
        "fifth": 5
    }
    for n in nth:
        if n in user_choice.lower():
            index = nth[n]
            return (candidates.keys()[index-1], candidates.values()[index-1])

    # format 2:given index number
    format2 = re.search(r'\d+', user_choice)
    if format2:
        index = int(format2.group(0))
        return (candidates.keys()[index-1], candidates.values()[index-1])
    # format 3:given specific company name
    else:
        for comany, symbol in candidates.items():
            if re.search(user_choice, comany, re.IGNORECASE):
                return (comany, symbol)
            if re.search(user_choice, r"\b"+symbol+"\b", re.IGNORECASE):
                return (comany, symbol)
        return None

# if both company and time are provided, check price of given time, return new company as target
# if only company are given, check current price, return new company as target
def checkPrice(entities, message):
    global target_stock
    global state
    global time
    time = []
    # state == INIT, no target and time, find them from entities
    target = None
    if state == INIT:
        for name, value in entities:
            if name == 'company':
                target = value
            if name == 'time':
                time.append(value)
    #state == DO_OPERATION, target are given
    elif state == DO_OPERATION:
        for name, value in entities:
            if name == 'company':
                #if value == it, target unchanged, else changed the targe and get symbols again
                if value != "it":
                    target = value
            if name == 'time':
                time.append(value)
    time = formal_time(time)
    # if successfully get new company name , search symbol
    if target:
        symbols = get_symbol(target)
        if len(symbols) == 0:
            # no symbol found
            return "Sorry, I cannot find a company named {}".format(target_stock)
        if len(symbols) == 1:
            # only one stock found
            target_stock = (list(symbols.keys())[0], list(symbols.values())[0])
            r = get_price(target_stock[1], time)
            print(r)
            result = specific_op(r, message)
            return result
        else:
            # more than one symbols found
            # let user select one
            global NEXT
            NEXT = "check_price"
            global Last_input
            Last_input = message
            response = user_selection(symbols)
            return response
    #target unchanged, use the symbol and time from last sate
    else:
        r = get_price(target_stock[1], time)
        return specific_op(r, message)

#get the price, given exact stock symbol and time period
def get_price(symbol, times):
    #real time price
    if len(times) == 0:
        target = Stock(symbol)
        tp = target.get_quote()
        r={}
        tp_dic={}
        tp_dic['open'] = tp['open']
        tp_dic['high'] = tp['high']
        tp_dic['low'] = tp['low']
        tp_dic['close'] = tp['close']
        tp_dic['volume'] = tp['latestVolume']
        tp_dic['price'] = tp['latestPrice']
        r['Today'] = tp_dic
        return r

    elif len(times) == 1:
        df = get_historical_data(symbol, times[0], times[0])
        t = list(df.keys())[0]
        r = {}
        #make return value have same format
        df[t]["price"] = df[t]['close']
        r[t] = df[t]
        #r is a dic with only one specific date
        return r
    else:
        df = get_historical_data(symbol, times[0], times[1])
        for date in df:
            df[date]["price"] = df[date]["close"]
        return df

#parse string to date object
def formal_time(times):
    print(times)
    if len(times) == 0:
        return []
    else:
        t = []
        for time in times:
            date = parse(time, fuzzy=True)
            t.append(date.date())
        t.sort()
        return t


def specific_op(result, message):
    print(message)
    global target_stock
    r = ""
    if "open" in message:
        r+="Open price for {0}\n".format(target_stock[0])
        r+="date                open\n"
        for date in result:
            tp = "{0}           {1}\n".format(date, result[date]['open'])
            r += tp
        return r
    if "high" in message:
        r += "High price for {0}\n".format(target_stock[0])
        r+="date                high\n"
        for date in result:
            tp = "{0}           {1}\n".format(date, result[date]['high'])
            r += tp
        return r
    if "low" in message:
        r += "Low price for {0}\n".format(target_stock[0])
        r+="date                low\n"
        for date in result:
            tp = "{0}           {1}\n".format(date, result[date]['low'])
            r += tp
        return r
    if "close" in message:
        r += "Close price for {0}\n".format(target_stock[0])
        r+="date                close\n"
        for date in result:
            tp = "{0}           {1}\n".format(date, result[date]['close'])
            r += tp
        return r
    if "price" in message:
        r += "Price for {0}\n".format(target_stock[0])
        r += "date              price\n"
        for date in result:
            tp = "{0}           {1}\n".format(date, result[date]['close'])
            r += tp
        return r
    if "volume" in message:
        r += "Volumn for {0}\n".format(target_stock[0])
        r+="date                volume\n"
        for date in result:
            tp = "{0}           {1}\n".format(date, result[date]['volume'])
            r += tp
        return r
    if "summary" in message:
        r+="Summary for {0}:\n".format(target_stock[0])
        tp = pd.DataFrame.from_dict(result)
        r+= tp.to_string()
        return r
    return r



user_name = "unknown"
target_stock = None
state = INIT
#user's choice
candidates = {}
#given time
time = []
#when pending, remember the next operation supposed to do
NEXT = ""
Last_input = ""
# wxpy setup
bot = Bot()
user = bot.friends().search("ask")[0]
@bot.register(user, TEXT)
def print_msg(msg):
    #parse input message
    global user_name
    user_input = msg.text
    intent, entities = interperat(user_input, trainer)
    print(intent, entities)
    global state
    global target_stock
    if state == INIT:
        if intent == "greet":
            return greeting_respond(entities)
        elif intent == "goodbye":
            state = END
            return "But you haven't ask anything."
        elif intent == "pickStock":
            response = target_respond(entities)
            #if target exists, move to next state
            if target_stock:
                state = DO_OPERATION
            return response
        elif intent == "check_price":
            result = checkPrice(entities, user_input)
            state = DO_OPERATION
            return result
    elif state == PEND:
        #ask for required information
        target_stock = get_selection(user_input)
        #got exact target
        if target_stock:
            state = DO_OPERATION
            if NEXT == "pickStock":
                return "What can I tell you about {}?".format(target_stock[0])
            elif NEXT == "check_price":
                r = get_price(target_stock[1], time)
                result = specific_op(r, Last_input)
                return result
        # didn't get exact symbol
        else:
            return "Sorry, I didn't get your selection, please provide a specific name, symbol or index"

    elif state == DO_OPERATION:
        # check_price, keep the state
        if intent == "check_price":
            return checkPrice(entities, user_input)
        elif intent == "greet":
            if user_name == "unknown":
                return ('Hi')
            else:
                return ("Hell, {0}".format(user_name))
        elif intent == "goodbye":
            state = END
            return goodbye_respond(user_name)

        elif intent == "pickStock":

            response = target_respond(entities)
            print(response)
            return response
        else:
            return "Sorry, I didn't get you."
    elif state == END:
        msg.reply("We've already said goodbye, right?")
        if intent == "greet":
            state = INIT
            return "But I'm happy to help you."
        else:
            return "I'm tired. I'm not gonna to talk to you unless you say hello to me."

embed()