from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class AnalyzeRequest(BaseModel):
    query: str  # Can be username, email, or GitHub URL


class LanguageStat(BaseModel):
    name: str
    percentage: float
    bytes: int
    color: str


class RepoHighlight(BaseModel):
    name: str
    description: Optional[str]
    stars: int
    forks: int
    language: Optional[str]
    url: str


class ActivityPattern(BaseModel):
    most_active_day: str
    most_active_hour: int
    total_commits_last_year: int
    longest_streak: int
    current_streak: int
    consistency_score: float  # 0-100


class CollaborationMetrics(BaseModel):
    public_repos: int
    public_gists: int
    followers: int
    following: int
    follower_ratio: float
    organizations: list[str]


class GrowthTimeline(BaseModel):
    year: int
    repos_created: int
    languages_used: list[str]
    stars_earned: int


class ProfileAnalysis(BaseModel):
    # Basic Info
    username: str
    name: Optional[str]
    avatar_url: str
    bio: Optional[str]
    location: Optional[str]
    company: Optional[str]
    blog: Optional[str]
    twitter: Optional[str]
    email: Optional[str]
    hireable: Optional[bool]

    # Account Info
    created_at: datetime
    account_age_years: float
    profile_url: str

    # Technical Skills
    languages: list[LanguageStat]
    primary_language: Optional[str]
    tech_diversity_score: float  # 0-100

    # Top Repositories
    top_repos: list[RepoHighlight]
    total_stars: int
    total_forks: int

    # Activity
    activity: ActivityPattern

    # Collaboration
    collaboration: CollaborationMetrics

    # Growth
    growth_timeline: list[GrowthTimeline]

    # Overall Scores
    overall_score: float  # 0-100
    experience_level: str  # Junior, Mid, Senior, Expert
    focus_areas: list[str]  # e.g., ["Web Development", "Data Science"]

    # Recruiter Brief
    recruiter_summary: str


class ErrorResponse(BaseModel):
    error: str
    detail: Optional[str] = None
