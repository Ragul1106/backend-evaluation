from flask_mail import Message
from . import mail
from flask import current_app, render_template

def send_email(subject, recipients, template_name, **context):
    msg = Message(subject, recipients=recipients)
    # you can create HTML templates under templates/emails/
    msg.body = render_template(f'emails/{template_name}.txt', **context)
    msg.html = render_template(f'emails/{template_name}.html', **context)
    mail.send(msg)
