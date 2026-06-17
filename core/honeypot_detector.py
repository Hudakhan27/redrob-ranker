"""Detect keyword-stuffing and structurally impossible profiles."""

from dataclasses import dataclass
from typing import Dict, List


@dataclass
class HoneypotScore:
    is_suspected_honeypot: bool
    red_flags: List[str]
    confidence: float


def cross_reference_skill_timelines(profile: Dict) -> HoneypotScore:
    red_flags = []
    career_history = profile.get('career_history', [])
    skills = profile.get('skills', [])

    total_career_months = sum(job.get('duration_months', 0) for job in career_history)

    for skill in skills:
        skill_duration = skill.get('duration_months', 0)
        proficiency = skill.get('proficiency', '').lower()
        name = skill.get('name', '')

        if skill_duration > total_career_months:
            red_flags.append(
                f"Impossible skill timeline: '{name}' claimed for {skill_duration} months, "
                f"total career is only {total_career_months} months"
            )

        if proficiency == 'expert' and skill_duration < 6:
            red_flags.append(
                f"Skill '{name}' marked 'expert' with only "
                f"{skill_duration} months experience"
            )

        if proficiency == 'expert' and 6 <= skill_duration < 12:
            red_flags.append(
                f"Skill '{name}' marked 'expert' with only "
                f"{skill_duration} months (<12 expected)"
            )

    total_skill_months = sum(s.get('duration_months', 0) for s in skills)
    if total_career_months > 0 and total_skill_months > total_career_months * 3:
        red_flags.append(
            f"Total skill months ({total_skill_months}) >> 3 × career months ({total_career_months * 3}); likely overlap inflation"
        )

    is_honeypot = len(red_flags) >= 1
    confidence = min(1.0, len(red_flags) / 5.0)

    return HoneypotScore(is_suspected_honeypot=is_honeypot, red_flags=red_flags, confidence=confidence)


def detect_keyword_stuffing(profile: Dict) -> HoneypotScore:
    red_flags = []
    skills = profile.get('skills', [])
    current_title = profile.get('profile', {}).get('current_title', '').lower()

    ai_count = sum(
        1 for s in skills
        if any(kw in s.get('name', '').lower() for kw in [
            'llm', 'nlp', 'ml', 'ai', 'deep learning', 'machine learning',
            'ranking', 'embeddings', 'transformer', 'rag', 'langchain',
            'faiss', 'prompt engineering', 'fine-tuning', 'fine tuning',
            'chatgpt', 'openai', 'bert', 'gpt', 'llama', 'stable diffusion'
        ])
    )

    relevant_titles = {'engineer', 'scientist', 'analyst', 'researcher', 'manager'}
    title_is_relevant = any(t in current_title for t in relevant_titles)

    if ai_count >= 8 and not title_is_relevant:
        red_flags.append(
            f"High AI skill count ({ai_count}) but title '{current_title}' is not technical"
        )

    for skill in skills:
        if skill.get('proficiency') == 'expert':
            endorsements = skill.get('endorsements', 0)
            duration = skill.get('duration_months', 1)
            endorsement_rate = endorsements / (duration / 12 + 0.1)
            if endorsement_rate > 50:
                red_flags.append(
                    f"Skill '{skill.get('name')}': {endorsement_rate:.0f} endorsements/year (suspicious)"
                )

    is_honeypot = len(red_flags) >= 1
    confidence = min(1.0, len(red_flags) * 0.6)

    return HoneypotScore(is_suspected_honeypot=is_honeypot, red_flags=red_flags, confidence=confidence)
