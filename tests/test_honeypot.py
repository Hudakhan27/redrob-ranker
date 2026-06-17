import pytest

from core.honeypot_detector import (
    cross_reference_skill_timelines,
    detect_keyword_stuffing,
)


def test_skill_duration_impossible():
    profile = {
        'career_history': [
            {'company': 'A', 'duration_months': 24},
        ],
        'skills': [
            {
                'name': 'Machine Learning',
                'duration_months': 100,
                'proficiency': 'expert',
                'endorsements': 50,
            },
        ],
    }

    score = cross_reference_skill_timelines(profile)
    assert score.is_suspected_honeypot
    assert any('impossible' in flag.lower() for flag in score.red_flags)


def test_expert_with_minimal_exposure():
    profile = {
        'career_history': [
            {'company': 'A', 'duration_months': 36},
        ],
        'skills': [
            {
                'name': 'NLP',
                'duration_months': 3,
                'proficiency': 'expert',
                'endorsements': 100,
            },
        ],
    }

    score = cross_reference_skill_timelines(profile)
    assert score.is_suspected_honeypot
    assert any('expert' in flag.lower() for flag in score.red_flags)


def test_keyword_stuffing_technical_title():
    profile = {
        'profile': {'current_title': 'ML Engineer'},
        'skills': [
            {'name': 'NLP', 'duration_months': 12, 'proficiency': 'advanced', 'endorsements': 5},
            {'name': 'Machine Learning', 'duration_months': 12, 'proficiency': 'advanced', 'endorsements': 5},
            {'name': 'Deep Learning', 'duration_months': 12, 'proficiency': 'advanced', 'endorsements': 5},
            {'name': 'LLM', 'duration_months': 12, 'proficiency': 'advanced', 'endorsements': 5},
        ],
        'career_history': [
            {'company': 'Google', 'duration_months': 48},
        ],
    }

    score = detect_keyword_stuffing(profile)
    assert score.confidence < 0.5


def test_keyword_stuffing_non_technical_title():
    profile = {
        'profile': {'current_title': 'Accountant'},
        'skills': [
            {'name': 'NLP', 'duration_months': 12, 'proficiency': 'expert', 'endorsements': 50},
            {'name': 'Machine Learning', 'duration_months': 12, 'proficiency': 'expert', 'endorsements': 50},
            {'name': 'Deep Learning', 'duration_months': 12, 'proficiency': 'expert', 'endorsements': 50},
            {'name': 'LLM', 'duration_months': 12, 'proficiency': 'expert', 'endorsements': 50},
            {'name': 'Fine-tuning LLMs', 'duration_months': 12, 'proficiency': 'expert', 'endorsements': 50},
            {'name': 'RAG', 'duration_months': 12, 'proficiency': 'expert', 'endorsements': 50},
            {'name': 'Prompt Engineering', 'duration_months': 12, 'proficiency': 'expert', 'endorsements': 50},
            {'name': 'Embeddings', 'duration_months': 12, 'proficiency': 'expert', 'endorsements': 50},
        ],
        'career_history': [
            {'company': 'Accounting Firm', 'duration_months': 48},
        ],
    }

    score = detect_keyword_stuffing(profile)
    assert score.is_suspected_honeypot
    assert score.confidence > 0.5
