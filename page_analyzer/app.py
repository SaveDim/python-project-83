import os
import psycopg2

import validators
from dotenv import load_dotenv
from .db import (
    get_urls_list,
    get_url_check, insert_url_into_db,
)

from flask import (
    Flask,
    flash,
    get_flashed_messages,
    render_template,
    redirect,
    request,
    url_for,
)

app = Flask(__name__)

load_dotenv()

app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")
app.config["DATABASE_URL"] = os.getenv("DATABASE_URL")

DATABASE_URL = os.getenv("DATABASE_URL")
SECRET_KEY = os.getenv("SECRET_KEY")


def is_valid(url):
    if len(url) > 255:
        return {"result": False, "message": "URL превышает 255 символов"}
    if not validators.url(url):
        return {"result": False, "message": "Некорректный URL"}
    return {"result": True}


@app.route("/")
def index():
    messages = get_flashed_messages(with_categories=True)
    return render_template("index.html", messages=messages)


@app.post("/urls")
def add_url():
    url_from_form = request.form.get("url")
    validated = is_valid(url_from_form)
    if not validated["result"]:
        flash(validated["message"], "danger")
        messages = get_flashed_messages(with_categories=True)
        return (
            render_template(
                "index.html", url=url_from_form, messages=messages
            ),
            422,
        )
    url_id = insert_url_into_db()
    return redirect(url_for("show_single_url", url_id=url_id))


@app.route("/urls/<int:url_id>")
def show_single_url(url_id):
    messages = get_flashed_messages(with_categories=True)
    with psycopg2.connect(DATABASE_URL) as conn:
        with conn.cursor() as curs:
            curs.execute(
                """SELECT *
                FROM urls
                WHERE urls.id = %s
                LIMIT 1""",
                (url_id,),
            )
            single_url = curs.fetchall()
    with psycopg2.connect(DATABASE_URL) as conn:
        with conn.cursor() as curs:
            curs.execute(
                """
                        SELECT
                        id, status_code, h1, title,
                        description, created_at
                        FROM url_checks
                        WHERE url_checks.url_id = %s
                        ORDER BY id DESC
                        """,
                (url_id,),
            )
            checks = curs.fetchall()

    return render_template(
        "url.html", url=single_url[0], checks=checks, messages=messages
    )


@app.get("/urls")
def show_urls():
    messages = get_flashed_messages(with_categories=True)
    urls = get_urls_list()
    return render_template(
        "urls.html",
        urls=urls,
        messages=messages,
    )


@app.post("/urls/<int:url_id>/checks")
def check_url(url_id):
    get_url_check(url_id)
    return redirect(url_for("show_single_url", url_id=url_id))
