#!/usr/bin/env python
# -*- coding: utf-8 -*-
# mining.py
# Created by Stephen White
# Date: 1/25/2019
# Purpose: This script will provide the necessary functionality send users
#          and email from gitossum@gmail.com

 
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from mining_scripts.config import * # for authentication purposes 
import smtplib # Import smtplib for sending email 


def send_mining_initialized_email(repo_name, to_email):
    if to_email == "":
        return 

    try:
        server = smtplib.SMTP('smtp.gmail.com:587')
        server.ehlo()
        server.starttls()
        server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        subj = f'Git-OSS-um {repo_name} Mining Request Accepted!'
        msg = (
            f'''Hello {username},\n\n'''
            f'''This is an automated message letting you know that your ''' 
            f'''request to mine {repo_name} has been accepted! ''' 
            f'''A confirmation email will be sent when your repository has been fully mined. '''
            f'''\n\nThank you for using our service!\n\n'''
            f'''Until next time,\n\n'''
            f'''Git-OSS-um Team <3'''
        )
        message = "Subject: {}\n\n{}".format(subj, msg)
        server.sendmail(EMAIL_ADDRESS, to_email, message)
        return True 

    except Exception as e:
        print(e)
        return False 

    finally:
        server.quit() 

def send_confirmation_email(repo_name, username, to_email):
    if to_email == "":
        return 

    try:
        server = smtplib.SMTP('smtp.gmail.com:587')
        server.ehlo()
        server.starttls()
        server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        subj = f'Git-OSS-um {repo_name} Mining Request Complete!'
        msg = (
            f'''Hello {username},\n\n'''
            f'''This is an automated message letting you know that your ''' 
            f'''request to mine {repo_name} has been completed!''' 
            f'''\n\nThank you for using our service!\n\n'''
            f'''Until next time,\n\n'''
            f'''Git-OSS-um Team <3'''
        )
        message = "Subject: {}\n\n{}".format(subj, msg)
        print(message)
        server.sendmail(EMAIL_ADDRESS, to_email, message)
        return True 

    except Exception as e:
        print(e)
        return False 

    finally:
        server.quit() 

    

def send_repository_denied_email(repo_name, to_email):
    if to_email == "":
        return 

    try:
        server = smtplib.SMTP('smtp.gmail.com:587')
        server.ehlo()
        server.starttls()
        server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        subj = f'Git-OSS-um {repo_name} Mining Request Denied'
        msg = (
            f'''Hello {username},\n\n'''
            f'''This is an automated message letting you know that your ''' 
            f'''request to mine {repo_name} has been denied. We appologize for the inconvenience, ''' 
            f'''and thank you for using our service.\n\n'''
            f'''Until next time,\n\n'''
            f'''Git-OSS-um Team <3'''
        )
        message = "Subject: {}\n\n{}".format(subj, msg)
        server.sendmail(EMAIL_ADDRESS, to_email, message)
        return True 

    except Exception as e:
        print(e)
        return False 

    finally:
        server.quit()

def send_repository_blacklist_email(repo_name, to_email):
    if to_email == "":
        return 

    try:
        server = smtplib.SMTP('smtp.gmail.com:587')
        server.ehlo()
        server.starttls()
        server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        subj = f'Git-OSS-um {repo_name} Mining Request Blacklisted'
        msg = (
            f'''Hello {username},\n\n'''
            f'''This is an automated message letting you know that your ''' 
            f'''request to mine {repo_name} has been denied. The Administrator has chosen to ''' 
            f'''blacklist this repository, meaning it can no longer be requested. '''
            f'''We appologize for the inconvenience, and thank you for using our service.\n\n'''
            f'''Until next time,\n\n'''
            f'''Git-OSS-um Team <3'''
        )
        message = "Subject: {}\n\n{}".format(subj, msg)
        server.sendmail(EMAIL_ADDRESS, to_email, message)
        return True 

    except Exception as e:
        print(e)
        return False 

    finally:
        server.quit() 