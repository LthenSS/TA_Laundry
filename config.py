import os
from urllib.parse import quote_plus

try:
    from dotenv import load_dotenv
except ModuleNotFoundError:
    def load_dotenv():
        return False


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ENV_PATH = os.path.join(BASE_DIR, ".env")
if os.path.exists(ENV_PATH):
    with open(ENV_PATH, "r", encoding="utf-8") as env_file:
        for line in env_file:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip())
load_dotenv(ENV_PATH, override=True)


class Config:
    SECRET_KEY = "smartwash123"

    def _build_database_uri():
        database_url = os.getenv("DATABASE_URL") or os.getenv("SQLALCHEMY_DATABASE_URI")
        if database_url:
            return database_url

        host = os.getenv("DB_HOST") or os.getenv("MYSQL_HOST") or "localhost"
        port = os.getenv("DB_PORT") or os.getenv("MYSQL_PORT") or "3306"
        username = os.getenv("DB_USERNAME") or os.getenv("MYSQL_USER") or "root"
        password = os.getenv("DB_PASSWORD") or os.getenv("MYSQL_PASSWORD") or ""
        database_name = os.getenv("DB_NAME") or os.getenv("MYSQL_DATABASE") or "smartwash"
        ssl_ca = os.getenv("DB_SSL_CA") or os.getenv("MYSQL_SSL_CA")
        ssl_verify_cert = os.getenv("DB_SSL_VERIFY_CERT") or os.getenv("MYSQL_SSL_VERIFY_CERT")
        ssl_verify_identity = os.getenv("DB_SSL_VERIFY_IDENTITY") or os.getenv("MYSQL_SSL_VERIFY_IDENTITY")

        encoded_password = quote_plus(password)
        uri = f"mysql+pymysql://{username}:{encoded_password}@{host}:{port}/{database_name}"

        query_parts = []
        if ssl_ca:
            query_parts.append(f"ssl_ca={quote_plus(ssl_ca)}")
        if ssl_verify_cert:
            query_parts.append(f"ssl_verify_cert={ssl_verify_cert}")
        if ssl_verify_identity:
            query_parts.append(f"ssl_verify_identity={ssl_verify_identity}")
        if query_parts:
            uri = f"{uri}?{'&'.join(query_parts)}"
        return uri

    SQLALCHEMY_DATABASE_URI = _build_database_uri()
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    WHATSAPP_API_URL = "https://api.fonnte.com/send"
    WHATSAPP_API_KEY = "RDMnrgiUFpWKxNqPwUgc"
    WHATSAPP_SENDER = "Smart Wash Laundry"