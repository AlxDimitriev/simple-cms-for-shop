from app import create_app, db
from app.models import User, Item, Group


app = create_app()


@app.shell_context_processor
def make_shell_context():
    return {'db': db, 'User': User, 'Item': Item, 'Group': Group}

# (venv) $ pip freeze > requirements.txt
# (venv) $ pip install -r requirements.txt

