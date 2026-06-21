# RepoLens Sample Projects

Complex test repositories for validating all analyzers.

| Sample | Language | Upload file |
|--------|----------|-------------|
| Python | `.py` | `python-sample.zip` |
| JavaScript | `.js` | `js-sample.zip` |
| TypeScript | `.ts` / `.tsx` | `typescript-sample.zip` |

## Intentional issues in each sample

- **Large file** — `data/catalog_*` module (>500 lines)
- **Large function** — `process_orders` / `processOrders` (>50 lines)
- **Complexity** — nested branching (Python only, via Radon)
- **Security** — hardcoded API keys, passwords, secrets, `eval()`, `innerHTML`
- **Architecture** — circular import/require chains between services

## Regenerate

```bash
python scripts/build_sample_projects.py
```

## Test via API

```powershell
curl -X POST -F "file=@samples/python-sample.zip" http://127.0.0.1:8080/api/analyze
```

Expected: multiple findings across maintainability, security, and architecture categories.
