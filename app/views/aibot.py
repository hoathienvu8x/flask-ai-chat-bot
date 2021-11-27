# -*- coding: utf-8 -*-

from app import engine, DATA_FOLDER
from flask import jsonify, request
import os, json

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

    return jsonify({
        'reply':question
    })

@engine.route("/api/intent", methods=['POST'])
def eliza_intent():
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
        intents_file = os.path.join(DATA_FOLDER, 'intents.json')
        intents = []
        if os.path.isfile(intents_file):
            with open(intents_file, 'r') as f:
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
        with open(intents_file,'w') as f:
            f.write(json.dumps(intents, ensure_ascii=False))
    except Exception as e:
        return jsonify({
            'error':str(e)
        })

    return jsonify({
        'intent':intent
    })
