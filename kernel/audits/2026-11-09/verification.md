<!-- SPDX-License-Identifier: Apache-2.0 -->
# Kernel audit verification: 2026-11-09

This record distinguishes source/documentation checks from kernel acceptance. See
[assessment](../kernel-assessment.md), [issue register](../kernel-issues.md) and
[roadmap](../kernel-modernization.md). Source baseline: kernel
792d36ef1a9169b3fc9084fcc494b209501a7487; documentation starting baseline:
6a6236c41d46481948b8080a362abb4b9f0e10bb; build baseline:
82be8e7a3a006bdf21325e374fa8b9b8299a12f0.

## Source and workspace checks

Commands were run from /Users/vachagan/WS/NeoSymbian unless an absolute path is given.

| Exact command/check | Exit | Result |
|---|---|---|
| git -C kernel rev-parse HEAD | 0 | Kernel baseline above |
| git -C docs rev-parse HEAD | 0 | Documentation starting baseline above |
| git -C build rev-parse HEAD | 0 | Build baseline above; branch legacy-gui |
| git -C kernel status --short --branch | 0 | Existing nine modified and five untracked paths at capture |
| git -C docs status --short --branch | 0 | Initially clean main |
| git -C build status --short --branch | 0 | Existing modified neo |
| git -C kernel grep -n -e RandomSalt -e AddTimingEntropy HEAD -- baseport/arm64 kernel/eka/nkernsmp/arm64 kernel/eka/kernel/arm64 | 1 | No committed collector call matches in those platform paths; not a full-system runtime entropy test |
| git -C kernel ls-tree --name-only HEAD .github | 0 | No tracked kernel workflow directory at this baseline |

The workspace-root git status returned 128 because the workspace root is not a repository. Subsequent checks
used its individual repositories. Concurrent remote-access.md work and its README navigation row appeared after
the initial capture; they are preserved and excluded from this audit's change ownership.

Inventory used git ls-tree -r --name-only HEAD per repository and suffix/path counts, recorded in
[/private/tmp/neosymbian-kernel-audit-baseline.json](/private/tmp/neosymbian-kernel-audit-baseline.json).
The baseline contains dirty-path lists and a kernel tracked-diff hash; it contains no private firmware or dumps.
The working-tree timer hook was read with
git -C kernel show HEAD:baseport/arm64/common/specific/a64_variant.cpp because concurrent edits shift its lines.
Published source citations use full commit permalinks.

The entropy search, workflow-directory check and exact source-consistency diff command/results are retained in
[/private/tmp/neosymbian-audit-evidence/source-checks.json](/private/tmp/neosymbian-audit-evidence/source-checks.json).
That source diff exited 0 with no output: the listed legacy/architecture/tool paths still matched HEAD.
Concurrent kernel edits continued after the initial capture, so the whole-tree dirty-diff hash changed while
the reviewed repository HEADs stayed the same. The later status is retained in
[/private/tmp/neosymbian-audit-evidence/workspace-status.json](/private/tmp/neosymbian-audit-evidence/workspace-status.json);
it must not be mistaken for this documentation task's source diff.

## Controlled runner failure probe

The actual run-qemu.sh was invoked with OUT in a temporary directory and PATH prefixed with a mock timeout
program. The mock printed a diagnostic and exited 42 without executing QEMU. The original script was unmodified.

| Exact invocation | Launcher exit | Runner exit | Interpretation |
|---|---|---|---|
| sh /Users/vachagan/WS/NeoSymbian/kernel/baseport/arm64/tools/run-qemu.sh 1 | 42 | 0 | Failure is masked when no expected marker is requested |
| sh /Users/vachagan/WS/NeoSymbian/kernel/baseport/arm64/tools/run-qemu.sh 1 REQUIRED_COMPLETION_MARKER | 42 | 1 | Missing marker is rejected |

Environment: PATH began with /private/tmp/neosymbian-audit-evidence/mock-bin; OUT was respectively
/private/tmp/neosymbian-audit-evidence/without-marker and
/private/tmp/neosymbian-audit-evidence/with-marker. The Python probe asserted runner exits [0, 1] and exited 0.
Raw commands, statuses and output:
[/private/tmp/neosymbian-audit-evidence/run-qemu-probe.json](/private/tmp/neosymbian-audit-evidence/run-qemu-probe.json).
The two OUT directories retain serial.log. This proves a test-harness behavior, not kernel behavior.

## Documentation verification

The checker and outputs are local research artifacts, not additions to the kernel or its toolchain.

| Exact command | Exit | Scope |
|---|---|---|
| python3 /private/tmp/neosymbian-audit-evidence/verify_kernel_docs.py | 0 | Seven documents, 76 pinned source citations across 46 files, 34 issue/phase mappings and 22 legacy test paths; local links/anchors and whitespace/fences checked |
| git -C docs diff --check | 0 | Tracked documentation diff whitespace; the checker also covers untracked new documents |
| git -C docs apply --check --reverse /private/tmp/neosymbian-audit-evidence/docs-change.patch | 0 | Final seven-path task patch matches the working files; read-only check, no patch applied |

An initial checker run exited 1: its link parser consumed closing punctuation and one source link exceeded its
file's last line. Both were corrected and the checker exited 0. These checks validate references and structure,
not the semantic correctness of every source conclusion. Raw final results are in
[/private/tmp/neosymbian-audit-evidence/documentation-checks.json](/private/tmp/neosymbian-audit-evidence/documentation-checks.json)
and [/private/tmp/neosymbian-audit-evidence/git-diff-check.json](/private/tmp/neosymbian-audit-evidence/git-diff-check.json).

Independent review used a fresh context with the user specification, baseline, incremental patch and raw
evidence. **Result: no actionable findings in the bounded documentation change.** The reviewer independently
traced representative inherited defects and port contracts, confirmed all issue/phase and historical-issue
mappings, and checked compatibility and proposed acceptance criteria. This is not exhaustive source or runtime
acceptance. Full report:
[/private/tmp/neosymbian-audit-evidence/independent-review.md](/private/tmp/neosymbian-audit-evidence/independent-review.md).

The final task patch is
[/private/tmp/neosymbian-audit-evidence/docs-change.patch](/private/tmp/neosymbian-audit-evidence/docs-change.patch).
It excludes the unrelated remote-access README row and contains the seven owned documentation paths only.
The final checks were repeated after integrating this review record. The audit is kept in the docs repository;
no kernel/build/application edits belong to this task.

## Acceptance not executed

No toolchain build, QEMU launch, Syborg boot, nkernsa, e32test, f32test, live-phone check, exploit, fuzz campaign,
hardware write, power-cut test, benchmark, remote connection or CI run was performed. Remote-host availability
was not checked. These are verification gaps, never passing checks. Roadmap test names and acceptance thresholds
are proposed future work. Historical phone/CI/performance claims in existing documents were not refreshed.

The work changes documentation only. Source fixes, authenticated boot, firmware support, personal-data safety
and a production-ready kernel remain unaccepted until their stated gates pass.
