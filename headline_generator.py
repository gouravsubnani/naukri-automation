"""
Headline generator for Naukri.com profile.
Generates fresh, keyword-rich headlines daily so your profile stays active
and relevant to recruiter searches.
"""

import random
from datetime import datetime


# Core keywords to always rotate through
CORE_KEYWORDS = [
    "Data Engineer",
    "STL",
    "SnapLogic",
    "Developer",
]

# Extended skill keywords to mix in
SKILL_KEYWORDS = [
    "ETL",
    "Python",
    "SQL",
    "Data Pipeline",
    "Cloud",
    "AWS",
    "Azure",
    "Big Data",
    "Apache Spark",
    "Kafka",
    "Airflow",
    "Data Warehouse",
    "Snowflake",
    "Databricks",
    "Data Integration",
    "API Development",
    "CI/CD",
    "Docker",
]

# Headline templates — {kw1}, {kw2}, {kw3} get replaced with keywords
HEADLINE_TEMPLATES = [
    "Experienced {kw1} | {kw2} & {kw3} Specialist | Building Scalable Data Solutions",
    "{kw1} with Expertise in {kw2}, {kw3} | Passionate About Data-Driven Innovation",
    "Senior {kw1} | {kw2} | {kw3} | Designing Robust Data Pipelines",
    "{kw1} | Skilled in {kw2} & {kw3} | Delivering End-to-End Data Solutions",
    "Results-Driven {kw1} | {kw2}, {kw3} Expert | Automating Data Workflows",
    "{kw1} Professional | {kw2} | {kw3} | Turning Raw Data into Business Value",
    "Dedicated {kw1} | {kw2} & {kw3} Enthusiast | Scalable Architecture Design",
    "{kw1} | Proficient in {kw2}, {kw3} | High-Performance Data Engineering",
    "Innovative {kw1} | {kw2} | {kw3} | Streamlining Data Infrastructure",
    "{kw1} & {kw2} Specialist | {kw3} | Optimizing Data Ecosystems",
    "Versatile {kw1} | {kw2}, {kw3} | Bridging Data and Business Strategy",
    "{kw1} | Expert in {kw2} & {kw3} | Enabling Data-Driven Decisions",
]


def generate_headline() -> str:
    """
    Generate a unique headline for today.

    Uses the current date as a seed component so the same day always
    produces the same headline (idempotent if run multiple times),
    but each new day yields a different one.
    """
    today = datetime.now().strftime("%Y-%m-%d")
    seed = int(datetime.now().strftime("%Y%m%d"))
    rng = random.Random(seed)

    # Always pick one core keyword as kw1
    kw1 = rng.choice(CORE_KEYWORDS)

    # Pick kw2 from remaining core + skill keywords (no duplicates)
    remaining = [k for k in CORE_KEYWORDS + SKILL_KEYWORDS if k != kw1]
    kw2 = rng.choice(remaining)

    # Pick kw3 from what's left
    remaining = [k for k in remaining if k != kw2]
    kw3 = rng.choice(remaining)

    # Pick a template
    template = rng.choice(HEADLINE_TEMPLATES)

    headline = template.format(kw1=kw1, kw2=kw2, kw3=kw3)

    # Naukri headline limit is ~250 chars — trim if needed
    if len(headline) > 250:
        headline = headline[:247] + "..."

    return headline


if __name__ == "__main__":
    # Quick test — run this file directly to see today's headline
    print(f"Today's headline ({datetime.now().strftime('%Y-%m-%d')}):")
    print(generate_headline())
