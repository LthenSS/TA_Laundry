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

        if os.getenv("VERCEL") == "1" and os.getenv("USE_SQLITE_FALLBACK") == "1":
            db_path = os.getenv("DB_PATH", "/tmp/smartwash.db")
            if db_path.startswith("/"):
                return f"sqlite:////{db_path.lstrip('/')}"
            return f"sqlite:///{db_path}"

        host = os.getenv("DB_HOST") or os.getenv("MYSQL_HOST") or "localhost"
        port = os.getenv("DB_PORT") or os.getenv("MYSQL_PORT") or "3306"
        username = os.getenv("DB_USERNAME") or os.getenv("MYSQL_USER") or "root"
        password = os.getenv("DB_PASSWORD") or os.getenv("MYSQL_PASSWORD") or ""
        database_name = os.getenv("DB_NAME") or os.getenv("MYSQL_DATABASE") or "smartwash"
        ssl_ca = os.getenv("DB_SSL_CA") or os.getenv("MYSQL_SSL_CA")
        ssl_ca_content = os.getenv("DB_SSL_CA_CONTENT") or os.getenv("MYSQL_SSL_CA_CONTENT")
        ssl_verify_cert = os.getenv("DB_SSL_VERIFY_CERT") or os.getenv("MYSQL_SSL_VERIFY_CERT")
        ssl_verify_identity = os.getenv("DB_SSL_VERIFY_IDENTITY") or os.getenv("MYSQL_SSL_VERIFY_IDENTITY")

        if ssl_ca_content and not ssl_ca:
            ssl_ca_path = os.getenv("DB_SSL_CA_PATH", "/tmp/tidb-ca.pem")
            try:
                with open(ssl_ca_path, "w", encoding="utf-8") as ca_file:
                    ca_file.write(ssl_ca_content)
                ssl_ca = ssl_ca_path
            except OSError:
                pass

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
    QRIS_API_URL = os.getenv("QRIS_API_URL", "")
    QRIS_API_KEY = os.getenv("QRIS_API_KEY", "")