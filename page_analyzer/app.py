import os

import psycopg2
from flask import (
    Flask,
    render_template,
    request,
    url_for,
    get_flashed_messages,
    redirect,
    flash,
)
from dotenv import load_dotenv
from validators.url import url as is_valid

app = Flask(__name__)

load_dotenv()

app.config.update(SECRET_KEY=os.getenv("SECRET_KEY"))

DATABASE_URL = os.getenv("DATABASE_URL")


def get_connection():
    return psycopg2.connect(DATABASE_URL)


@app.route("/")
def index():
    messages = get_flashed_messages(with_categories=True)
    return render_template("index.html", messages=messages)


@app.post("/urls")
def add_url():
    url_from_form = request.form.to_dict()
    url = url_from_form.get("url")
    if not is_valid(url):
        flash("Некорректный URL", "danger")
        messages = get_flashed_messages(with_categories=True)
        return render_template("index.html",
                               url=url_from_form,
                               messages=messages), 422
    else:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id FROM urls WHERE urls.name = %s LIMIT 1",
            (url,),
        )
        result = cursor.fetchall()
        if not result:
            cursor.execute("INSERT INTO urls (name) VALUES (%s)", (url,))
            conn.commit()
            flash("Страница успешно добавлена", "success")

            cursor.execute(
                "SELECT id FROM urls WHERE urls.name = %s LIMIT 1",
                (url,),
            )
            url_id = cursor.fetchall()[0][0]
            conn.close()
        else:
            flash("Страница уже существует", "info")
            conn.close()
            url_id = result[0][0]
    return redirect(url_for("index", url_id=url_id))
