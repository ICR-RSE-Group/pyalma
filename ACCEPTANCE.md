# ✅ Merge Request Acceptance Criteria

To ensure code quality and maintain reliability, all merge requests (MRs) must meet the following conditions **before they can be merged into `main`**:

---

## ✅ Unit Tests

- **All unit tests must pass** with no errors or failures.
- Tests are executed automatically via GitHub Actions during the CI process.
- Any failing unit test will block the merge.

---

## ✅ Code Coverage

- **Overall test coverage must be at least 80%.**
- Code coverage is measured using `coverage.py` during CI.
- A coverage drop below 80% will cause the CI pipeline to fail.

---

## ✅ Integration Tests (SSH)

- Integration tests must validate SSH connectivity and permissions using two user roles:
  - `testuser1`: has permission to execute commands/scripts over SSH.
  - `restricted`: is limited to **SFTP access only** (no shell or command execution).
- These tests confirm that:
  - SSH server starts and accepts connections.
  - Each user adheres to the expected permission model.
- Failures in integration tests will block the merge.

---

## ✅ Summary

| Requirement         | Status Required to Merge |
|---------------------|---------------------------|
| All Unit Tests Pass | ✅ Required               |
| Coverage ≥ 80%      | ✅ Required               |
| SSH IT Tests Pass   | ✅ Required               |

---

_Merge requests not meeting the above criteria will not be accepted until all issues are resolved._
