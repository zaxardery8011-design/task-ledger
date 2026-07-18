# Engine coupling (required disclosure)

1. **Production origin** used an external **CLI agent worker** (CLI agent family) as the default long-job engine.
2. **Core library is engine-agnostic** at the `EnginePort` boundary.
3. Optional CLI adapters are **samples**, not hard dependencies of the package.
4. **Selftests** run with **scripted / fake** engines only — no network, no API keys.
5. **Chat networks** are one possible `NotifyPort` implementation — **not** bundled as required runtime.
6. **External CLI adapter sample:** docs-only first (`EXTERNAL_CLI_ADAPTER.md`). No in-tree sample until a concrete need + packaging decision.

Missing this disclosure fails sanitization review.

## PowerShell

PowerShell modules under `adapters/powershell/` are **optional host adapters**.
The pip-installable default surface is pure Python. Production-specific orchestration remains behind adapter boundaries and is not bundled. Selftests do **not** require host orchestration parity.
