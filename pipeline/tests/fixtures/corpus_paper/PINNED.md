# Pinned test fixtures

These files are deterministic test fixtures for schema and corpus validation (SPEC 10.5).

- **Do not change** without updating the checksum and migration notes.
- Checksum: see `.checksum` in this directory (SHA-256 of canonical JSON concatenation).

To regenerate the checksum after an intentional change:

```bash
uv run --project pipeline python -c "
from pathlib import Path
import hashlib, json
d = Path('pipeline/tests/fixtures/corpus_paper')
files = sorted(d.glob('*.json'))
h = hashlib.sha256()
for f in files:
    h.update(json.dumps(json.loads(f.read_text()), sort_keys=True).encode())
print(h.hexdigest())
"
```
