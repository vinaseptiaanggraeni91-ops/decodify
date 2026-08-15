// Header functionality
document.addEventListener('DOMContentLoaded', function() {
    // Global Search
    const globalSearch = document.getElementById('globalSearch');
    const notificationsBtn = document.getElementById('notificationsBtn');
    const themeToggle = document.getElementById('themeToggle');
    
    // Search functionality
    if (globalSearch) {
        let searchTimeout;
        
        globalSearch.addEventListener('input', function(e) {
            clearTimeout(searchTimeout);
            const searchTerm = e.target.value.trim();
            
            if (searchTerm.length < 2) {
                hideSearchResults();
                return;
            }
            
            searchTimeout = setTimeout(() => {
                performGlobalSearch(searchTerm);
            }, 500);
        });
        
        globalSearch.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                const searchTerm = e.target.value.trim();
                if (searchTerm.length > 0) {
                    window.location.href = `/search?q=${encodeURIComponent(searchTerm)}`;
                }
            }
        });
        
        // Hide results when clicking outside
        document.addEventListener('click', function(e) {
            if (!e.target.closest('.header-search')) {
                hideSearchResults();
            }
        });
    }
    
    // Notifications functionality
    if (notificationsBtn) {
        notificationsBtn.addEventListener('click', function() {
            toggleNotificationsPanel();
        });
    }
    
    // Theme toggle
    if (themeToggle) {
        themeToggle.addEventListener('click', function() {
            toggleTheme();
        });
        
        // Load saved theme
        const savedTheme = localStorage.getItem('theme') || 'light';
        setTheme(savedTheme);
    }
    
    // Load weather data
    loadWeatherData();
    
    // Load notifications count
    loadNotificationsCount();
});

// Global Search Functions
function performGlobalSearch(searchTerm) {
    fetch('/api/search/global', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ search: searchTerm })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            displaySearchResults(data.results, searchTerm);
        } else {
            console.error('Search error:', data.error);
        }
    })
    .catch(error => {
        console.error('Search error:', error);
    });
}

function displaySearchResults(results, searchTerm) {
    // Remove existing results
    const existingResults = document.querySelector('.search-results');
    if (existingResults) {
        existingResults.remove();
    }
    
    const totalResults = Object.values(results).reduce((sum, arr) => sum + arr.length, 0);
    
    if (totalResults === 0) {
        return;
    }
    
    const searchContainer = document.querySelector('.header-search');
    const resultsDiv = document.createElement('div');
    resultsDiv.className = 'search-results';
    resultsDiv.innerHTML = `
        <div class="search-results-header">
            <span>Hasil pencarian untuk "${searchTerm}"</span>
            <small>${totalResults} hasil ditemukan</small>
        </div>
        <div class="search-results-body">
            ${renderSearchCategory('Cipher', results.ciphers)}
            ${renderSearchCategory('Modul Belajar', results.modules)}
            ${renderSearchCategory('Tantangan', results.challenges)}
            ${renderSearchCategory('Glossary', results.glossary)}
            ${renderSearchCategory('Video', results.videos)}
        </div>
        <div class="search-results-footer">
            <a href="/search?q=${encodeURIComponent(searchTerm)}">Lihat semua hasil</a>
        </div>
    `;
    
    searchContainer.appendChild(resultsDiv);
}

function renderSearchCategory(title, items) {
    if (items.length === 0) return '';
    
    const itemsHtml = items.map(item => `
        <a href="${item.url}" class="search-result-item">
            <div class="search-result-icon">
                <i class="fas fa-${getIconForType(item.type)}"></i>
            </div>
            <div class="search-result-content">
                <div class="search-result-title">${item.name}</div>
                ${item.category ? `<div class="search-result-meta">${item.category}</div>` : ''}
                ${item.cipher ? `<div class="search-result-meta">${item.cipher}</div>` : ''}
                ${item.instructor ? `<div class="search-result-meta">${item.instructor}</div>` : ''}
            </div>
        </a>
    `).join('');
    
    return `
        <div class="search-category">
            <div class="search-category-title">${title}</div>
            ${itemsHtml}
        </div>
    `;
}

function getIconForType(type) {
    const icons = {
        'cipher': 'fa-lock',
        'module': 'fa-book',
        'challenge': 'fa-flag',
        'glossary': 'fa-bookmark',
        'video': 'fa-play-circle'
    };
    return icons[type] || 'fa-search';
}

function hideSearchResults() {
    const existingResults = document.querySelector('.search-results');
    if (existingResults) {
        existingResults.remove();
    }
}

// Notifications Functions
function toggleNotificationsPanel() {
    const existingPanel = document.querySelector('.notifications-panel');
    
    if (existingPanel) {
        existingPanel.remove();
        return;
    }
    
    fetch('/api/notifications')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showNotificationsPanel(data.notifications, data.unread_count);
                markNotificationsAsRead();
            }
        })
        .catch(error => {
            console.error('Error loading notifications:', error);
            showNotificationsPanel([], 0);
        });
}

function showNotificationsPanel(notifications, unreadCount) {
    const panel = document.createElement('div');
    panel.className = 'notifications-panel';
    
    const notificationsHtml = notifications.length > 0 
        ? notifications.map(notif => `
            <div class="notification-item ${notif.is_read ? '' : 'unread'}" data-id="${notif.id}">
                <div class="notification-icon">
                    <i class="fas fa-${getNotificationIcon(notif.type)} text-${notif.type}"></i>
                </div>
                <div class="notification-content">
                    <div class="notification-title">${notif.title}</div>
                    <div class="notification-message">${notif.message}</div>
                    <div class="notification-time">${notif.time_ago}</div>
                </div>
                ${notif.link ? `<a href="${notif.link}" class="notification-link"><i class="fas fa-external-link-alt"></i></a>` : ''}
            </div>
        `).join('')
        : `<div class="notification-empty">Tidak ada notifikasi</div>`;
    
    panel.innerHTML = `
        <div class="notifications-header">
            <h6>Notifikasi</h6>
            <div class="notifications-actions">
                ${unreadCount > 0 ? `<button class="btn-mark-all-read" onclick="markAllNotificationsAsRead()">Tandai semua dibaca</button>` : ''}
                <button class="btn-clear-notifications" onclick="clearNotifications()">Hapus</button>
            </div>
        </div>
        <div class="notifications-body">
            ${notificationsHtml}
        </div>
        <div class="notifications-footer">
            <a href="/activity">Lihat semua aktivitas</a>
        </div>
    `;
    
    document.body.appendChild(panel);
    
    // Position panel
    const btn = document.getElementById('notificationsBtn');
    const rect = btn.getBoundingClientRect();
    panel.style.top = (rect.bottom + 5) + 'px';
    panel.style.right = (window.innerWidth - rect.right) + 'px';
    
    // Close panel when clicking outside
    setTimeout(() => {
        document.addEventListener('click', function closePanel(e) {
            if (!e.target.closest('.notifications-panel') && !e.target.closest('#notificationsBtn')) {
                panel.remove();
                document.removeEventListener('click', closePanel);
            }
        });
    }, 100);
}

function getNotificationIcon(type) {
    const icons = {
        'info': 'fa-info-circle',
        'success': 'fa-check-circle',
        'warning': 'fa-exclamation-triangle',
        'danger': 'fa-exclamation-circle'
    };
    return icons[type] || 'fa-bell';
}

function markNotificationsAsRead() {
    fetch('/api/notifications/mark-read', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ notification_id: 'all' })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            updateNotificationsBadge(0);
        }
    });
}

function markAllNotificationsAsRead() {
    fetch('/api/notifications/mark-read', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ notification_id: 'all' })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Reload notifications panel
            document.querySelector('.notifications-panel')?.remove();
            toggleNotificationsPanel();
        }
    });
}

function clearNotifications() {
    fetch('/api/notifications/clear', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Reload notifications panel
            document.querySelector('.notifications-panel')?.remove();
            toggleNotificationsPanel();
        }
    });
}

function loadNotificationsCount() {
    fetch('/api/notifications')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                updateNotificationsBadge(data.unread_count);
            }
        })
        .catch(error => {
            console.error('Error loading notifications count:', error);
        });
}

function updateNotificationsBadge(count) {
    const badge = document.querySelector('.notification-badge');
    if (badge) {
        badge.textContent = count;
        badge.style.display = count > 0 ? 'flex' : 'none';
    }
}

// Weather Functions
function loadWeatherData() {
    fetch('/api/weather')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                updateWeatherDisplay(data);
            }
        })
        .catch(error => {
            console.error('Error loading weather:', error);
        });
}

function updateWeatherDisplay(weather) {
    const weatherIcon = document.querySelector('.weather-info i');
    const weatherTemp = document.querySelector('.weather-info span');
    
    if (weatherIcon && weatherTemp) {
        weatherIcon.className = `fas ${weather.icon}`;
        weatherTemp.textContent = `${weather.temperature}°C`;
        
        // Add tooltip
        weatherIcon.title = `${weather.condition} di ${weather.location}`;
        weatherTemp.title = `Diperbarui: ${weather.updated_at}`;
    }
}

// Theme Functions
function toggleTheme() {
    const currentTheme = localStorage.getItem('theme') || 'light';
    const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
    
    setTheme(newTheme);
}

function setTheme(theme) {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('theme', theme);
    
    const themeIcon = document.querySelector('#themeToggle i');
    if (themeIcon) {
        themeIcon.className = theme === 'dark' ? 'fas fa-sun' : 'fas fa-moon';
    }
}

// Polling untuk notifikasi dan cuaca
setInterval(() => {
    loadNotificationsCount();
    loadWeatherData();
}, 300000); // Update setiap 5 menit