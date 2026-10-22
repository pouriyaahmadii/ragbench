# License Decision Note

**Status:** Unresolved — to be finalized before Phase 23 (README/Licensing/Portfolio Packaging)

## Options Under Consideration

| License | SPDX ID | Pros | Cons |
|---------|---------|------|------|
| **MIT** | `MIT` | Simple, permissive, widely recognized, GPL-compatible | No explicit patent grant |
| **Apache-2.0** | `Apache-2.0` | Explicit patent grant, clear contribution terms, widely used | Slightly longer text |
| **BSD-3-Clause** | `BSD-3-Clause` | Permissive, no endorsement clause, simple | No patent grant |

## Decision Criteria

1. **Portfolio Use:** License should not hinder portfolio presentation or hiring manager review
2. **Community Norms:** Align with common practices for portfolio/educational projects
3. **Contributor Friendly:** Clear terms for any future contributors
4. **Dependency Compatibility:** Must be compatible with all transitive dependencies (MIT, Apache-2.0, BSD, ISC)
5. **No Viral Licenses:** GPL/AGPL/LGPL not acceptable for this codebase

## Current Leaning

**MIT License** — simplest, most recognized for portfolio projects, compatible with all dependencies.

## Next Steps

1. Finalize decision before Phase 23
2. Create `LICENSE` file with chosen license text
3. Generate `THIRD_PARTY_LICENSES.md` from lockfiles
4. Add license headers to source files (optional but recommended)
4. Update `README.md` with license badge

## Third-Party License Compliance

Regardless of project license, all transitive dependencies must be:
- Inventoried at release (`pip-licenses`, `npm ls --all --json`)
- Compatible (no GPL/AGPL in runtime dependencies)
- Attributed in `THIRD_PARTY_LICENSES.md`

---

**Decision Record:** To be updated when finalized.