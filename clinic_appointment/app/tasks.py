from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime, timedelta
from .models import Appointment
from . import db

def send_reminders():
    now = datetime.utcnow()
    window_start = now + timedelta(hours=23)
    window_end = now + timedelta(hours=25)
    upcoming = Appointment.query.filter(Appointment.reminder_sent==False,
                                        Appointment.date>=window_start.date(),
                                        Appointment.date<=window_end.date()).all()
    for a in upcoming:
        # send email/sms and mark reminder_sent True
        ...
        a.reminder_sent = True
    db.session.commit()

def init_scheduler(app):
    scheduler = BackgroundScheduler()
    scheduler.add_job(lambda: with_app_context_send_reminders(app), 'interval', minutes=30)
    scheduler.start()
