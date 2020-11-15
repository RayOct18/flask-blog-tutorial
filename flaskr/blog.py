from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for
)
from werkzeug.exceptions import abort

from flaskr.auth import login_required
from flaskr.db import get_db

import time
import json

from .utils import *

bp = Blueprint('blog', __name__)

@bp.route('/', methods=('GET', 'POST'))
def index():
    db = get_db()
    posts = db.execute(
        'SELECT p.id, title, body, reply, created, author_id, username, liked'
        ' FROM post p JOIN user u ON p.author_id = u.id'
        ' ORDER BY created DESC'
    ).fetchall()
    
    max_id, page, comment_num = 0, 0, 0
    if request.values:
        page = int(request.values['ind'])
    end_post = len(posts) if (page + 1) * 5 > len(posts) else (page + 1) * 5
    start_post = page * 5
    end = True if len(posts) - start_post <= 5 else False
    posts = post2list(posts)
    if posts:
        max_id = posts[0]['id']
    for i in range(start_post, end_post):
        collapse = True
        text = posts[i]['body']
        line = text.splitlines()
        if len(line) > 6:
            text = '\n'.join(line[:6])
        elif len(text) > 400:
            text = text[:400]
        else:
            collapse = False
        posts[i]['body'] = text
        posts[i]['collapse'] = collapse
        if posts[i]['reply']:
            comment_num = len(posts[i]['reply'])
        posts[i]['comment_num'] = comment_num

    pages = [max_id, page, end]

    return render_template('blog/index.html', posts=posts[start_post:end_post], pages=pages)

@bp.route('/<int:id>', methods=('GET', 'POST'))
@login_required
def post(id):

    post = get_post(id)

    if request.method == 'POST':
        db = get_db()
        post = dict(zip(post.keys(), post))
        reply = request.form['reply']

        if reply:
            if not post['reply']:
                reply_dict = {'username':[], 'created':[], 'reply':[]}
            else:
                reply_dict = eval(post['reply'])
            cur_time = time.strftime('%Y-%m-%d', time.localtime())
            reply_dict['username'].append(g.user['username'])
            reply_dict['created'].append(cur_time)
            reply_dict['reply'].append(reply)

            db.execute(
                'UPDATE post SET reply = ? WHERE id = ?',
                (json.dumps(reply_dict), id)
            )
            db.commit()
            return redirect(url_for('blog.post', id=id))
        elif 'like' in request.form:
            db.execute(
                'UPDATE post SET liked = ? WHERE id = ?',
                (post['liked'] + 1, id)
            )
            db.commit()
            return redirect(url_for('blog.post', id=id))
        else:
            return redirect(url_for('blog.post', id=id))
    
    post = post2list([post])[0]

    return render_template('blog/post.html', post=post)

@bp.route('/create', methods=('GET', 'POST'))
@login_required
def create():
    if request.method == 'POST':
        title = request.form['title']
        body = request.form['body']
        error = None

        if not title:
            error = 'Title is required.'

        if error is not None:
            flash(error)
        else:
            db = get_db()
            db.execute(
                'INSERT INTO post (title, body, author_id)'
                ' VALUES (?, ?, ?)',
                (title, body, g.user['id'])
            )
            db.commit()
            return redirect(url_for('blog.index'))
    return render_template('blog/create.html')

def get_post(id, check_author=False):
    post = get_db().execute(
        'SELECT p.id, title, body, reply, liked, created, author_id, username'
        ' FROM post p JOIN user u ON p.author_id = u.id'
        ' WHERE p.id = ?',
        (id,)
    ).fetchone()

    if post is None:
        abort(404, "Post id {0} doesn't exist.".format(id))

    if check_author and post['author_id'] != g.user['id']:
        abort(403)

    return post

@bp.route('/<int:id>/update', methods=('GET', 'POST'))
@login_required
def update(id):
    post = get_post(id)

    if request.method == 'POST':
        title = request.form['title']
        body = request.form['body']
        error = None

        if not title:
            flash(error)
        else:
            db = get_db()
            db.execute(
                'UPDATE post SET title = ?, body = ?'
                ' WHERE id = ?',
                (title, body, id)
            )
            db.commit()
            return redirect(url_for('blog.post', id=id))

    return render_template('blog/update.html', post=post)


@bp.route('/<int:id>/delete', methods=('POST',))
@login_required
def delete(id):
    get_post(id)
    db = get_db()
    db.execute('DELETE FROM post WHERE id = ?', (id,))
    db.commit()
    return redirect(url_for('blog.index'))
