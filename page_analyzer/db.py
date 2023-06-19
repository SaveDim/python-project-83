import os

import psycopg2
import requests
import bs4

from dotenv import load_dotenv

from flask import (
    redirect,
    url_for,
    flash,
    session,
    request
)

from page_analyzer.url_parser import parser

load_dotenv()


DATABASE_URL = os.getenv("DATABASE_URL")
SECRET_KEY = os.getenv("SECRET_KEY")


def get_urls_list():
    with psycopg2.connect(DATABASE_URL) as conn:
        with conn.cursor() as curs:
            curs.execute(
                "SELECT urls.id, urls.name, url_checks.created_at, "
                "url_checks.status_code FROM urls "
                "LEFT JOIN url_checks ON urls.id = url_checks.url_id "
                "WHERE url_checks.url_id IS NULL OR "
                "url_checks.id = (SELECT MAX(url_checks.id) FROM url_checks "
                "WHERE url_checks.url_id = urls.id) ORDER BY urls.id DESC "
            )
            urls = curs.fetchall()
    return urls


def get_url_check(url_id):
    with psycopg2.connect(DATABASE_URL) as conn:
        with conn.cursor() as curs:
            curs.execute(
                "SELECT name FROM urls WHERE id = %s LIMIT 1", (url_id,)
            )
            url_to_check = curs.fetchall()[0][0]
            session["name"] = url_to_check
    try:
        response = requests.get(url_to_check)
        response.raise_for_status()
    except requests.exceptions.RequestException:
        flash("Произошла ошибка при проверке", "danger")
        conn.close()
        return redirect(url_for("show_single_url", url_id=url_id))

    status_code = response.status_code
    parsed_page = bs4.BeautifulSoup(response.text, "html.parser")
    title = parsed_page.title.text if parsed_page.find("title") else ""
    h1 = parsed_page.h1.text if parsed_page.find("h1") else ""
    description = parsed_page.find("meta", attrs={"name": "description"})
    description = description.get("content") if description else ""

    with psycopg2.connect(DATABASE_URL) as conn:
        with conn.cursor() as curs:
            curs.execute(
                """
                        INSERT INTO public.url_checks
                            (url_id, status_code, title, h1, description)
                        VALUES (%s, %s, %s, %s, %s)
                        """,
                (url_id, status_code, title, h1, description),
            )
            flash("Страница успешно проверена", "success")


def insert_url_into_db():
    url_from_form = request.form.get("url")
    parsed_url = parser(url_from_form)
    with psycopg2.connect(DATABASE_URL) as conn:
        with conn.cursor() as curs:
            curs.execute(
                "SELECT id FROM urls WHERE urls.name = %s LIMIT 1",
                (parsed_url,),
            )
            signle_url = curs.fetchall()
    if not signle_url:
        with psycopg2.connect(DATABASE_URL) as conn:
            with conn.cursor() as curs:
                curs.execute(
                    "INSERT INTO urls (name) VALUES (%s)", (parsed_url,)
                )
                flash("Страница успешно добавлена!", "success")
                session["name"] = parsed_url

                curs.execute(
                    "SELECT id FROM urls WHERE urls.name = %s LIMIT 1",
                    (parsed_url,),
                )
                url_id = curs.fetchall()[0][0]
    else:
        flash("Страница уже существует", "info")
        conn.close()
        url_id = signle_url[0][0]
    return url_id


def select_url(url_id):
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
    return single_url


def select_checks(url_id):
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
    return checks
