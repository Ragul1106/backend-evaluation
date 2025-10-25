# Job Portal

Quickstart
```
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
cp .env.example .env  # set DEBUG=True for local
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

- Local dev uses MEDIA folder for resumes at /media/resumes/.
- Production: set DEBUG=False and provide CLOUDINARY_URL to store files on Cloudinary. Optionally configure SMTP for emails.
