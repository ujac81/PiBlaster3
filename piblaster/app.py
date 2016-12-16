#!/usr/bin/env python3
""" app.py -- Flask main file -- run webserver from here.

@Author Ulrich Jansen <ulrich.jansen@rwth-aachen.de>
"""

from flask import Flask, render_template
from flask_bootstrap import Bootstrap


def create_app():
    app = Flask('piblaster')
    Bootstrap(app)

    app.config['BOOTSTRAP_SERVE_LOCAL'] = True

    return app


app = create_app()

@app.route('/')
def index():
    return render_template('index.html')


if __name__ == '__main__':

    app.run()
