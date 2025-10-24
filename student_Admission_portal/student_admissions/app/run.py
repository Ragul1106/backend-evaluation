from app import create_app, db
from app.models import Admin

app = create_app()

# for easy shell: flask shell or python run.py shell
@app.shell_context_processor
def make_shell_context():
    return {'db': db, 'Admin': Admin}
