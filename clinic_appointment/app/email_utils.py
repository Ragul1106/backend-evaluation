from flask_mail import Message
from . import mail
from flask import render_template

def send_email(subject, recipients, template, **context):
    msg = Message(subject, recipients=recipients)
    msg.body = render_template(template + '.txt', **context)
    try:
        msg.html = render_template(template + '.html', **context)
    except:
        pass
    mail.send(msg)
