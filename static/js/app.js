let languageChart = null;
let timelineChart = null;

async function analyzeProfile() {
    const input = document.getElementById('searchInput').value.trim();
    if (!input) {
        alert('Please enter a GitHub username, URL, or email');
        return;
    }

    // Show loading, hide others
    document.getElementById('loadingState').classList.remove('hidden');
    document.getElementById('errorState').classList.add('hidden');
    document.getElementById('resultsContainer').classList.add('hidden');

    try {
        const response = await fetch('/api/analyze', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ query: input })
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to analyze profile');
        }

        const data = await response.json();
        displayResults(data);

    } catch (error) {
        document.getElementById('loadingState').classList.add('hidden');
        document.getElementById('errorState').classList.remove('hidden');
        document.getElementById('errorMessage').textContent = error.message;
    }
}

function displayResults(data) {
    document.getElementById('loadingState').classList.add('hidden');
    document.getElementById('resultsContainer').classList.remove('hidden');

    // Profile Header
    document.getElementById('avatar').src = data.avatar_url;
    document.getElementById('profileName').textContent = data.name || data.username;
    document.getElementById('username').textContent = `@${data.username}`;
    document.getElementById('bio').textContent = data.bio || 'No bio available';
    document.getElementById('experienceLevel').textContent = data.experience_level;

    if (data.hireable) {
        document.getElementById('hireableBadge').classList.remove('hidden');
    } else {
        document.getElementById('hireableBadge').classList.add('hidden');
    }

    // Profile Meta
    const metaHtml = [];
    if (data.location) metaHtml.push(`<span>📍 ${data.location}</span>`);
    if (data.company) metaHtml.push(`<span>🏢 ${data.company}</span>`);
    if (data.blog) metaHtml.push(`<a href="${data.blog.startsWith('http') ? data.blog : 'https://' + data.blog}" target="_blank" class="text-purple-600 hover:underline">🔗 Website</a>`);
    if (data.twitter) metaHtml.push(`<a href="https://twitter.com/${data.twitter}" target="_blank" class="text-purple-600 hover:underline">🐦 @${data.twitter}</a>`);
    metaHtml.push(`<a href="${data.profile_url}" target="_blank" class="text-purple-600 hover:underline">View on GitHub →</a>`);
    document.getElementById('profileMeta').innerHTML = metaHtml.join('');

    // Score Ring Animation
    const score = Math.min(100, data.overall_score);
    const circumference = 2 * Math.PI * 45;
    const offset = circumference - (score / 100) * circumference;
    const scoreRing = document.getElementById('scoreRing');
    setTimeout(() => {
        scoreRing.style.transition = 'stroke-dashoffset 1s ease-out';
        scoreRing.style.strokeDashoffset = offset;
    }, 100);
    document.getElementById('overallScore').textContent = Math.round(score);

    // Recruiter Summary
    document.getElementById('recruiterSummary').textContent = data.recruiter_summary;

    // Stats
    document.getElementById('statRepos').textContent = data.collaboration.public_repos;
    document.getElementById('statStars').textContent = formatNumber(data.total_stars);
    document.getElementById('statFollowers').textContent = formatNumber(data.collaboration.followers);
    document.getElementById('statYears').textContent = data.account_age_years;

    // Languages
    const langContainer = document.getElementById('languagesContainer');
    langContainer.innerHTML = data.languages.slice(0, 6).map(lang => `
        <div class="flex items-center justify-between mb-2">
            <div class="flex items-center gap-2">
                <div class="w-3 h-3 rounded-full" style="background-color: ${lang.color}"></div>
                <span class="text-sm font-medium">${lang.name}</span>
            </div>
            <span class="text-sm text-gray-500">${lang.percentage}%</span>
        </div>
    `).join('');

    // Language Chart
    renderLanguageChart(data.languages.slice(0, 6));

    // Activity Info
    const activityHtml = `
        <div class="flex justify-between items-center p-3 bg-gray-50 rounded-lg">
            <span class="text-gray-600">Most Active Day</span>
            <span class="font-semibold">${data.activity.most_active_day}</span>
        </div>
        <div class="flex justify-between items-center p-3 bg-gray-50 rounded-lg">
            <span class="text-gray-600">Peak Hours</span>
            <span class="font-semibold">${formatHour(data.activity.most_active_hour)}</span>
        </div>
        <div class="flex justify-between items-center p-3 bg-gray-50 rounded-lg">
            <span class="text-gray-600">Consistency Score</span>
            <span class="font-semibold">${data.activity.consistency_score}%</span>
        </div>
    `;
    document.getElementById('activityInfo').innerHTML = activityHtml;

    // Focus Areas
    const focusHtml = data.focus_areas.map(area =>
        `<span class="px-3 py-1 bg-purple-100 text-purple-700 rounded-full text-sm">${area}</span>`
    ).join('');
    document.getElementById('focusAreas').innerHTML = focusHtml || '<span class="text-gray-500">Not enough data</span>';

    // Top Repos
    const reposHtml = data.top_repos.map(repo => `
        <a href="${repo.url}" target="_blank" class="block p-4 border rounded-lg hover:border-purple-300 hover:shadow-md transition-all">
            <div class="font-semibold text-gray-800 mb-1">${repo.name}</div>
            <p class="text-sm text-gray-600 mb-2 line-clamp-2">${repo.description || 'No description'}</p>
            <div class="flex items-center gap-4 text-sm text-gray-500">
                ${repo.language ? `<span class="flex items-center gap-1"><span class="w-2 h-2 rounded-full" style="background-color: ${getLanguageColor(repo.language)}"></span>${repo.language}</span>` : ''}
                <span>⭐ ${repo.stars}</span>
                <span>🍴 ${repo.forks}</span>
            </div>
        </a>
    `).join('');
    document.getElementById('topRepos').innerHTML = reposHtml || '<p class="text-gray-500">No repositories found</p>';

    // Growth Timeline
    renderTimelineChart(data.growth_timeline);

    // Organizations
    if (data.collaboration.organizations && data.collaboration.organizations.length > 0) {
        document.getElementById('orgsSection').classList.remove('hidden');
        document.getElementById('orgsList').innerHTML = data.collaboration.organizations.map(org =>
            `<a href="https://github.com/${org}" target="_blank" class="px-4 py-2 bg-gray-100 rounded-lg hover:bg-gray-200 transition-colors">${org}</a>`
        ).join('');
    } else {
        document.getElementById('orgsSection').classList.add('hidden');
    }
}

function renderLanguageChart(languages) {
    const ctx = document.getElementById('languageChart').getContext('2d');

    if (languageChart) {
        languageChart.destroy();
    }

    languageChart = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: languages.map(l => l.name),
            datasets: [{
                data: languages.map(l => l.percentage),
                backgroundColor: languages.map(l => l.color),
                borderWidth: 0
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: {
                    display: false
                }
            },
            cutout: '60%'
        }
    });
}

function renderTimelineChart(timeline) {
    const ctx = document.getElementById('timelineChart').getContext('2d');

    if (timelineChart) {
        timelineChart.destroy();
    }

    timelineChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: timeline.map(t => t.year),
            datasets: [{
                label: 'Repositories Created',
                data: timeline.map(t => t.repos_created),
                backgroundColor: '#667eea',
                borderRadius: 4
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: {
                    display: false
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        stepSize: 1
                    }
                }
            }
        }
    });
}

function formatNumber(num) {
    if (num >= 1000000) return (num / 1000000).toFixed(1) + 'M';
    if (num >= 1000) return (num / 1000).toFixed(1) + 'K';
    return num.toString();
}

function formatHour(hour) {
    const period = hour >= 12 ? 'PM' : 'AM';
    const displayHour = hour % 12 || 12;
    return `${displayHour}:00 ${period}`;
}

function getLanguageColor(lang) {
    const colors = {
        "Python": "#3572A5",
        "JavaScript": "#f1e05a",
        "TypeScript": "#2b7489",
        "Java": "#b07219",
        "C++": "#f34b7d",
        "C": "#555555",
        "Go": "#00ADD8",
        "Rust": "#dea584",
        "Ruby": "#701516",
        "PHP": "#4F5D95"
    };
    return colors[lang] || '#858585';
}

// Enter key support
document.getElementById('searchInput').addEventListener('keypress', function(e) {
    if (e.key === 'Enter') {
        analyzeProfile();
    }
});

// Rate limit and cache status
async function updateStatus() {
    try {
        const [rateLimit, cacheStats] = await Promise.all([
            fetch('/api/rate-limit').then(r => r.json()),
            fetch('/api/cache/stats').then(r => r.json())
        ]);

        const rateLimitEl = document.getElementById('rateLimitStatus');
        const tokenEl = document.getElementById('tokenStatus');
        const cacheEl = document.getElementById('cacheStatus');

        if (rateLimit.remaining !== null) {
            const color = rateLimit.remaining > 100 ? 'text-green-400' : rateLimit.remaining > 20 ? 'text-yellow-400' : 'text-red-400';
            rateLimitEl.innerHTML = `API Requests: <span class="${color}">${rateLimit.remaining} remaining</span>`;
        } else {
            rateLimitEl.textContent = 'API Status: Ready';
        }

        if (rateLimit.has_token) {
            tokenEl.innerHTML = '<span class="text-green-400">Token: Active (5000/hr)</span>';
        } else {
            tokenEl.innerHTML = '<span class="text-yellow-400">No token (60/hr) - Add GITHUB_TOKEN to .env</span>';
        }

        cacheEl.textContent = `Cache: ${cacheStats.valid_entries} entries`;

    } catch (error) {
        console.error('Failed to fetch status:', error);
    }
}

// Update status on load and after each analysis
updateStatus();

// Wrap original analyzeProfile to update status after
const originalAnalyzeProfile = analyzeProfile;
analyzeProfile = async function() {
    await originalAnalyzeProfile();
    updateStatus();
};
