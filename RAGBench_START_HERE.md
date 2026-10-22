# RAGBench Prompt Pack — Start Here

## Files in this pack

- `RAGBench_Product_SPEC.md`: product and technical requirements baseline, architecture, API contract, data model, ingestion, chunking, retrieval, evaluation, metrics, security, testing, and acceptance gates.
- `RAGBench_Antigravity_Roadmap.md`: full sequence of Antigravity prompts, from Prompt 00 through Prompt 25, including phase-level acceptance criteria and safe remediation guidance.
- `RAGBench_Evaluation_Sample.json`: a small synthetic example of an evaluation dataset format. IDs are illustrative; do not treat them as actual indexed document/chunk IDs until matching fixture documents and indexing have been built.

## Execution order

1. Create/open an empty `ragbench` folder as the Antigravity workspace.
2. Read the product spec and prompt-pack introduction.
3. Run Prompt 00.
4. Run prompts one at a time in numeric order. Inspect the report and actual test outputs after every phase.
5. Do not move forward if a foundational phase fails. Use Prompt 25 to diagnose and repair a concrete defect.
6. Start with deterministic Mock mode. Add a local model or paid provider only after the end-to-end Mock path and its tests pass.
7. Never publish secrets, private documents, database files, vector-store volumes, model weights, or invented metrics.

## Source of truth

The Product SPEC defines required product behavior. The prompt pack defines the recommended implementation sequence. If an architectural decision must change, require Antigravity to create/update an ADR, update the relevant SPEC sections, and add or update tests before continuing.

## Release rule

The repo is ready for portfolio demonstration only when the MVP acceptance gates in the SPEC have been checked against actual implementation and test evidence. A green build is necessary but does not prove RAG quality or production security.
