"""Compute candidate match scores with fact-driven reasoning."""

from dataclasses import dataclass
from typing import Dict, List, Tuple

from core.filters import validate_career_timeline


@dataclass
class ScoreComponent:
    name: str
    value: float
    reasoning: str
    weight: float = 1.0


@dataclass
class CandidateScore:
    candidate_id: str
    final_score: float
    rank: int
    reasoning: str
    components: List[ScoreComponent]


class CandidateRanker:
    WEIGHTS = {
        'title_match': 0.30,
        'experience': 0.25,
        'skills': 0.20,
        'behavioral': 0.15,
        'availability': 0.10,
    }

    TARGET_TITLES = {
        'ml engineer', 'ml', 'machine learning engineer',
        'data scientist', 'ai engineer', 'ranking engineer',
        'search engineer', 'recommendation engineer',
        'backend engineer', 'full stack engineer',
        'nlp engineer', 'cv engineer', 'computer vision',
        'applied ml', 'ai/ml', 'llm engineer',
    }

    def score_candidate(self, profile: Dict) -> CandidateScore:
        candidate_id = profile.get('candidate_id')
        components: List[ScoreComponent] = []

        title_score, title_reasoning = self._score_title_match(profile)
        components.append(ScoreComponent(
            name='title_match',
            value=title_score,
            reasoning=title_reasoning,
            weight=self.WEIGHTS['title_match'],
        ))

        exp_score, exp_reasoning = self._score_experience(profile)
        components.append(ScoreComponent(
            name='experience',
            value=exp_score,
            reasoning=exp_reasoning,
            weight=self.WEIGHTS['experience'],
        ))

        skills_score, skills_reasoning = self._score_skills(profile)
        components.append(ScoreComponent(
            name='skills',
            value=skills_score,
            reasoning=skills_reasoning,
            weight=self.WEIGHTS['skills'],
        ))

        behavioral_score, behavioral_reasoning = self._score_behavioral(profile)
        components.append(ScoreComponent(
            name='behavioral',
            value=behavioral_score,
            reasoning=behavioral_reasoning,
            weight=self.WEIGHTS['behavioral'],
        ))

        avail_score, avail_reasoning = self._score_availability(profile)
        components.append(ScoreComponent(
            name='availability',
            value=avail_score,
            reasoning=avail_reasoning,
            weight=self.WEIGHTS['availability'],
        ))

        final_score = sum(c.value * c.weight for c in components) / sum(c.weight for c in components)
        reasoning = self._build_reasoning(profile, components)

        return CandidateScore(
            candidate_id=candidate_id,
            final_score=final_score,
            rank=0,
            reasoning=reasoning,
            components=components,
        )

    def _score_title_match(self, profile: Dict) -> Tuple[float, str]:
        current_title = profile.get('profile', {}).get('current_title', '').lower()
        career_history = profile.get('career_history', [])

        current_match = any(target in current_title for target in self.TARGET_TITLES)
        recent_roles = career_history[:3]
        recent_match_count = sum(
            1 for job in recent_roles
            if any(target in job.get('title', '').lower() for target in self.TARGET_TITLES)
        )

        if current_match:
            score = 0.95
            reasoning = f"Current title '{current_title}' directly matches target roles"
        elif recent_match_count >= 2:
            score = 0.85
            reasoning = f"Recent roles ({recent_match_count}/3) match target titles"
        elif recent_match_count == 1:
            score = 0.65
            reasoning = f"One recent role matches target; current title is '{current_title}'"
        else:
            score = 0.35
            reasoning = f"No title match; current='{current_title}'"

        return score, reasoning

    def _score_experience(self, profile: Dict) -> Tuple[float, str]:
        timeline = validate_career_timeline(profile)
        total_years = timeline.total_years
        years_in_product = timeline.years_in_product
        years_in_ml_ai = timeline.years_in_ml_ai

        if 6 <= total_years <= 8:
            base_score = 0.90
        elif 5 <= total_years < 6:
            base_score = 0.80
        elif 8 < total_years <= 10:
            base_score = 0.75
        elif 4 <= total_years < 5:
            base_score = 0.70
        elif total_years < 4:
            base_score = 0.40
        else:
            base_score = 0.50

        product_boost = min(0.15, years_in_product / 5 * 0.15)
        ml_boost = min(0.10, years_in_ml_ai / 4 * 0.10)
        final_score = min(1.0, base_score + product_boost + ml_boost)

        reasoning = (
            f"{total_years:.1f} yrs experience ({years_in_product:.1f} in product, {years_in_ml_ai:.1f} in ML/AI)"
        )

        return final_score, reasoning

    def _score_skills(self, profile: Dict) -> Tuple[float, str]:
        from core.filters import get_ai_core_skills
        from core.honeypot_detector import cross_reference_skill_timelines

        ai_skills, valid_duration_count = get_ai_core_skills(profile.get('skills', []))
        honeypot_score = cross_reference_skill_timelines(profile)
        honeypot_penalty = honeypot_score.confidence * 0.3

        if len(ai_skills) >= 8 and valid_duration_count >= 6:
            base_score = 0.90
        elif len(ai_skills) >= 6 and valid_duration_count >= 4:
            base_score = 0.80
        elif len(ai_skills) >= 4 and valid_duration_count >= 2:
            base_score = 0.70
        elif len(ai_skills) >= 2:
            base_score = 0.50
        else:
            base_score = 0.30

        final_score = max(0.0, base_score - honeypot_penalty)
        reasoning = (
            f"{len(ai_skills)} AI skills ({valid_duration_count} with credible duration)"
        )
        if honeypot_score.is_suspected_honeypot:
            reasoning += "; keyword-stuffing suspected"

        return final_score, reasoning

    def _score_behavioral(self, profile: Dict) -> Tuple[float, str]:
        signals = profile.get('redrob_signals', {})
        recruiter_response_rate = signals.get('recruiter_response_rate', 0)
        interview_completion_rate = signals.get('interview_completion_rate', 0)
        profile_completeness = signals.get('profile_completeness_score', 50) / 100
        offer_acceptance = signals.get('offer_acceptance_rate', -1)
        if offer_acceptance >= 0:
            offer_signal = offer_acceptance
        else:
            offer_signal = 0.5

        behavioral_base = (
            recruiter_response_rate * 0.35 +
            interview_completion_rate * 0.35 +
            profile_completeness * 0.20 +
            offer_signal * 0.10
        )

        reasoning = (
            f"Recruiter response {recruiter_response_rate:.0%}, "
            f"interview completion {interview_completion_rate:.0%}"
        )

        return behavioral_base, reasoning

    def _score_availability(self, profile: Dict) -> Tuple[float, str]:
        signals = profile.get('redrob_signals', {})
        notice_days = signals.get('notice_period_days', 60)
        willing_relocate = signals.get('willing_to_relocate', False)
        location = profile.get('profile', {}).get('location', '').lower()
        target_cities = {'pune', 'noida', 'gurgaon', 'bangalore', 'hyderabad'}
        in_target_city = any(city in location for city in target_cities)

        if notice_days <= 30:
            notice_score = 1.0
        elif notice_days <= 60:
            notice_score = 0.85
        elif notice_days <= 90:
            notice_score = 0.70
        elif notice_days <= 120:
            notice_score = 0.55
        else:
            notice_score = 0.30

        location_score = 0.95 if in_target_city else (0.75 if willing_relocate else 0.50)
        final_score = (notice_score * 0.6) + (location_score * 0.4)

        reasoning = (
            f"Notice {notice_days}d, location: {location} "
            f"(in target: {in_target_city}, willing relocate: {willing_relocate})"
        )

        return final_score, reasoning

    def _build_reasoning(self, profile: Dict, components: List[ScoreComponent]) -> str:
        title = profile.get('profile', {}).get('current_title', 'Unknown')
        years = profile.get('profile', {}).get('years_of_experience', 0)
        top_components = sorted(
            components,
            key=lambda c: c.value * c.weight,
            reverse=True,
        )[:2]

        reason_parts = [f"{title} ({years:.1f} yrs)"]
        for comp in top_components:
            reason_parts.append(comp.reasoning)

        full_reasoning = "; ".join(reason_parts)
        if len(full_reasoning) > 200:
            full_reasoning = full_reasoning[:197] + '...'

        return full_reasoning
