import pytest

from core.scoring import CandidateRanker


def test_score_candidate_ml_engineer():
    ranker = CandidateRanker()

    profile = {
        'candidate_id': 'CAND_0000001',
        'profile': {
            'current_title': 'Machine Learning Engineer',
            'years_of_experience': 6.5,
            'location': 'Pune',
        },
        'career_history': [
            {'company': 'Google', 'title': 'ML Engineer', 'duration_months': 36},
            {'company': 'Swiggy', 'title': 'Data Scientist', 'duration_months': 42},
        ],
        'skills': [
            {'name': 'Python', 'duration_months': 72, 'proficiency': 'advanced', 'endorsements': 20},
            {'name': 'Machine Learning', 'duration_months': 48, 'proficiency': 'advanced', 'endorsements': 15},
            {'name': 'TensorFlow', 'duration_months': 36, 'proficiency': 'advanced', 'endorsements': 10},
            {'name': 'NLP', 'duration_months': 24, 'proficiency': 'intermediate', 'endorsements': 8},
        ],
        'redrob_signals': {
            'recruiter_response_rate': 0.8,
            'interview_completion_rate': 0.75,
            'profile_completeness_score': 85,
            'offer_acceptance_rate': 0.6,
            'notice_period_days': 30,
            'willing_to_relocate': True,
        },
    }

    score = ranker.score_candidate(profile)
    assert score.final_score > 0.7
    assert score.reasoning is not None
    assert len(score.components) == 5


def test_score_candidate_it_services():
    ranker = CandidateRanker()

    profile = {
        'candidate_id': 'CAND_0000002',
        'profile': {
            'current_title': 'Software Engineer',
            'years_of_experience': 5.0,
            'location': 'Bangalore',
        },
        'career_history': [
            {'company': 'TCS', 'title': 'Software Engineer', 'duration_months': 30},
            {'company': 'Infosys', 'title': 'Senior Software Engineer', 'duration_months': 30},
        ],
        'skills': [
            {'name': 'Java', 'duration_months': 60, 'proficiency': 'advanced', 'endorsements': 10},
            {'name': 'C++', 'duration_months': 60, 'proficiency': 'advanced', 'endorsements': 5},
        ],
        'redrob_signals': {
            'recruiter_response_rate': 0.3,
            'interview_completion_rate': 0.4,
            'profile_completeness_score': 50,
            'offer_acceptance_rate': -1,
            'notice_period_days': 90,
            'willing_to_relocate': False,
        },
    }

    score = ranker.score_candidate(profile)
    assert score.final_score < 0.6


def test_score_components_weights():
    ranker = CandidateRanker()

    profile = {
        'candidate_id': 'CAND_TEST',
        'profile': {
            'current_title': 'ML Engineer',
            'years_of_experience': 7.0,
            'location': 'Pune',
        },
        'career_history': [
            {'company': 'Google', 'title': 'ML Engineer', 'duration_months': 84},
        ],
        'skills': [
            {'name': 'ML', 'duration_months': 60, 'proficiency': 'advanced', 'endorsements': 10},
        ],
        'redrob_signals': {
            'recruiter_response_rate': 0.5,
            'interview_completion_rate': 0.5,
            'profile_completeness_score': 50,
            'notice_period_days': 60,
            'willing_to_relocate': False,
        },
    }

    score = ranker.score_candidate(profile)
    total_weight = sum(c.weight for c in score.components)
    assert total_weight > 0
    weighted_sum = sum(c.value * c.weight for c in score.components)
    expected_score = weighted_sum / total_weight
    assert abs(score.final_score - expected_score) < 0.001
