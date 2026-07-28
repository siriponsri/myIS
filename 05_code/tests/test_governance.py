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

    def test_active_owner_gate_actions_are_typed(self) -> None:
        ExecutionAuthorization("owner gate", "S", "preflight", gate_id="G4", action="authorize_track_s").validate()
        ExecutionAuthorization("owner gate", "S", "freeze", gate_id="G5", action="freeze_track_s").validate()
        ExecutionAuthorization("owner gate", "C", "confirmation", gate_id="G6", action="authorize_joint_confirmation").validate()
        ExecutionAuthorization("owner gate", "C", "transfer", gate_id="G7", action="authorize_transfer").validate()
        ExecutionAuthorization("owner gate", "C", "publication", gate_id="G8", action="authorize_publication").validate()
        with self.assertRaises(AuthorizationError):
            ExecutionAuthorization("owner gate", "C", "legacy", gate_id="G4", action="authorize_track_r").validate()
        with self.assertRaises(AuthorizationError):
            ExecutionAuthorization("owner gate", "R", "legacy").validate()


if __name__ == "__main__":
    unittest.main()
