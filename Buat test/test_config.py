import importlib
import os
import unittest


class ConfigEnvironmentTest(unittest.TestCase):
    def setUp(self):
        self.env_backup = {key: os.environ.get(key) for key in [
            "DATABASE_URL",
            "SQLALCHEMY_DATABASE_URI",
            "DB_HOST",
            "DB_PORT",
            "DB_USERNAME",
            "DB_PASSWORD",
            "DB_NAME",
            "DB_SSL_CA",
            "DB_SSL_VERIFY_CERT",
            "DB_SSL_VERIFY_IDENTITY",
        ]}

    def tearDown(self):
        for key, value in self.env_backup.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value

    def test_builds_tiDB_uri_from_environment(self):
        os.environ["DB_HOST"] = "gateway01.ap-southeast-1.prod.aws.tidbcloud.com"
        os.environ["DB_PORT"] = "4000"
        os.environ["DB_USERNAME"] = "root"
        os.environ["DB_PASSWORD"] = "secret"
        os.environ["DB_NAME"] = "smartwash"
        os.environ["DB_SSL_CA"] = "/tmp/ca.pem"
        os.environ["DB_SSL_VERIFY_CERT"] = "true"
        os.environ["DB_SSL_VERIFY_IDENTITY"] = "true"

        import config
        config_module = importlib.reload(config)

        self.assertIn("mysql+pymysql://root:secret@", config_module.Config.SQLALCHEMY_DATABASE_URI)
        self.assertIn("gateway01.ap-southeast-1.prod.aws.tidbcloud.com:4000/smartwash", config_module.Config.SQLALCHEMY_DATABASE_URI)
        self.assertIn("ssl_ca=%2Ftmp%2Fca.pem", config_module.Config.SQLALCHEMY_DATABASE_URI)
        self.assertIn("ssl_verify_cert=true", config_module.Config.SQLALCHEMY_DATABASE_URI)
        self.assertIn("ssl_verify_identity=true", config_module.Config.SQLALCHEMY_DATABASE_URI)


if __name__ == "__main__":
    unittest.main()
