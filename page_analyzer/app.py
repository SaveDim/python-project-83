import os

import psycopg2

from flask import Flask, render_template
from dotenv import load_dotenv

app = Flask(__name__)

load_dotenv()

PORT = os.getenv('PORT')


@app.route('/')
def index():
    return render_template('index.html')


if __name__ == '__main__':
    index()
    app.run('0.0.0.0', port=PORT, debug=True)
