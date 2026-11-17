# Legal AI evidence audit

A small Python demonstration of citation applicability and the treatment of missing facts. It uses fictional review rules and manually written examples.

## Run

Python 3.10 or later is sufficient.

```sh
python evidence_audit.py
python evidence_audit.py --json
```

The fixture includes deliberately flawed answers. The default run reports four passing examples out of nine. The JSON report gives the possible outcomes, decisive missing facts, and any branch that the cited provisions fail to cover.

## How the audit works

Each source clause has an identifier, its text, the conditions under which it applies, and its outcome. Each answer supplies an outcome, cited clause identifiers, and the facts it says are missing.

The program evaluates every true-or-false completion of the unknown facts. It flags a fact as decisive when changing that fact alone can change the result. It also checks that every possible completion is covered by a cited provision and flags unknown or inapplicable citations.

- A correct eligibility answer citing the timely-filing rule fails its citation check when the late-filing exception actually controls.
- An answer about a late filing needs both branches when the record is silent about whether notice was given.
- The same missing notice fact leaves a timely filing eligible, so it does not need to be flagged.

The examples use structured answers and hand-encoded rules. The auditor tests those inputs directly. Applying the method to real legal text would require source versioning, human review of the rule encoding, and validation of the extracted claims.
