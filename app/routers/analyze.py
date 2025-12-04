from fastapi import APIRouter, HTTPException
from app.models.schemas import AnalyzeRequest, ProfileAnalysis, ErrorResponse
from app.services.github_service import GitHubService, get_cache_stats, clear_cache
from app.services.analyzer import ProfileAnalyzer
from dotenv import load_dotenv
import os

# Load .env before accessing environment variables
load_dotenv()

router = APIRouter()

github_service = GitHubService(token=os.getenv("GITHUB_TOKEN"))
analyzer = ProfileAnalyzer()


@router.post("/analyze", response_model=ProfileAnalysis, responses={404: {"model": ErrorResponse}})
async def analyze_profile(request: AnalyzeRequest):
    """Analyze a GitHub profile and return comprehensive metrics."""
    try:
        # Resolve username from query
        username = await github_service.resolve_username(request.query)

        # Fetch all data concurrently where possible
        user = await github_service.get_user(username)
        repos = await github_service.get_repos(username)
        orgs = await github_service.get_orgs(username)
        contribution_stats = await github_service.get_contribution_stats(username)

        # Fetch languages for top repos concurrently
        repo_names = [repo["name"] for repo in repos[:20]]
        repo_languages = await github_service.get_multiple_repo_languages(username, repo_names)

        # Perform analysis
        analysis = await analyzer.analyze(
            user=user,
            repos=repos,
            repo_languages=repo_languages,
            contribution_stats=contribution_stats,
            orgs=orgs
        )

        return analysis

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        if "404" in str(e):
            raise HTTPException(status_code=404, detail=f"GitHub user not found: {request.query}")
        raise HTTPException(status_code=500, detail=f"Error analyzing profile: {str(e)}")


@router.get("/rate-limit")
async def get_rate_limit():
    """Get current GitHub API rate limit status."""
    return github_service.get_rate_limit_info()


@router.get("/cache/stats")
async def cache_stats():
    """Get cache statistics."""
    return get_cache_stats()


@router.post("/cache/clear")
async def cache_clear():
    """Clear the cache."""
    clear_cache()
    return {"message": "Cache cleared"}
