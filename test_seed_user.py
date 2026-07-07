import importlib
import os
import unittest


class SeedDefaultUserTest(unittest.TestCase):
    def setUp(self):
        self.env_backup = os.environ.get("DATABASE_URL")
        os.environ["DATABASE_URL"] = "sqlite:///:memory:"

    def tearDown(self):
        if self.env_backup is None:
            os.environ.pop("DATABASE_URL", None)
        else:
            os.environ["DATABASE_URL"] = self.env_backup

    def test_seed_default_owner_user(self):
        import app as app_module
        app_module = importlib.reload(app_module)

        with app_module.app.app_context():
            from models.user import User

            user = User.query.filter_by(username="owner").first()
            self.assertIsNotNone(user)
            self.assertEqual(user.role, "Owner")


if __name__ == "__main__":
    unittest.main()
