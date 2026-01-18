// Reddit Summarizer - Simple Frontend JavaScript

// API Configuration
const API_BASE_URL = 'http://13.63.49.1:8000';

// DOM Elements
const sections = document.querySelectorAll('.section');
const navLinks = document.querySelectorAll('.nav-link');
const loading = document.getElementById('loading');

// Initialize
document.addEventListener('DOMContentLoaded', function() {
    loadMonitoringData();
    setupNavigation();
    setupEventListeners();
    loadSubreddits();
});

// Navigation
function setupNavigation() {
    navLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            const targetId = this.getAttribute('href').substring(1);
            showSection(targetId);
        });
    });
}

// Navigate to section from feature cards
function navigateToSection(sectionId) {
    showSection(sectionId);
    // Update active nav link
    navLinks.forEach(link => {
        link.classList.remove('active');
    });
    const activeLink = document.querySelector(`[href="#${sectionId}"]`);
    if (activeLink) {
        activeLink.classList.add('active');
    }
    // Smooth scroll to section
    document.getElementById(sectionId).scrollIntoView({ behavior: 'smooth' });
}

function showSection(sectionId) {
    // Hide all sections
    sections.forEach(section => {
        section.classList.remove('active');
    });
    
    // Remove active class from all nav links
    navLinks.forEach(link => {
        link.classList.remove('active');
    });
    
    // Show target section
    const targetSection = document.getElementById(sectionId);
    if (targetSection) {
        targetSection.classList.add('active');
    }
    
    // Add active class to corresponding nav link
    const activeLink = document.querySelector(`[href="#${sectionId}"]`);
    if (activeLink) {
        activeLink.classList.add('active');
    }
    
    // Load data for the section
    switch(sectionId) {
        case 'monitoring':
            loadMonitoringData();
            break;
        case 'trends':
            loadTrends();
            break;
        case 'summaries':
            loadSummaries();
            break;
        case 'beginner':
            loadBeginnerInsights();
            break;
    }
}

// Event Listeners
function setupEventListeners() {
    // Search input enter key
    document.getElementById('search-query').addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            performSearch();
        }
    });
    
    // Summary topic enter key
    document.getElementById('summary-topic').addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            loadSummaries();
        }
    });
}

// Loading Functions
function showLoading() {
    loading.classList.remove('hidden');
}

function hideLoading() {
    loading.classList.add('hidden');
}

// API Helper Functions
async function apiCall(endpoint, params = {}) {
    try {
        showLoading();
        const url = new URL(`${API_BASE_URL}${endpoint}`);
        Object.keys(params).forEach(key => url.searchParams.append(key, params[key]));
        
        const response = await fetch(url);
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        return await response.json();
    } catch (error) {
        console.error('API call failed:', error);
        showError(`Failed to fetch data: ${error.message}`);
        throw error;
    } finally {
        hideLoading();
    }
}

// Monitoring Data
async function loadMonitoringData() {
    try {
        const data = await apiCall('/monitoring');
        
        document.getElementById('total-posts').textContent = data.total_posts || 0;
        document.getElementById('summarized-posts').textContent = data.summarized_posts || 0;
        document.getElementById('coverage').textContent = `${data.summary_coverage_pct || 0}%`;
        document.getElementById('pipeline-status').textContent = data.pipeline_status || 'Unknown';
        
        // Update status color based on pipeline status
        const statusElement = document.getElementById('pipeline-status');
        if (data.pipeline_status === 'healthy') {
            statusElement.style.color = 'var(--secondary)';
        } else {
            statusElement.style.color = 'var(--primary)';
        }
    } catch (error) {
        // Set default values if monitoring fails
        document.getElementById('total-posts').textContent = 'N/A';
        document.getElementById('summarized-posts').textContent = 'N/A';
        document.getElementById('coverage').textContent = 'N/A';
        document.getElementById('pipeline-status').textContent = 'Offline';
        document.getElementById('pipeline-status').style.color = 'var(--primary)';
    }
}

// Subreddits Functions
async function loadSubreddits() {
    // Use hardcoded subreddits since API endpoint was removed
    const subreddits = [
        { name: 'datascience', description: 'Data science discussions' },
        { name: 'Python', description: 'Python programming' },
        { name: 'MachineLearning', description: 'Machine learning discussions' }
    ];
    
    // Small delay to ensure DOM is ready
    setTimeout(() => {
        populateSubredditDropdown(subreddits);
    }, 100);
}

function populateSubredditDropdown(subreddits) {
    console.log('🔄 Populating subreddit dropdown with:', subreddits);
    const dropdown = document.getElementById('search-subreddit');
    
    if (!dropdown) {
        console.error('❌ Could not find search-subreddit dropdown element');
        return;
    }
    
    console.log('✅ Found dropdown, current options:', dropdown.children.length);
    
    // Clear existing options except the first one
    while (dropdown.children.length > 1) {
        dropdown.removeChild(dropdown.lastChild);
    }
    
    // Add subreddit options
    subreddits.forEach(subreddit => {
        const option = document.createElement('option');
        option.value = subreddit.name;
        option.textContent = `r/${subreddit.name}`;
        if (subreddit.description) {
            option.title = subreddit.description;
        }
        dropdown.appendChild(option);
        console.log(`➕ Added option: r/${subreddit.name}`);
    });
    
    console.log(`✅ Subreddit dropdown populated with ${subreddits.length} options`);
}

// Search Functions
async function performSearch() {
    const query = document.getElementById('search-query').value.trim();
    const limit = document.getElementById('search-limit').value;
    const subreddit = document.getElementById('search-subreddit').value;
    
    if (!query) {
        showError('Please enter a search query');
        return;
    }
    
    try {
        const params = { query, limit };
        if (subreddit) params.subreddit = subreddit;
        
        const data = await apiCall('/search', params);
        displaySearchResults(data);
    } catch (error) {
        // Error already handled by apiCall
    }
}

function displaySearchResults(data) {
    const container = document.getElementById('search-results');
    
    console.log('🔍 Search Results Data:', data);
    
    if (!data.results || data.results.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <i class="fas fa-search"></i>
                <h3>No results found</h3>
                <p>Try adjusting your search terms or filters</p>
            </div>
        `;
        return;
    }
    
    const resultsHTML = data.results.map(post => {
        console.log('📝 Post object:', post);
        console.log('🔗 Raw permalink:', post.permalink);
        console.log('🔗 Permalink type:', typeof post.permalink);
        
        // Fix permalink if it's not a full Reddit URL
        let redditUrl = post.permalink;
        if (redditUrl && !redditUrl.startsWith('http')) {
            // Convert Reddit-style permalink to full URL
            if (redditUrl.startsWith('/r/')) {
                redditUrl = 'https://reddit.com' + redditUrl;
            } else if (redditUrl.startsWith('r/')) {
                redditUrl = 'https://reddit.com/' + redditUrl;
            } else {
                redditUrl = 'https://reddit.com/r/' + post.subreddit + '/comments/' + redditUrl;
            }
        }
        
        console.log('🌐 Fixed URL:', redditUrl);
        
        return `
        <div class="result-card">
            <div class="result-header">
                <div>
                    <a href="${redditUrl}" target="_blank" class="result-title">
                        ${post.title}
                    </a>
                    <div class="result-meta">
                        r/${post.subreddit} • Score: ${post.score}
                    </div>
                </div>
                <div class="result-score">${post.score}</div>
            </div>
            <div class="result-footer">
                <a href="${redditUrl}" target="_blank" class="result-link">
                    <i class="fas fa-external-link-alt"></i> View on Reddit
                </a>
            </div>
        </div>
    `}).join('');
    
    container.innerHTML = resultsHTML;
    showSuccess(`Found ${data.results_count} results for "${data.query}"`);
}

// Trends Functions
async function loadTrends() {
    const days = document.getElementById('trends-days').value;
    const limit = document.getElementById('trends-limit').value;
    
    try {
        const data = await apiCall('/trends', { days, limit });
        displayTrends(data);
    } catch (error) {
        // Error already handled by apiCall
    }
}

function displayTrends(data) {
    const container = document.getElementById('trends-results');
    
    if (!data.trending_topics || data.trending_topics.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <i class="fas fa-chart-line"></i>
                <h3>No trending topics found</h3>
                <p>Try a different time period</p>
            </div>
        `;
        return;
    }
    
    const trendsHTML = data.trending_topics.map((topic, index) => `
        <span class="trend-chip" onclick="selectTopic('${topic.topic}')">
            ${topic.topic} (${topic.mentions})
        </span>
    `).join('');
    
    container.innerHTML = trendsHTML;
    showSuccess(`Showing top ${data.trending_topics.length} trending topics`);
}

function selectTopic(topic) {
    document.getElementById('summary-topic').value = topic;
    showSection('summaries');
    loadSummaries();
}

// Summaries Functions
async function loadSummaries() {
    const topic = document.getElementById('summary-topic').value.trim();
    const limit = document.getElementById('summary-limit').value;
    
    try {
        const params = { limit };
        if (topic) params.topic = topic;
        
        const data = await apiCall('/summaries', params);
        displaySummaries(data);
    } catch (error) {
        // Error already handled by apiCall
    }
}

function displaySummaries(data) {
    const container = document.getElementById('summaries-results');
    
    if (!data.summaries || data.summaries.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <i class="fas fa-compress-alt"></i>
                <h3>No summaries found</h3>
                <p>Try a different topic or check back later</p>
            </div>
        `;
        return;
    }
    
    const summariesHTML = data.summaries.map(summary => {
        console.log('ML Learning Hub loaded successfully!');
        console.log('🔗 Summary permalink:', summary.permalink);
        
        // Fix permalink if it's not a full Reddit URL
        let redditUrl = summary.permalink;
        if (redditUrl && !redditUrl.startsWith('http')) {
            // Convert Reddit-style permalink to full URL
            if (redditUrl.startsWith('/r/')) {
                redditUrl = 'https://reddit.com' + redditUrl;
            } else if (redditUrl.startsWith('r/')) {
                redditUrl = 'https://reddit.com/' + redditUrl;
            } else {
                redditUrl = 'https://reddit.com/r/' + summary.name + '/comments/' + redditUrl;
            }
        }
        
        console.log('🌐 Fixed summary URL:', redditUrl);
        
        return `
        <div class="result-card">
            <div class="result-header">
                <div>
                    <a href="${redditUrl}" target="_blank" class="result-title">
                        ${summary.title}
                    </a>
                    <div class="result-meta">
                        r/${summary.name} • Score: ${summary.score}
                    </div>
                </div>
            </div>
            <div class="result-content">
                ${summary.summary_text ? `<strong>Summary:</strong> ${summary.summary_text}` : '<em>No summary available</em>'}
            </div>
            <div class="result-footer">
                <span>Post ID: ${summary.post_id}</span>
                <a href="${redditUrl}" target="_blank" class="result-link">
                    <i class="fas fa-external-link-alt"></i> View on Reddit
                </a>
            </div>
        </div>
    `}).join('');
    
    container.innerHTML = summariesHTML;
    showSuccess(`Found ${data.summaries.length} summaries for topic "${data.topic}"`);
}

// Beginner Insights Functions
async function loadBeginnerInsights() {
    const days = document.getElementById('beginner-days').value;
    
    try {
        const data = await apiCall('/beginner/insights', { days });
        displayBeginnerInsights(data);
    } catch (error) {
        // Error already handled by apiCall
    }
}

function displayBeginnerInsights(data) {
    const container = document.getElementById('beginner-results');
    
    if (!data.recommended_learning_focus || data.recommended_learning_focus.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <i class="fas fa-lightbulb"></i>
                <h3>No beginner insights found</h3>
                <p>Try a different time period</p>
            </div>
        `;
        return;
    }
    
    const insightsHTML = data.recommended_learning_focus.map((insight, index) => `
        <div class="result-card">
            <div class="result-header">
                <div>
                    <h3 class="result-title">Learning Focus #${index + 1}</h3>
                    <div class="result-meta">
                        Based on ${data.posts_used} posts in the last ${data.window_days} days
                    </div>
                </div>
                <div class="result-score">${insight.score}</div>
            </div>
            <div class="result-content">
                ${insight.insight}
            </div>
        </div>
    `).join('');
    
    container.innerHTML = insightsHTML;
    showSuccess(`Found ${data.recommended_learning_focus.length} learning recommendations`);
}

// Utility Functions
function formatDate(dateString) {
    const date = new Date(dateString);
    const now = new Date();
    const diffTime = Math.abs(now - date);
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
    
    if (diffDays === 1) return 'yesterday';
    if (diffDays < 7) return `${diffDays} days ago`;
    if (diffDays < 30) return `${Math.floor(diffDays / 7)} weeks ago`;
    return `${Math.floor(diffDays / 30)} months ago`;
}

function truncateText(text, maxLength) {
    if (text.length <= maxLength) return text;
    return text.substring(0, maxLength) + '...';
}

function showError(message) {
    // Remove existing messages
    removeMessages();
    
    // Create error message
    const errorDiv = document.createElement('div');
    errorDiv.className = 'error-message';
    errorDiv.innerHTML = `
        <i class="fas fa-exclamation-triangle"></i>
        <span>${message}</span>
    `;
    
    // Style the error message
    errorDiv.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: #dc3545;
        color: white;
        padding: 12px 20px;
        border-radius: 8px;
        display: flex;
        align-items: center;
        gap: 10px;
        z-index: 1001;
        box-shadow: 0 4px 12px rgba(220, 53, 69, 0.3);
        animation: slideIn 0.3s ease;
    `;
    
    document.body.appendChild(errorDiv);
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
        if (errorDiv.parentNode) {
            errorDiv.parentNode.removeChild(errorDiv);
        }
    }, 5000);
}

function showSuccess(message) {
    // Remove existing messages
    removeMessages();
    
    // Create success message
    const successDiv = document.createElement('div');
    successDiv.className = 'success-message';
    successDiv.innerHTML = `
        <i class="fas fa-check-circle"></i>
        <span>${message}</span>
    `;
    
    // Style the success message
    successDiv.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: #28a745;
        color: white;
        padding: 12px 20px;
        border-radius: 8px;
        display: flex;
        align-items: center;
        gap: 10px;
        z-index: 1001;
        box-shadow: 0 4px 12px rgba(40, 167, 69, 0.3);
        animation: slideIn 0.3s ease;
    `;
    
    document.body.appendChild(successDiv);
    
    // Auto-remove after 3 seconds
    setTimeout(() => {
        if (successDiv.parentNode) {
            successDiv.parentNode.removeChild(successDiv);
        }
    }, 3000);
}

function removeMessages() {
    const messages = document.querySelectorAll('.error-message, .success-message');
    messages.forEach(msg => {
        if (msg.parentNode) {
            msg.parentNode.removeChild(msg);
        }
    });
}

// Add slide-in animation
const style = document.createElement('style');
style.textContent = `
    @keyframes slideIn {
        from {
            transform: translateX(100%);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }
`;
document.head.appendChild(style);

// Auto-refresh monitoring data every 30 seconds
setInterval(loadMonitoringData, 30000);
