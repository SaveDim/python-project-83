import os

from flask import Flask
from dotenv import load_dotenv

app = Flask(__name__)

load_dotenv()

PORT = os.getenv('PORT')


@app.route('/')
def main():
    return 'Hello!'


if __name__ == '__main__':
    main()
    app.run('0.0.0.0', port=PORT, debug=True)
