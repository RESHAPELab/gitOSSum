#!/usr/bin/env python
# -*- coding: utf-8 -*-
# mining.py
# Created by Stephen White
# Date: 1/25/2019
# Purpose: This script will provide the necessary functionality send users
#          and email from gitossum@gmail.com



import django
django.setup() 
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from mining_scripts.config import * # for authentication purposes 
import smtplib # Import smtplib for sending email 


def send_mining_initialized_email(repo_name, email_address):
    if email_address == "":
        return 

    try:
        server = smtplib.SMTP('smtp.gmail.com:587')
        server.ehlo()
        server.starttls()
        server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        subj = 'Git-OSS-um %s Mining Request Initialized!' % repo_name
        msg = (
        '''Hello, this is an automated message letting you know that your ''' + \
        '''request to mine %s has been accepted! A confirmation email will be sent when your ''' + \
        '''repository has been fully mined. Thank you for using our service!''' % repo_name + \
        '''\n\nUntil next time,\n\nGit-OSS-um Team <3''')
        message = "Subject: {}\n\n{}".format(subj, msg)
        server.sendmail(EMAIL_ADDRESS, email_address, message)
        return True 

    except Exception as e:
        print(e)
        return False 

    finally:
        server.quit() 

def send_confirmation_email(repo_name, username, to_email):
    if to_email == "":
        return 

    mail_subject = 'Git-OSS-um %s Mining Request Complete!' % repo_name
    message = render_to_string('email_notifications/confirmation.html', {
        'user': username,
        'repo': repo_name
    })
    print("EMAIL SUBJECT:", mail_subject)
    print("EMAIL MESSAGE:", message)
    email = EmailMessage(mail_subject, message, to=[to_email])
    email.send()
    return True 

    

def send_repository_denied_email(repo_name, email_address):
    if email_address == "":
        return 

    try:
        server = smtplib.SMTP('smtp.gmail.com:587')
        server.ehlo()
        server.starttls()
        server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        subj = 'Git-OSS-um %s Mining Request Complete!' % repo_name
        msg = (
        '''Hello, this is an automated message letting you know that your ''' + \
        '''request to mine %s has been denied. We appologize for the inconvenience, ''' + \
        '''and thank you for using our service.''' % repo_name + \
        '''\n\nUntil next time,\n\nGit-OSS-um Team <3''')
        message = "Subject: {}\n\n{}".format(subj, msg)
        server.sendmail(EMAIL_ADDRESS, email_address, message)
        return True 

    except Exception as e:
        print(e)
        return False 

    finally:
        server.quit()

def send_repository_blacklist_email(repo_name, email_address):
    if email_address == "":
        return 

    try:
        server = smtplib.SMTP('smtp.gmail.com:587')
        server.ehlo()
        server.starttls()
        server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        subj = 'Git-OSS-um %s Mining Request Complete!' % repo_name
        msg = (
        '''Hello, this is an automated message letting you know that your ''' + \
        '''request to mine %s has been denied. The Administrator has chosen to ''' + \
        '''blacklist this repository, meaning it can no longer be requested. ''' + \
        '''We appologize for the inconvenience, and thank you for using our service.''' % repo_name + \
        '''\n\nUntil next time,\n\nGit-OSS-um Team <3''')
        message = "Subject: {}\n\n{}".format(subj, msg)
        server.sendmail(EMAIL_ADDRESS, email_address, message)
        return True 

    except Exception as e:
        print(e)
        return False 

    finally:
        server.quit() 