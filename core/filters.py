"""Structural filters for candidate eligibility and fit."""

from dataclasses import dataclass
from typing import Dict, List, Tuple

IT_SERVICES_FIRMS = {
    'tcs', 'infosys', 'wipro', 'accenture', 'cognizant',
    'hcl', 'mindtree', 'tech mahindra', 'deloitte', 'ibm',
    'capgemini', 'genpact', 'mphasis', 'kforce'
}


@dataclass
class CareerTimeline:
    total_years: float
    career_history: List[Dict]
    spans_valid: bool
    years_in_product: float
    years_in_ml_ai: float
    red_flags: List[str]


def extract_company_type(company_name: str) -> str:
    company_lower = company_name.lower()

    if any(firm in company_lower for firm in IT_SERVICES_FIRMS):
        return 'it_services'

    industry_keywords = {
        'ai/ml': ['ml', 'ai', 'machine learning', 'deep learning'],
        'data': ['data', 'analytics', 'big data'],
        'fintech': ['fintech', 'banking', 'finance', 'razorpay', 'cred'],
        'saas': ['saas', 'software'],
        'ecommerce': ['amazon', 'flipkart', 'zomato', 'swiggy'],
        'manufacturing': ['manufacturing', 'stark', 'dunder mifflin'],
    }

    for category, keywords in industry_keywords.items():
        if any(kw in company_lower for kw in keywords):
            return category

    return 'other'


def validate_career_timeline(profile: Dict) -> CareerTimeline:
    years_reported = profile.get('years_of_experience', 0)
    career_history = profile.get('career_history', [])

    red_flags = []
    total_duration_months = 0
    years_in_product = 0
    years_in_ml_ai = 0

    if not career_history:
        red_flags.append('No career history provided')
        return CareerTimeline(
            total_years=years_reported,
            career_history=career_history,
            spans_valid=False,
            years_in_product=0,
            years_in_ml_ai=0,
            red_flags=red_flags,
        )

    for job in career_history:
        duration = job.get('duration_months', 0)
        total_duration_months += duration

        company_type = extract_company_type(job.get('company', ''))
        if company_type != 'it_services':
            years_in_product += duration / 12

        title_lower = job.get('title', '').lower()
        if any(term in title_lower for term in [
            'ml', 'ai', 'data', 'engineer', 'scientist', 'ranking', 'search'
        ]):
            years_in_ml_ai += duration / 12

    total_years_calculated = total_duration_months / 12
    tolerance = 1.0

    if abs(total_years_calculated - years_reported) > tolerance:
        red_flags.append(
            f"Career timeline mismatch: reported {years_reported} yrs, "
            f"history sums to {total_years_calculated:.1f} yrs"
        )

    if years_in_product == 0:
        red_flags.append('Entire career in IT services/consulting')

    spans_valid = len(red_flags) == 0

    return CareerTimeline(
        total_years=years_reported,
        career_history=career_history,
        spans_valid=spans_valid,
        years_in_product=years_in_product,
        years_in_ml_ai=years_in_ml_ai,
        red_flags=red_flags,
    )


def is_pure_researcher(profile: Dict) -> bool:
    career_history = profile.get('career_history', [])
    academic_keywords = ['university', 'lab', 'research', 'phd', 'postdoc']

    for job in career_history:
        company_lower = job.get('company', '').lower()
        if not any(kw in company_lower for kw in academic_keywords):
            return False

    return len(career_history) > 0


def get_ai_core_skills(skills: List[Dict]) -> Tuple[List[str], int]:
    ai_keywords = {
        'llm', 'nlp', 'ml', 'ai', 'deep learning', 'neural', 'transformer',
        'embeddings', 'vector search', 'rag', 'langchain', 'pinecone', 'faiss',
        'machine learning', 'recommendation', 'ranking', 'classification',
        'object detection', 'yolo', 'cnn', 'gans', 'reinforcement learning',
        'tensorflow', 'pytorch', 'keras', 'bert', 'gpt', 'opt', 'dolly',
        'openai', 'bert', 'clip', 'roberta', 'xgboost', 'lightgbm'
    }

    ai_skills = []
    valid_duration_count = 0

    for skill in skills:
        name_lower = skill.get('name', '').lower()
        if any(kw in name_lower for kw in ai_keywords):
            ai_skills.append(skill.get('name'))
            duration = skill.get('duration_months', 0)
            proficiency = skill.get('proficiency', '').lower()

            if duration > 0 and proficiency != 'expert':
                valid_duration_count += 1
            elif duration > 12 and proficiency == 'expert':
                valid_duration_count += 1

    return ai_skills, valid_duration_count
