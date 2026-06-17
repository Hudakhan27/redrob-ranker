#!/usr/bin/env python3
"""
Main ranking engine: CPU-only, offline, < 5 minutes for 50K candidates.
Outputs: submission.csv with 100 ranked candidates.
"""

import csv
import json
import sys
from typing import Dict, List

from core.filters import validate_career_timeline, is_pure_researcher
from core.honeypot_detector import (
    cross_reference_skill_timelines,
    detect_keyword_stuffing,
)
from core.scoring import CandidateRanker, CandidateScore


def load_candidates(candidates_file: str) -> List[Dict]:
    """Load candidate profiles from JSON or JSONL."""
    candidates = []

    with open(candidates_file, 'r', encoding='utf-8') as f:
        if candidates_file.endswith('.jsonl'):
            for line in f:
                if line.strip():
                    candidates.append(json.loads(line))
        else:
            candidates = json.load(f)

    return candidates


def rank_candidates(
    candidates: List[Dict],
    output_file: str = 'submission.csv',
    top_n: int = 100,
) -> None:
    """
    Rank candidates and output CSV.

    Args:
        candidates: List of candidate profiles
        output_file: Output CSV path
        top_n: Number of top candidates to output (typically 100)
    """
    ranker = CandidateRanker()
    scores: List[CandidateScore] = []

    print(f"[*] Scoring {len(candidates)} candidates...")

    for i, profile in enumerate(candidates):
        if (i + 1) % 10000 == 0:
            print(f"    Progress: {i + 1}/{len(candidates)}")

        if is_pure_researcher(profile):
            continue

        score = ranker.score_candidate(profile)
        scores.append(score)

    print(f"[*] Ranked {len(scores)} eligible candidates")

    scores.sort(key=lambda s: (-s.final_score, s.candidate_id))

    for rank, score in enumerate(scores[:top_n], start=1):
        score.rank = rank

    top_scores = scores[:top_n]

    print(f"[*] Writing {len(top_scores)} candidates to {output_file}")

    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['candidate_id', 'rank', 'score', 'reasoning'])

        for score in top_scores:
            writer.writerow([
                score.candidate_id,
                score.rank,
                f"{score.final_score:.4f}",
                score.reasoning,
            ])

    print(f"[✓] Submission complete: {output_file}")
    validate_output(output_file)


def validate_output(csv_file: str) -> None:
    """Quick validation of output CSV."""
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    assert len(rows) == 100, f"Expected 100 rows, got {len(rows)}"

    ranks = [int(row['rank']) for row in rows]
    assert ranks == list(range(1, 101)), "Ranks must be 1-100"

    scores = [float(row['score']) for row in rows]
    for i in range(len(scores) - 1):
        assert scores[i] >= scores[i + 1], \
            f"Score not monotonic: {scores[i]} < {scores[i + 1]}"

    print(f"[✓] Output validation passed")


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: python rank.py --candidates <file.json> --out <output.csv>")
        sys.exit(1)

    candidates_file = None
    output_file = 'submission.csv'

    for i, arg in enumerate(sys.argv[1:]):
        if arg == '--candidates' and i + 1 < len(sys.argv):
            candidates_file = sys.argv[i + 2]
        elif arg == '--out' and i + 1 < len(sys.argv):
            output_file = sys.argv[i + 2]

    if not candidates_file:
        print("Error: --candidates argument required")
        sys.exit(1)

    candidates = load_candidates(candidates_file)
    rank_candidates(candidates, output_file)


if __name__ == '__main__':
    main()
