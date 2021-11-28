# -*- coding: utf-8 -*-

from app import TOKENS_FILE
import os, json

def check_token(token):
    token = token.strip()
    if not token:
        return False

    tokens = []
    if not os.path.isfile(TOKENS_FILE):
        return False

    with open(token_file,'r') as f:
        tokens = json.load(f)

    if not isinstance(tokens, list):
        return False

    if token not in tokens:
        return False

    return True
