import pytest

from core.filters import (
    extract_company_type,
    get_ai_core_skills,
    is_pure_researcher,
    validate_career_timeline,
)


def test_extract_company_type():
    assert extract_company_type('Infosys') == 'it_services'
    assert extract_company_type('TCS') == 'it_services'
    assert extract_company_type('Google') == 'other'
    assert extract_company_type('Flipkart') == 'ecommerce'


def test_validate_career_timeline_valid():
    profile = {
        'years_of_experience': 6.0,
        'career_history': [
            {'company': 'Google', 'title': 'ML Engineer', 'duration_months': 36},
            {'company': 'Swiggy', 'title': 'Data Scientist', 'duration_months': 36},
        ],
    }

    timeline = validate_career_timeline(profile)
    assert timeline.spans_valid
    assert len(timeline.red_flags) == 0
    assert timeline.total_years == 6.0


def test_validate_career_timeline_mismatch():
    profile = {
        'years_of_experience': 10.0,
        'career_history': [
            {'company': 'Company A', 'title': 'Engineer', 'duration_months': 24},
        ],
    }

    timeline = validate_career_timeline(profile)
    assert not timeline.spans_valid
    assert any('mismatch' in flag.lower() for flag in timeline.red_flags)


def test_is_pure_researcher():
    academic_profile = {
        'career_history': [
            {'company': 'MIT Lab', 'title': 'Researcher'},
            {'company': 'Stanford University', 'title': 'Postdoc'},
        ],
    }
    assert is_pure_researcher(academic_profile)

    mixed_profile = {
        'career_history': [
            {'company': 'MIT Lab', 'title': 'Researcher'},
            {'company': 'Google', 'title': 'Engineer'},
        ],
    }
    assert not is_pure_researcher(mixed_profile)


def test_get_ai_core_skills():
    skills = [
        {'name': 'Python', 'duration_months': 24, 'proficiency': 'advanced'},
        {'name': 'Machine Learning', 'duration_months': 12, 'proficiency': 'intermediate'},
        {'name': 'NLP', 'duration_months': 6, 'proficiency': 'expert'},
        {'name': 'TensorFlow', 'duration_months': 18, 'proficiency': 'advanced'},
    ]

    ai_skills, valid_count = get_ai_core_skills(skills)
    assert len(ai_skills) == 3
    assert valid_count >= 2
