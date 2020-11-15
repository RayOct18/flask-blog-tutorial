import sqlite3

import click
from flask import current_app, g
from flask.cli import with_appcontext

def get_db():
    # g is unique object for store data
    if 'db' not in g:
        # sqlite3.connect establishes a connection to the DATABASE file
        g.db = sqlite3.connect(
            # current_app is object for flask application to
            # handle request
            current_app.config['DATABASE'],
            detect_types=sqlite3.PARSE_DECLTYPES
        )
        # sqlite3.Row return rows that behave like dicts
        g.db.row_factory = sqlite3.Row

    return g.db

def close_db(e=None):
    db = g.pop('db', None)

    if db is not None:
        db.close()

def init_db():
    db = get_db()

    with current_app.open_resource('schema.sql') as f:
        db.executescript(f.read().decode('utf8'))


@click.command('init-db')
@with_appcontext # wraps command and guaranteed the command to be executed with script's application context
def init_db_command():
    """Clear the existing data and create new tables."""
    init_db()
    click.echo('Initialized the database.')

def init_app(app):
    app.teardown_appcontext(close_db)
    app.cli.add_command(init_db_command)
