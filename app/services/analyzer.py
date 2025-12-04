from datetime import datetime, timezone
from collections import Counter, defaultdict
from typing import Optional
from app.models.schemas import (
    ProfileAnalysis, LanguageStat, RepoHighlight, ActivityPattern,
    CollaborationMetrics, GrowthTimeline
)

# Language colors from GitHub
LANGUAGE_COLORS = {
    "Python": "#3572A5",
    "JavaScript": "#f1e05a",
    "TypeScript": "#2b7489",
    "Java": "#b07219",
    "C++": "#f34b7d",
    "C": "#555555",
    "C#": "#178600",
    "Go": "#00ADD8",
    "Rust": "#dea584",
    "Ruby": "#701516",
    "PHP": "#4F5D95",
    "Swift": "#ffac45",
    "Kotlin": "#F18E33",
    "Dart": "#00B4AB",
    "Scala": "#c22d40",
    "R": "#198CE7",
    "Shell": "#89e051",
    "HTML": "#e34c26",
    "CSS": "#563d7c",
    "Vue": "#41b883",
    "Svelte": "#ff3e00",
    "Jupyter Notebook": "#DA5B0B",
}

# Focus area detection based on common patterns
FOCUS_PATTERNS = {
    "Web Development": ["JavaScript", "TypeScript", "HTML", "CSS", "Vue", "React", "Angular", "Svelte", "PHP"],
    "Data Science": ["Python", "R", "Jupyter Notebook"],
    "Mobile Development": ["Swift", "Kotlin", "Dart", "Java"],
    "Systems Programming": ["C", "C++", "Rust", "Go"],
    "DevOps": ["Shell", "Python", "Go", "Dockerfile"],
    "Backend Development": ["Java", "Python", "Go", "Ruby", "PHP", "C#"],
    "Game Development": ["C++", "C#", "GDScript"],
}


class ProfileAnalyzer:
    def __init__(self):
        pass

    def _calculate_account_age(self, created_at: str) -> float:
        """Calculate account age in years."""
        created = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
        now = datetime.now(timezone.utc)
        age_days = (now - created).days
        return round(age_days / 365.25, 1)

    def _aggregate_languages(self, repos: list[dict], repo_languages: dict[str, dict]) -> list[LanguageStat]:
        """Aggregate language statistics across all repos."""
        total_bytes = defaultdict(int)

        for repo in repos:
            repo_name = repo["name"]
            if repo_name in repo_languages:
                for lang, bytes_count in repo_languages[repo_name].items():
                    total_bytes[lang] += bytes_count

        total = sum(total_bytes.values()) or 1

        languages = []
        for lang, bytes_count in sorted(total_bytes.items(), key=lambda x: x[1], reverse=True):
            languages.append(LanguageStat(
                name=lang,
                percentage=round((bytes_count / total) * 100, 1),
                bytes=bytes_count,
                color=LANGUAGE_COLORS.get(lang, "#858585")
            ))

        return languages[:10]  # Top 10 languages

    def _get_top_repos(self, repos: list[dict], limit: int = 5) -> list[RepoHighlight]:
        """Get top repositories by stars."""
        sorted_repos = sorted(repos, key=lambda r: r.get("stargazers_count", 0), reverse=True)

        highlights = []
        for repo in sorted_repos[:limit]:
            highlights.append(RepoHighlight(
                name=repo["name"],
                description=repo.get("description"),
                stars=repo.get("stargazers_count", 0),
                forks=repo.get("forks_count", 0),
                language=repo.get("language"),
                url=repo["html_url"]
            ))

        return highlights

    def _analyze_activity(self, contribution_stats: dict, repos: list[dict]) -> ActivityPattern:
        """Analyze activity patterns."""
        commit_hours = contribution_stats.get("commit_hours", [])
        commit_days = contribution_stats.get("commit_days", [])

        # Most active hour
        hour_counts = Counter(commit_hours)
        most_active_hour = hour_counts.most_common(1)[0][0] if hour_counts else 12

        # Most active day
        day_counts = Counter(commit_days)
        most_active_day = day_counts.most_common(1)[0][0] if day_counts else "Monday"

        # Calculate consistency score based on repo update frequency
        total_commits = contribution_stats.get("total_push_events", 0)

        # Simple consistency calculation
        consistency = min(100, (total_commits / 30) * 100)  # Normalize to 100

        return ActivityPattern(
            most_active_day=most_active_day,
            most_active_hour=most_active_hour,
            total_commits_last_year=total_commits * 4,  # Estimate
            longest_streak=0,  # Would need more data
            current_streak=0,
            consistency_score=round(consistency, 1)
        )

    def _calculate_collaboration(self, user: dict, orgs: list[str]) -> CollaborationMetrics:
        """Calculate collaboration metrics."""
        followers = user.get("followers", 0)
        following = user.get("following", 0)

        follower_ratio = round(followers / max(following, 1), 2)

        return CollaborationMetrics(
            public_repos=user.get("public_repos", 0),
            public_gists=user.get("public_gists", 0),
            followers=followers,
            following=following,
            follower_ratio=follower_ratio,
            organizations=orgs
        )

    def _build_growth_timeline(self, repos: list[dict]) -> list[GrowthTimeline]:
        """Build growth timeline from repos."""
        yearly_data = defaultdict(lambda: {"repos": 0, "languages": set(), "stars": 0})

        for repo in repos:
            created = datetime.fromisoformat(repo["created_at"].replace("Z", "+00:00"))
            year = created.year

            yearly_data[year]["repos"] += 1
            yearly_data[year]["stars"] += repo.get("stargazers_count", 0)
            if repo.get("language"):
                yearly_data[year]["languages"].add(repo["language"])

        timeline = []
        for year in sorted(yearly_data.keys()):
            data = yearly_data[year]
            timeline.append(GrowthTimeline(
                year=year,
                repos_created=data["repos"],
                languages_used=list(data["languages"]),
                stars_earned=data["stars"]
            ))

        return timeline

    def _detect_focus_areas(self, languages: list[LanguageStat]) -> list[str]:
        """Detect focus areas based on languages used."""
        lang_names = {lang.name for lang in languages[:5]}
        focus_areas = []

        for area, area_languages in FOCUS_PATTERNS.items():
            if lang_names & set(area_languages):
                focus_areas.append(area)

        return focus_areas[:3]  # Top 3 focus areas

    def _calculate_overall_score(
            self,
            user: dict,
            repos: list[dict],
            languages: list[LanguageStat],
            activity: ActivityPattern,
            collaboration: CollaborationMetrics
    ) -> float:
        """Calculate overall developer score (0-100)."""
        scores = []

        # Repository score (0-25)
        repo_score = min(25, len(repos) * 1.5)
        scores.append(repo_score)

        # Stars score (0-25)
        total_stars = sum(r.get("stargazers_count", 0) for r in repos)
        star_score = min(25, total_stars * 0.5)
        scores.append(star_score)

        # Language diversity (0-15)
        diversity_score = min(15, len(languages) * 2)
        scores.append(diversity_score)

        # Activity score (0-20)
        activity_score = min(20, activity.consistency_score * 0.2)
        scores.append(activity_score)

        # Community engagement (0-15)
        engagement_score = min(15, (collaboration.followers / 10) + (len(collaboration.organizations) * 2))
        scores.append(engagement_score)

        return round(sum(scores), 1)

    def _determine_experience_level(self, account_age: float, repos: list[dict], score: float) -> str:
        """Determine experience level."""
        if score >= 70 or (account_age >= 5 and len(repos) >= 30):
            return "Expert"
        elif score >= 50 or (account_age >= 3 and len(repos) >= 15):
            return "Senior"
        elif score >= 30 or (account_age >= 1 and len(repos) >= 5):
            return "Mid-Level"
        else:
            return "Junior"

    def _generate_summary(
            self,
            user: dict,
            languages: list[LanguageStat],
            repos: list[dict],
            activity: ActivityPattern,
            collaboration: CollaborationMetrics,
            experience_level: str,
            focus_areas: list[str],
            account_age: float
    ) -> str:
        """Generate recruiter-friendly summary."""
        name = user.get("name") or user["login"]
        primary_lang = languages[0].name if languages else "various technologies"
        total_stars = sum(r.get("stargazers_count", 0) for r in repos)

        # Build summary parts
        parts = []

        # Intro
        parts.append(f"{name} is a {experience_level.lower()}-level developer")
        if account_age >= 1:
            parts.append(f"with {account_age:.0f}+ years on GitHub")

        # Tech focus
        if focus_areas:
            parts.append(f", focusing on {', '.join(focus_areas[:2])}")

        parts.append(". ")

        # Technical skills
        if languages:
            top_langs = [l.name for l in languages[:3]]
            parts.append(f"Primary expertise in {', '.join(top_langs)}. ")

        # Achievements
        if total_stars > 0:
            parts.append(f"Has earned {total_stars} stars across {len(repos)} public repositories. ")

        # Collaboration
        if collaboration.followers >= 10:
            parts.append(f"Active community member with {collaboration.followers} followers")
            if collaboration.organizations:
                parts.append(f" and contributions to {len(collaboration.organizations)} organizations")
            parts.append(". ")

        # Activity pattern
        parts.append(f"Most active on {activity.most_active_day}s")
        if activity.most_active_hour < 12:
            parts.append(" (morning coder)")
        elif activity.most_active_hour < 18:
            parts.append(" (afternoon coder)")
        else:
            parts.append(" (evening coder)")
        parts.append(".")

        return "".join(parts)

    async def analyze(
            self,
            user: dict,
            repos: list[dict],
            repo_languages: dict[str, dict],
            contribution_stats: dict,
            orgs: list[str]
    ) -> ProfileAnalysis:
        """Perform complete profile analysis."""

        account_age = self._calculate_account_age(user["created_at"])
        languages = self._aggregate_languages(repos, repo_languages)
        top_repos = self._get_top_repos(repos)
        activity = self._analyze_activity(contribution_stats, repos)
        collaboration = self._calculate_collaboration(user, orgs)
        growth_timeline = self._build_growth_timeline(repos)
        focus_areas = self._detect_focus_areas(languages)

        total_stars = sum(r.get("stargazers_count", 0) for r in repos)
        total_forks = sum(r.get("forks_count", 0) for r in repos)

        overall_score = self._calculate_overall_score(user, repos, languages, activity, collaboration)
        experience_level = self._determine_experience_level(account_age, repos, overall_score)

        tech_diversity = min(100, len(languages) * 12)

        summary = self._generate_summary(
            user, languages, repos, activity, collaboration,
            experience_level, focus_areas, account_age
        )

        return ProfileAnalysis(
            username=user["login"],
            name=user.get("name"),
            avatar_url=user["avatar_url"],
            bio=user.get("bio"),
            location=user.get("location"),
            company=user.get("company"),
            blog=user.get("blog"),
            twitter=user.get("twitter_username"),
            email=user.get("email"),
            hireable=user.get("hireable"),
            created_at=datetime.fromisoformat(user["created_at"].replace("Z", "+00:00")),
            account_age_years=account_age,
            profile_url=user["html_url"],
            languages=languages,
            primary_language=languages[0].name if languages else None,
            tech_diversity_score=round(tech_diversity, 1),
            top_repos=top_repos,
            total_stars=total_stars,
            total_forks=total_forks,
            activity=activity,
            collaboration=collaboration,
            growth_timeline=growth_timeline,
            overall_score=overall_score,
            experience_level=experience_level,
            focus_areas=focus_areas,
            recruiter_summary=summary
        )
