"""exceptions.py — Custom exception hierarchy for gas-skill."""


class GasSkillError(Exception):
    """Base exception for all gas-skill errors."""
    pass


class ConfigError(GasSkillError):
    """Configuration file missing or invalid."""
    pass


class BranchProtectionError(GasSkillError):
    """Attempted forbidden operation on a protected branch."""
    pass


class DirtyTreeError(GasSkillError):
    """Working tree has uncommitted changes."""
    pass


class PrePushValidationError(GasSkillError):
    """Pre-push validation failed."""
    pass


class ClaspError(GasSkillError):
    """clasp command failed."""
    pass


class AuthenticationError(GasSkillError):
    """Authentication token missing or expired."""
    pass


class MergeConflictError(GasSkillError):
    """Git merge produced conflicts that need resolution."""
    def __init__(self, conflicting_files: list[str]):
        self.conflicting_files = conflicting_files
        super().__init__(
            f"Merge conflict in {len(conflicting_files)} file(s): "
            + ", ".join(conflicting_files)
        )


class ReleaseError(GasSkillError):
    """Release process failed (smoke test, tag, deploy)."""
    pass


class MaxRetriesError(GasSkillError):
    """Feedback loop exceeded maximum retry count."""
    pass
