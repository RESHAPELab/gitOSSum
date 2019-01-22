#!/usr/bin/env python
# -*- coding: utf-8 -*-
# mining.py
# Created by Stephen White
# Date: 1/22/2019
# Purpose: This script will provide the necessary functionality to download json files
#          from GitHub's api.

from github import Github
import json

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


g = Github("Swhite9478", "$Aphira911")

repo = g.get_repo("google/gumbo-parser")
pulls = repo.get_pulls(state='all', sort='created', base='master')


print(repo.get_pull(pulls[0].number).raw_data)



# repo = g.get_user().get_repos()[7]
# pull_requests = repo.get_pulls()
# print(repo.name, '\n')
# # print(repo.raw_data)
# for pull in pull_requests:
#     print(pull.number)


# for repo in g.get_user().get_repos():
#     print(repo.name)
#     # repo.edit(has_wiki=False)
#     # to see all the available attributes and methods
#     # print(dir(repo))
#     print('\t', repo.raw_data)
