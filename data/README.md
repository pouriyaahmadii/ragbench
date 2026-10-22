# Data — Sample Documents and Expected Outputs

This directory contains fixture documents for testing and demonstration, plus expected outputs for validation.

## Structure

```
data/
├── samples/                  # Fixture documents (openly licensed / synthetic)
│   ├── policy.pdf            # Synthetic retention policy document
│   ├── access.txt            # Synthetic access control rules
│   └── guide.md              # Synthetic technical guide with headings
├── expected/                 # Expected outputs for test validation
│   ├── policy_chunks.json    # Expected chunking output for policy.pdf
│   ├── access_chunks.json    # Expected chunking output for access.txt
│   └── guide_chunks.json     # Expected chunking output for guide.md
└── README.md                 # This file
```

## Fixture Documents

All fixture documents are **synthetic** (authored for RAGBench) or **openly licensed** (CC0, MIT, etc.). No private, proprietary, or copyrighted documents are committed.

| Document | Format | Purpose | License |
|----------|--------|---------|---------|
| `policy.pdf` | PDF | Retention policy, multi-page | CC0 (synthetic) |
| `access.txt` | TXT | Access control rules | CC0 (synthetic) |
| `guide.md` | Markdown | Technical guide with headings | CC0 (synthetic) |

## Expected Outputs

The `expected/` directory contains pre-computed expected outputs for unit/integration test validation:

- **Chunking outputs:** Expected chunk boundaries, metadata, hashes for each fixture
- Used by tests to verify deterministic chunking behavior

## Usage

These fixtures are used by:
- Unit tests (parsing, chunking validation)
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