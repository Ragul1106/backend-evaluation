# seed_doctors.py
from app import create_app, db
from app.models import Doctor

app = create_app()
with app.app_context():
    # check if any doctors already exist
    if not Doctor.query.first():
        d1 = Doctor(name='Dr. Smith', email='drsmith@example.com')
        d1.set_password('smith123')
        d2 = Doctor(name='Dr. Patel', email='drpatel@example.com')
        d2.set_password('patel123')

        db.session.add_all([d1, d2])
        db.session.commit()
        print("✅ Doctors added successfully.")
    else:
        print("ℹ️ Doctors already exist:")
        for doc in Doctor.query.all():
            print(f"- {doc.name} ({doc.email})")
