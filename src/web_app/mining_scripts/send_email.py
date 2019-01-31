#!/usr/bin/env python
# -*- coding: utf-8 -*-
# mining.py
# Created by Stephen White
# Date: 1/25/2019
# Purpose: This script will provide the necessary functionality send users
#          and email from gitossum@gmail.com

import mining_scripts.config # for authentication purposes 
import smtplib # Import smtplib for sending email 


def send_confirmation_email(repo_name, email_address):
    try:
        server = smtplib.SMTP('smtp.gmail.com:587')
        server.ehlo()
        server.starttls()
        server.login(config.EMAIL_ADDRESS, config.EMAIL_PASSWORD)
        subj = 'Git-OSS-um %s Mining Request Complete!' % repo_name
        msg = (
        '''Hello, this is an automated message letting you know that your ''' + \
        '''request to mine %s has been completed! Thank you for using our service!''' % repo_name + \
        '''\n\nUntil next time,\n\nGit-OSS-um Team <3''')
        message = "Subject: {}\n\n{}".format(subj, msg)
        server.sendmail(config.EMAIL_ADDRESS, email_address, message)
        return True 

    except Exception as e:
        print(e)
        return False 

    finally:
        server.quit() 