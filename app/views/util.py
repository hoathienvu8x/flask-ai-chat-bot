# -*- coding: utf-8 -*-

from app import DATA_FOLDER
import os, json

def check_token(token):
    token = token.strip()
    if not token:
        return False

    tokens = []
    token_file = os.path.join(DATA_FOLDER, 'tokens.json')
    if not os.path.isfile(token_file):
        return False

    with open(token_file,'r') as f:
        tokens = json.load(f)

    if not isinstance(tokens, list):
        return False

    if token not in tokens:
        return False

    return True
