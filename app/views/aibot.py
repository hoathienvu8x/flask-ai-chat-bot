# -*- coding: utf-8 -*-

from app import engine, ADMIN_KEY, MODEL_PICKLE, TOKENS_FILE, INTENTS_FILE, DATA_PICKLE
from flask import jsonify, request
import os, json, pickle, random, nltk
import numpy as np
from .util import check_token
from sklearn.neural_network import MLPClassifier

def load_kernel():
    model = None

    try:
        with open(MODEL_PICKLE, 'rb') as f:
            model = pickle.load(f)
    except:
        model = None

    words, labels = [], []
    try:
        with open(DATA_PICKLE,'rb') as f:
            words, labels = pickle.load(f)
    except:
        words, labels = [], []

    if not isinstance(words,list):
        words = []

    if not isinstance(labels,list):
        labels = []

    intents = []
    try:
        with open(INTENTS_FILE,'r') as f:
            intents = json.load(f)
    except:
        intents = []

    if not isinstance(intents, list):
        intents = []

    return (model, words, labels, intents)

model, words, labels, intents = load_kernel()

def bag_of_words(s, words):
    bag = [0 for _ in range(len(words))]
    s_words = nltk.word_tokenize(s)
    s_words = [stemmer.stem(word.lower()) for word in s_words]
    for se in s_words:
        for i, w in enumerate(words):
            if w == se:
                bag[i] = 1

    return np.array(bag)

@engine.route("/", methods=['GET','POST'])
def eliza():
    return jsonify(['Hi there'])

@engine.route("/api/reply", methods=['GET','POST'])
def eliza_reply():
    if request.method == "POST":
        req = request.form
    else:
        req = request.args

    question = req.get("q","").strip()

    if not question:
        return jsonify({
            'reply':'I am sorry! I don\'t understand you'
        })

    if model is None:
        return jsonify({
            'reply':question
        })

    results = model.predict([bag_of_words(question, words)])
    results_index = np.argmax(results)
    tag = labels[results_index]
    for tg in intents:
        if tg['tag'] == tag:
            responses = tg['responses']

    return jsonify({
        'reply':random.choice(responses)
    })

@engine.route("/api/intent", methods=['POST'])
def eliza_intent():
    token = request.args.get('token','').strip()
    if not check_token(token):
        return jsonify({
            'error':'Token is required'
        })

    if not request.content_type or not ("application/json" in request.content_type):
        return jsonify({
            'error':'Method is not allow, must be POST and content type is application/json'
        })

    intent = request.get_json()
    if not isinstance(intent, dict):
        return jsonify({
            'error':'Intent is not valid, must be json object'
        })

    if 'tag' not in intent or not isinstance(intent['tag'],str) or not intent['tag'].strip():
        return jsonify({
            'error':'Intent required tag key and tag key is string type'
        })

    if 'patterns' not in intent or not isinstance(intent['patterns'], list):
        return jsonify({
            'error':'Intent required patterns key and type must be list of string'
        })

    if len(intent['patterns']) == 0:
        return jsonify({
            'error':'Patterns is empty'
        })

    if 'responses' not in intent or not isinstance(intent['responses'], list):
        return jsonify({
            'error':'Intent require responses key, type must be list of string'
        })

    if 'context_set' in intent and not isinstance(intent['context_set'], list):
        del intent['context_set']

    intent['tag'] = intent['tag'].strip()
    intent['patterns'] = [ s.strip() for s in intent['patterns'] if s.strip() ]
    if len(intent['patterns']) == 0:
        return jsonify({
            'error':'Intent required tag key and tag key is string type and not empty'
        })

    intent['responses'] = [ s.strip() for s in intent['responses'] if s.strip() ]
    if len(intent['responses']) == 0:
        return jsonify({
            'error':'Intent require responses key, type must be list of string'
        })

    if 'context_set' in intent:
        intent['context_set'] = [ s.strip() for s in intent['context_set'] if s.strip() ]

    try:
        intents = []
        if os.path.isfile(INTENTS_FILE):
            with open(INTENTS_FILE, 'r') as f:
                intents = json.load(f)

        if not intents or not isinstance(intents,list):
            intents = []

        if len(intents) == 0:
            intents.append(intent)
        else:
            found = False
            for i, it in enumerate(intents):
                if it['tag'] == intent['tag']:
                    found = True
                    for pattern in intent['patterns']:
                        if pattern not in it['patterns']:
                            it['patterns'].append(pattern)

                    for response in intent['responses']:
                        if response not in it['responses']:
                            it['responses'].append(response)

                    if 'context_set' in intent:
                        if 'context_set' not in it:
                            it['context_set'] = []
                        for context in intent['context_set']:
                            if context not in it['context_set']:
                                it['context_set'].append(context)
                    intents[i] = it
                    intent = it
                    break

            if not found:
                intents.append(intent)
        with open(INTENTS_FILE,'w') as f:
            f.write(json.dumps(intents, ensure_ascii=False))
    except Exception as e:
        return jsonify({
            'error':str(e)
        })

    return jsonify({
        'intent':intent
    })

@engine.route("/api/token", methods=['GET', 'POST'])
def add_token():
    if request.method == "POST":
        req = request.form
    else:
        req = request.args

    auth = req.get('auth','').strip()
    if not auth or auth != ADMIN_KEY:
        return jsonify({
            'error':'Access Denied'
        })

    token = req.get('token','').strip()
    if len(token) < 16:
        return jsonify({
            'error':'Token is not valid'
        })

    try:
        tokens = []
        if os.path.isfile(TOKENS_FILE):
            with open(TOKENS_FILE,'r') as f:
                tokens = json.load(f)

        if not isinstance(tokens, list):
            tokens = []

        if token not in tokens:
            tokens.append(token)
            with open(TOKENS_FILE,'w') as f:
                f.write(json.dumps(tokens, ensure_ascii=False))

    except Exception as e:
        return jsonify({
            'error':str(e)
        })

    return jsonify({
        'token':token
    })

@engine.route('/api/train', methods=['GET', 'POST'])
def chatbot_train():
    if request.method == "POST":
        req = request.form
    else:
        req = request.args

    auth = req.get('auth','').strip()
    if not auth or auth != ADMIN_KEY:
        return jsonify({
            'error':'Access Denied'
        })

    if not os.path.isfile(INTENTS_FILE):
        return jsonify({
            'error':'No intents to train'
        })

    try:
        with open(INTENTS_FILE,'r') as f:
            data = json.load(f)
    except Exception as e:
        return jsonify({
            'error':str(e)
        })

    if not data or not isinstance(data, list):
        return jsonify({
            'error':'Error on load intents to train'
        })

    if len(data) == 0:
        return jsonify({
            'error':'No intents to train'
        })

    words, labels, docs_x, docs_y = ([],[],[],[])
    for intent in data:
        for pattern in intent["patterns"]:
            wrds = nltk.word_tokenize(pattern)
            words.extend(wrds)
            docs_x.append(wrds)
            docs_y.append(intent["tag"])

        if intent["tag"] not in labels:
            labels.append(intent["tag"])

    words = [stemmer.stem(w.lower()) for w in words if w != "?"]
    words = sorted(list(set(words)))
    labels = sorted(labels)

    training, output = ([],[])
    out_empty = [0 for _ in range(len(labels))]

    for x, doc in enumerate(docs_x):
        bag = []
        wrds = [stemmer.stem(w.lower()) for w in doc]
        for w in words:
            if w in wrds:
                bag.append(1)
            else:
                bag.append(0)

        output_row = out_empty[:]
        output_row[labels.index(docs_y[x])] = 1

        training.append(bag)
        output.append(output_row)

    training = np.array(training)
    output = np.array(output)

    with open(DATA_PICKLE,'wb') as f:
        pickle.dump((words, labels),f)

    mlp = MLPClassifier(hidden_layer_sizes=(8,8,8), activation='relu', solver='adam', max_iter=500)
    mlp.fit(training,output)

    return jsonify({
        'error':'No idea'
    })
