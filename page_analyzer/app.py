import os

import psycopg2
import bs4
import requests

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


@app.route("/urls/<int:id>")
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


@app.post('/urls/<int:id>/checks')
def check_url(id):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute('SELECT name FROM urls WHERE id = %s LIMIT 1', (id,))
    url_to_check = cur.fetchall()[0][0]
    try:
        response = requests.get(url_to_check)
        response.raise_for_status()
    except requests.exceptions.RequestException:
        conn.close()
        flash('Произошла ошибка при проверке', 'danger')
        return redirect(url_for('show_single_url', url_id=id))

    status_code = response.status_code
    parsed_page = bs4.BeautifulSoup(response.text, 'html.parser')
    title = parsed_page.title.text if parsed_page.find('title') else ''
    h1 = parsed_page.h1.text if parsed_page.find('h1') else ''
    description = parsed_page.find("meta", attrs={"name": "description"})
    description = description.get("content") if description else ''

    cur.execute("""
        INSERT INTO public.url_checks
            (url_id, status_code, title, h1, description)
        VALUES (%s, %s, %s, %s, %s)
        """,
                (id, status_code, title, h1, description),
                )
    conn.commit()
    conn.close()
    flash('Страница успешно проверена', 'success')
    return redirect(url_for('show_single_url', url_id=id))
