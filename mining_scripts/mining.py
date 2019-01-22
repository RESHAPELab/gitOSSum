#!/usr/bin/env python
# -*- coding: utf-8 -*-
# mining.py
# Created by Stephen White
# Date: 1/22/2019
# Purpose: This script will provide the necessary functionality to store json data
#          from GitHub's API into the MongoDB database of our choosing 

from pymongo import MongoClient
from github import Github
import json


client = MongoClient('localhost', 27017)
db = client.backend_db
pull_requests = db.pullRequests

github_accounts = {
        0: ['Githubfake01', '5RNsya*z#&aA'],
        1: ['GithubFake02', '9dJeg^Bp^g63'],
	    2: ['Github-Fake03', '2A$p3$zy%aaD'],
	    3: ['GithubFake04', '4Yg3&MQN9x%F'],
        4: ['GithubFake05', 'Cm82$$bFa!xb'],
        5: ['GithubFake06', '2t*u2Y8P^tTk'],
        6: ['GithubFake07', 'Hk1233**012'],
        7: ['GithubFake08', 'PO11sd*^%$']
    }


g = Github("Githubfake01", "5RNsya*z#&aA")

repo = g.get_repo("google/gumbo-parser")
pulls = repo.get_pulls(state='all', sort='created', base='master')

raw_json = repo.get_pull(pulls[0].number).raw_data

pull_requests.update(raw_json, raw_json, upsert=True)

