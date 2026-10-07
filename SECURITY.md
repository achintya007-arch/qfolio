# Security

- This project never needs secrets in the repository or in CI. IBM Quantum credentials are stored locally via
  `QiskitRuntimeService.save_account()` (`~/.qiskit/qiskit-ibm.json`).
- `detect-secrets` runs in pre-commit and CI.
- If you find a committed credential, please open an issue **without** pasting the secret, or contact the author
  via GitHub. The credential will be revoked immediately.
