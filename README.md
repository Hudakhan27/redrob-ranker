# Redrob Candidate Ranking System

A CPU-only ranking engine for the Redrob hackathon challenge. The system ranks candidates using structural filters, honeypot detection, title prioritization, behavioral signals, and availability.

## Project Structure

- `rank.py` - Main ranking entry point
- `validate_submission.py` - CSV validator for final output
- `core/filters.py` - Structural filtering logic
- `core/honeypot_detector.py` - Honeypot detection and timeline validation
- `core/scoring.py` - Scoring engine with fact-driven reasoning
- `tests/` - Unit tests for filtering, honeypot detection, and scoring
- `requirements.txt` - Python dependencies

## Usage

Install dependencies:

```bash
pip install -r requirements.txt
```

Run ranking:

```bash
python rank.py --candidates sample_candidates.json --out submission.csv
```

Validate output:

```bash
python validate_submission.py submission.csv
```

## Notes

- Output CSV is UTF-8 encoded
- Output contains exactly 100 ranked candidates
- Scores are monotonic non-increasing
- Ties are broken alphabetically by `candidate_id`
