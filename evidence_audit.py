"""Audit structured model answers against a miniature set of synthetic legal rules."""

import argparse
from collections import Counter
from itertools import product
import json
from pathlib import Path


def assess(example, rules):
    """Check the outcome, the cited support, and the handling of missing facts."""
    facts = example["facts"]
    answer = example["answer"]
    unknowns = tuple(name for name, value in facts.items() if value is None)
    outcomes = {}
    applicable_citations = {}

    for values in product((False, True), repeat=len(unknowns)):
        completed_facts = facts | dict(zip(unknowns, values))
        applicable = [
            rule
            for rule in rules
            if all(completed_facts[name] == value for name, value in rule["when"].items())
        ]
        possible = {rule["outcome"] for rule in applicable}
        if len(possible) != 1:
            raise ValueError(
                f"{example['id']}: fixture rules must give one outcome for "
                f"{completed_facts}, got {sorted(possible)}"
            )
        outcomes[values] = possible.pop()
        applicable_citations[values] = {rule["id"] for rule in applicable}

    possible_outcomes = sorted(set(outcomes.values()))
    expected = possible_outcomes[0] if len(possible_outcomes) == 1 else "undetermined"
    decisive = {
        fact
        for index, fact in enumerate(unknowns)
        if any(
            outcomes[values] != outcomes[values[:index] + (True,) + values[index + 1:]]
            for values in outcomes
            if not values[index]
        )
    }
    cited = set(answer["citations"])
    named_facts = set(answer["missing_facts"])
    known_citations = {rule["id"] for rule in rules}
    relevant_citations = set().union(*applicable_citations.values())
    issues = {}

    if answer["outcome"] != expected:
        issues["incorrect_outcome"] = {"reported": answer["outcome"], "expected": expected}
    if cited - known_citations:
        issues["unknown_citation"] = sorted(cited - known_citations)
    if (cited & known_citations) - relevant_citations:
        issues["inapplicable_citation"] = sorted((cited & known_citations) - relevant_citations)
    if decisive - named_facts:
        issues["unreported_decisive_fact"] = sorted(decisive - named_facts)
    if named_facts - decisive:
        issues["irrelevant_uncertainty"] = sorted(named_facts - decisive)

    uncovered = [
        {"missing_facts_assignment": dict(zip(unknowns, values)), "outcome": outcomes[values]}
        for values, allowed in applicable_citations.items()
        if not cited.intersection(allowed)
    ]
    if uncovered:
        issues["incomplete_citation_support"] = uncovered

    return {
        "id": example["id"],
        "expected_outcome": expected,
        "possible_outcomes": possible_outcomes,
        "decisive_missing_facts": sorted(decisive),
        "issues": issues,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "input",
        type=Path,
        nargs="?",
        default=Path(__file__).with_name("synthetic_cases.json"),
        help="JSON file of synthetic rules and structured answers",
    )
    parser.add_argument("--json", action="store_true", help="Print the full audit as JSON")
    args = parser.parse_args()

    data = json.loads(args.input.read_text(encoding="utf-8"))
    results = [assess(example, data["rules"]) for example in data["examples"]]
    issue_counts = Counter(issue for item in results for issue in item["issues"])
    passing = sum(not item["issues"] for item in results)

    if args.json:
        print(json.dumps({
            "total_examples": len(results),
            "passing_examples": passing,
            "issue_counts": dict(sorted(issue_counts.items())),
            "examples": results,
        }, indent=2))
        return

    for item in results:
        issues = ", ".join(item["issues"]) or "passed"
        print(f"{item['id']:33} {item['expected_outcome']:19} {issues}")
    print(f"\n{passing}/{len(results)} examples passed.")


if __name__ == "__main__":
    main()
