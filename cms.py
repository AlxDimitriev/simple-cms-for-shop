from app import create_app, db
from app.models import User, Item, Group


app = create_app()


@app.shell_context_processor
def make_shell_context():
    return {'db': db, 'User': User, 'Item': Item, 'Group': Group}

# (venv) $ pip freeze > requirements.txt
# (venv) $ pip install -r requirements.txt

# <form action="{{ url_for('main.follow', username=user.username) }}" method="post">
#     {{ form.hidden_tag() }}
#     {{ form.submit(value=_('Follow'), class_='btn btn-default') }}
# </form>
