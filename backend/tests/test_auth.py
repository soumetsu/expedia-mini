"""Tests for demo account credentials and per-user search history."""

from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from pydantic import ValidationError

from app.controllers.database import (
    AccountConflictError,
    authenticate_user,
    create_user_account,
    initialize_database,
    list_search_history,
    record_search,
)
from app.models import RegisterRequest


class AuthenticationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = TemporaryDirectory()
        self.database_path = Path(self.temporary_directory.name) / "test.db"
        initialize_database(self.database_path)

    def tearDown(self) -> None:
        self.temporary_directory.cleanup()

    def test_account_password_is_hashed_and_login_verifies_it(self) -> None:
        account = create_user_account(
            "traveler_one", "correct horse battery", "madeup@example.test", self.database_path
        )

        self.assertEqual(account.username, "traveler_one")
        self.assertEqual(
            authenticate_user("TRAVELER_ONE", "correct horse battery", self.database_path).user_id,
            account.user_id,
        )
        with self.assertRaisesRegex(LookupError, "incorrect"):
            authenticate_user("traveler_one", "wrong password", self.database_path)

    def test_username_and_email_are_unique(self) -> None:
        create_user_account("traveler_one", "correct horse battery", "same@example.test", self.database_path)
        with self.assertRaisesRegex(AccountConflictError, "username"):
            create_user_account("TRAVELER_ONE", "another password", None, self.database_path)
        with self.assertRaisesRegex(AccountConflictError, "email"):
            create_user_account("traveler_two", "another password", "SAME@example.test", self.database_path)

    def test_email_contract_rejects_malformed_values_but_allows_made_up_domain(self) -> None:
        self.assertEqual(
            RegisterRequest(username="traveler_one", password="correct horse", email="a@madeup.test").email,
            "a@madeup.test",
        )
        with self.assertRaises(ValidationError):
            RegisterRequest(username="traveler_one", password="correct horse", email="#@!(*&*!(@#&@gmail.coma")

    def test_search_history_is_isolated_between_users(self) -> None:
        first = create_user_account("traveler_one", "correct horse battery", None, self.database_path)
        second = create_user_account("traveler_two", "correct horse battery", None, self.database_path)
        record_search(first.user_id, "Boston", None, None, 4, self.database_path)
        record_search(second.user_id, "New York", None, None, 3, self.database_path)

        self.assertEqual([item.query for item in list_search_history(first.user_id, database_path=self.database_path)], ["Boston"])
        self.assertEqual([item.query for item in list_search_history(second.user_id, database_path=self.database_path)], ["New York"])


if __name__ == "__main__":
    unittest.main()
