import numpy as np
import json

def post2list(posts):
    posts_list = []
    for post in posts:
        post = dict(zip(post.keys(), post))

        if not post['reply'] is None:
            reply = json.loads(post['reply'])
            comment = np.array(list(reply.values()))
            comment = np.flip(comment, axis=1)
            comment = np.array(comment).transpose().reshape(-1, 3)
            post['reply'] = comment.tolist()
        posts_list.append(post)
    return posts_list