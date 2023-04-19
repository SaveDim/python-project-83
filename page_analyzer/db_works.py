import os
import psycopg2
from dotenv import load_dotenv


load_dotenv()


DATABASE_URL = os.getenv("DATABASE_URL")
SECRET_KEY = os.getenv('SECRET_KEY')


def get_conn():
    return psycopg2.connect(DATABASE_URL)


conn = get_conn()
cursor = conn.cursor()


def get_urls_list():
    cursor.execute(
        "SELECT urls.id, urls.name, url_checks.created_at, "
        "url_checks.status_code FROM urls "
        "LEFT JOIN url_checks ON urls.id = url_checks.url_id "
        "WHERE url_checks.url_id IS NULL OR "
        "url_checks.id = (SELECT MAX(url_checks.id) FROM url_checks "
        "WHERE url_checks.url_id = urls.id) ORDER BY urls.id DESC "
    )
    urls = cursor.fetchall()
    return urls


def insert_url_to_db():
    pass


def get_data_single_url():
    pass
