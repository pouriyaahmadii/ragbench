# Data Directory

This directory contains sample documents and expected outputs for testing and demonstration.

## Structure

```
data/
├── samples/          # Fixture documents for ingestion testing
│   ├── policy.pdf    # Synthetic policy document
│   ├── access.txt    # Synthetic access control document
│   └── guide.md      # Synthetic Markdown guide
├── expected/         # Expected outputs for testing
│   ├── policy_chunks.json
│   └── access_chunks.json
└── README.md         # This file
```

## Fixture Documents

All fixture documents are **synthetic** or **openly licensed** (CC0, MIT, or created for RAGBench). No private, proprietary, or copyrighted documents are committed.

| Document | Format | Purpose | License |
|----------|--------|---------|---------|
| `policy.pdf` | PDF | Retention policy, multi-page | CC0 (synthetic) |
| `access.txt` | TXT | Access control rules | CC0 (synthetic) |
| `guide.md` | Markdown | Technical guide with headings | CC0 (synthetic) |

## Usage

These fixtures are used by:
- Unit tests (parsing, chunking)
- Integration tests (full ingestion pipeline)
- E2E tests (Playwright demo flow)
- Evaluation datasets (ground truth references)

## Adding Fixtures

1. Ensure document is synthetic or openly licensed
2. Add to `samples/` with descriptive name
3. Document license/provenance in this README
4. Create expected outputs in `expected/` if needed for tests
5. Update evaluation dataset references if used for ground truth

## License

All fixtures in this directory are released under **CC0 (Public Domain)** unless otherwise noted.