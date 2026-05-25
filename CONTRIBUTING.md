# Contributing

Thanks for helping improve Q-VOID OS.

## Ground Rules

- Do not overclaim capabilities.
- Label new modules as `real`, `simulated`, or `experimental`.
- Add tests for success and failure paths.
- Keep demos runnable on a normal developer machine.
- Prefer clear code over theatrical complexity.

## Development

```bash
pip install -r requirements.txt
pytest
```

## Pull Request Checklist

- [ ] Tests pass.
- [ ] New behavior has negative-path tests.
- [ ] Module truth metadata is updated.
- [ ] Docs are updated when user-facing behavior changes.
- [ ] Security-sensitive code avoids silent failures.
