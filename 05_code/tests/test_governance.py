import unittest

from myis_research.governance import (
    AuthorizationError,
    ExecutionAuthorization,
    assert_research_execution_enabled,
)


class GovernanceTests(unittest.TestCase):
    def test_owner_approval_is_required(self) -> None:
        auth = ExecutionAuthorization(None, "C", "dev")
        with self.assertRaises(AuthorizationError):
            auth.validate()

    def test_held_out_requires_separate_gate(self) -> None:
        auth = ExecutionAuthorization("owner gate", "C", "confirmatory", True)
        with self.assertRaises(AuthorizationError):
            auth.validate()

    def test_restructure_mode_fails_closed(self) -> None:
        with self.assertRaises(AuthorizationError):
            assert_research_execution_enabled(False)


if __name__ == "__main__":
    unittest.main()

