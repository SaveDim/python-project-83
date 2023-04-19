import os

import bs4
import requests
import validators
from dotenv import load_dotenv
from .db_works import get_urls_list, insert_url_to_db, get_data_single_url, get_conn

from flask import (
    Flask,
    flash,
    get_flashed_messages,
    render_template,
    redirect,
    request,
    session,
    url_for,
)

app = Flask(__name__)

load_dotenv()

app.config['SECRET_KEY'] = os.getenv("SECRET_KEY")
app.config['DATABASE_URL'] = os.getenv("DATABASE_URL")

DATABASE_URL = os.getenv("DATABASE_URL")
SECRET_KEY = os.getenv('SECRET_KEY')


def is_valid(url):
    if not validators.length(url, max=255):
        return {'result': False, 'message': 'URL превышает 255 символов'}
    elif not validators.url(url):
        return {'result': False, 'message': 'Некорректный URL'}
    return {'result': True}


@app.route("/")
def index():
    messages = get_flashed_messages(with_categories=True)
    return render_template("index.html", messages=messages)


@app.post("/urls")
def add_url():
    url_from_form = request.form.get("url")
    validated = is_valid(url_from_form)
    if not validated['result']:
        flash(validated['message'], "danger")
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
        session["name"] = url_from_form

        cursor.execute(
            "SELECT id FROM urls WHERE urls.name = %s LIMIT 1",
            (url_from_form,),
        )
        url_id = cursor.fetchall()[0][0]
        conn.close()
    else:
        flash("Страница уже существует", "info")
        conn.close()
        url_id = result[0][0]
    return redirect(url_for("show_single_url", url_id=url_id))


@app.route("/urls/<int:url_id>")
def show_single_url(url_id):
    messages = get_flashed_messages(with_categories=True)
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute(
        """SELECT *
        FROM urls
        WHERE urls.id = %s
        LIMIT 1""",
        (url_id,),
    )
    result = cursor.fetchall()
    cursor.execute(
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
    checks = cursor.fetchall()
    conn.close()

    return render_template(
        "/url.html", url=result[0], checks=checks, messages=messages
    )


@app.get("/urls")
def show_urls():
    messages = get_flashed_messages(with_categories=True)
    urls = get_urls_list()
    return render_template(
        "/urls.html",
        urls=urls,
        messages=messages,
    )


@app.post("/urls/<int:url_id>/checks")
def check_url(url_id):
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM urls WHERE id = %s LIMIT 1", (url_id,))
    url_to_check = cursor.fetchall()[0][0]
    session["name"] = url_to_check
    try:
        response = requests.get(url_to_check)
        response.raise_for_status()
    except requests.exceptions.RequestException:
        conn.close()
        flash("Произошла ошибка при проверке", "danger")
        return redirect(url_for("show_single_url", url_id=url_id))

    status_code = response.status_code
    parsed_page = bs4.BeautifulSoup(response.text, "html.parser")
    title = parsed_page.title.text if parsed_page.find("title") else ""
    h1 = parsed_page.h1.text if parsed_page.find("h1") else ""
    description = parsed_page.find("meta", attrs={"name": "description"})
    description = description.get("content") if description else ""

    cursor.execute(
        """
        INSERT INTO public.url_checks
            (url_id, status_code, title, h1, description)
        VALUES (%s, %s, %s, %s, %s)
        """,
        (url_id, status_code, title, h1, description),
    )
    conn.commit()
    conn.close()
    flash("Страница успешно проверена", "success")
    return redirect(url_for("show_single_url", url_id=url_id))
