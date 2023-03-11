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

conn = psycopg2.connect(DATABASE_URI)


def is_valid(url):
    if len(url) > 255:
        return {"result": False, "message": "URL превышает 255 символов"}
    elif not validators.url(url):
        return {"result": False, "message": "Некорректный URL"}
    return {"result": True}


@app.route("/")
def index():
    messages = get_flashed_messages(with_categories=True)
    return render_template("index.html", messages=messages)


@app.route("/urls", methods=['POST'])
def add_url():
    url_from_form = request.form['url']
    if not is_valid(url_from_form)["result"]:
        flash(is_valid(url_from_form)["message"], "danger")
        messages = get_flashed_messages(with_categories=True)
        return render_template("index.html",
                               url=url_from_form,
                               messages=messages), 422
    else:
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


@app.route("/urls", methods=['GET'])
def get_url_list():
    return render_template("urls.html")


@app.route("/urls/<id>")
def show_single_url(id):
    messages = get_flashed_messages(with_categories=True)
    with conn:
        with conn.cursor() as curs:
            curs.execute(
                "SELECT id, name, created_at FROM urls WHERE id = %s",
                (id,)
            )

            result_url = curs.fetchone()
            # curs.execute(
            #     "SELECT id, name, created_at, h1, title, description, "
            #     "created_at FROM urls WHERE url_id = %s "
            #     "ORDER BY id DESC", (id,)
            # )
            #
            # result_checks = curs.fetchall()
            url_id, name, created_at = result_url
    return render_template(
        "/url.html",
        url_id=url_id,
        name=name,
        created_at=created_at,
        messages=messages
    )


@app.get("/urls")
def show_urls():
    cursor = conn.cursor()
    with cursor as curs:
        curs.execute("SELECT * FROM urls ORDER BY id DESC")
        result = cursor.fetchall()
        cursor.close()
    return render_template('urls.html', urls=result)
