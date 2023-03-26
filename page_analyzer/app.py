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
import validators
from dotenv import load_dotenv


app = Flask(__name__)

load_dotenv()

app.config.update(SECRET_KEY=os.getenv("SECRET_KEY"))
app.config.update(DATABASE_URL=os.getenv("DATABASE_URL"))
app.config.update(DATABASE_URI=os.getenv("DATABASE_URI"))

DATABASE_URL = os.getenv("DATABASE_URL")
DATABASE_URI = os.getenv("DATABASE_URI")


def get_conn():
    return psycopg2.connect(DATABASE_URI)


def is_valid(url):
    return validators.url(url) and validators.length(url, max=255)


@app.route("/")
def index():
    messages = get_flashed_messages(with_categories=True)
    return render_template("index.html", messages=messages)


@app.post("/urls")
def add_url():
    url_from_form = request.form.get("url")
    if not is_valid(url_from_form):
        flash("Некорректный URL", "danger")
        messages = get_flashed_messages(with_categories=True)
        return (
            render_template(
                "index.html", url=url_from_form, messages=messages
            ),
            422,
        )

    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id FROM urls WHERE urls.name = %s LIMIT 1",
        (url_from_form,),
    )
    result = cursor.fetchall()
    if not result:
        cursor.execute("INSERT INTO urls (name) VALUES (%s)", (url_from_form,))
        conn.commit()
        flash("Страница успешно добавлена", "success")

        cursor.execute(
            "SELECT id FROM urls WHERE urls.name = %s LIMIT 1",
            (url_from_form,),
        )
        url_id = cursor.fetchall()[0][0]
    else:
        flash("Страница уже существует", "info")
        url_id = result[0][0]
        cursor.close()
    return redirect(url_for("index", url_id=url_id))


@app.route("/urls/<id>")
def show_single_url(id):
    messages = get_flashed_messages(with_categories=True)
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute(
        """SELECT *
        FROM urls
        WHERE urls.id = %s
        LIMIT 1""",
        (id,),
    )
    result = cursor.fetchall()
    conn.close()
    return render_template(
        "/url.html", url_id=id, result=result, messages=messages
    )


@app.get("/urls")
def show_urls():
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM urls ORDER BY id DESC")
    urls = cursor.fetchall()
    conn.close()
    return render_template(
        "urls.html",
        urls=urls,
        messages=get_flashed_messages(with_categories=True),
    )


@app.post("/urls/<id>/checks")
def check_url(id):
    messages = get_flashed_messages(with_categories=True)
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO url_checks
            (url_id, title, created_at)
        VALUES (%s, %s, %s)
        """,
    )
    conn.commit()
    conn.close()
    return render_template("/url.html", url_id=id, messages=messages)
