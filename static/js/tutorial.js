// Tutorial Data Structure
const tutorials = {
    'caesar-cipher': {
        title: 'Caesar Cipher: Cipher Pertama dalam Sejarah',
        difficulty: 'beginner',
        duration: '30 menit',
        tags: ['Substitusi', 'Sejarah', 'Python', 'Dasar'],
        description: 'Pelajari cipher substitusi paling terkenal yang digunakan Julius Caesar untuk komunikasi militer rahasia.',
        content: `
            <div class="tutorial-content">
                <h2>Caesar Cipher</h2>
                <p>Cipher substitusi sederhana di mana setiap huruf digeser sejumlah posisi tertentu dalam alfabet.</p>
                
                <h3>Google Search References:</h3>
                <div class="google-links">
                    <a href="https://en.wikipedia.org/wiki/Caesar_cipher" target="_blank" rel="noopener noreferrer">
                        <i class="fab fa-wikipedia-w"></i> Wikipedia - Caesar Cipher
                    </a>
                    <a href="https://www.khanacademy.org/computing/computer-science/cryptography/crypt/v/caesar-cipher" target="_blank" rel="noopener noreferrer">
                        <i class="fas fa-graduation-cap"></i> Khan Academy Video
                    </a>
                    <a href="https://www.geeksforgeeks.org/caesar-cipher-in-cryptography/" target="_blank" rel="noopener noreferrer">
                        <i class="fas fa-code"></i> GeeksforGeeks Implementation
                    </a>
                    <a href="https://www.youtube.com/watch?v=sMOZf4GN3oc" target="_blank" rel="noopener noreferrer">
                        <i class="fab fa-youtube"></i> Computerphile Explanation
                    </a>
                </div>
            </div>
        `
    },
    'vigenere-cipher': {
        title: 'Vigenère Cipher: Polialfabetik Pertama',
        difficulty: 'intermediate',
        duration: '45 menit',
        tags: ['Polialfabetik', 'Tabel', 'Python', 'Analisis'],
        description: 'Pahami tabel Vigenère dan sistem polialfabetik yang menjadi evolusi dari cipher substitusi sederhana.',
        content: `
            <div class="tutorial-content">
                <h2>Vigenère Cipher</h2>
                <p>Cipher polialfabetik yang menggunakan serangkaian Caesar ciphers berdasarkan huruf-huruf dalam keyword.</p>
                
                <h3>Google Search References:</h3>
                <div class="google-links">
                    <a href="https://en.wikipedia.org/wiki/Vigen%C3%A8re_cipher" target="_blank" rel="noopener noreferrer">
                        <i class="fab fa-wikipedia-w"></i> Wikipedia - Vigenère Cipher
                    </a>
                    <a href="https://www.youtube.com/watch?v=SkJcmCaHqS0" target="_blank" rel="noopener noreferrer">
                        <i class="fab fa-youtube"></i> 3Blue1Brown Explanation
                    </a>
                    <a href="https://cryptii.com/pipes/vigenere-cipher" target="_blank" rel="noopener noreferrer">
                        <i class="fas fa-tools"></i> Online Vigenère Tool
                    </a>
                    <a href="https://www.cs.uri.edu/cryptography/classicalvigenere.htm" target="_blank" rel="noopener noreferrer">
                        <i class="fas fa-university"></i> University of Rhode Island Tutorial
                    </a>
                </div>
            </div>
        `
    },
    'rsa-encryption': {
        title: 'RSA Encryption: Kriptografi Kunci Publik',
        difficulty: 'advanced',
        duration: '90 menit',
        tags: ['Asimetris', 'Kunci Publik', 'Matematika', 'Python'],
        description: 'Pelajari matematika di balik RSA, algoritma yang mengamankan internet modern.',
        content: `
            <div class="tutorial-content">
                <h2>RSA Encryption</h2>
                <p>Algoritma kriptografi kunci publik yang digunakan untuk enkripsi dan tanda tangan digital.</p>
                
                <h3>Google Search References:</h3>
                <div class="google-links">
                    <a href="https://en.wikipedia.org/wiki/RSA_(cryptosystem)" target="_blank" rel="noopener noreferrer">
                        <i class="fab fa-wikipedia-w"></i> Wikipedia - RSA Cryptosystem
                    </a>
                    <a href="https://www.youtube.com/watch?v=wXB-V_Keiu8" target="_blank" rel="noopener noreferrer">
                        <i class="fab fa-youtube"></i> RSA Explained
                    </a>
                    <a href="https://cryptobook.nakov.com/asymmetric-key-ciphers/rsa-encrypt-decrypt-examples" target="_blank" rel="noopener noreferrer">
                        <i class="fas fa-book"></i> Practical Cryptography
                    </a>
                    <a href="https://www.di-mgt.com.au/rsa_alg.html" target="_blank" rel="noopener noreferrer">
                        <i class="fas fa-calculator"></i> RSA Algorithm Details
                    </a>
                </div>
            </div>
        `
    },
    'frequency-analysis': {
        title: 'Frequency Analysis: Memecahkan Substitusi',
        difficulty: 'intermediate',
        duration: '40 menit',
        tags: ['Analisis', 'Statistik', 'Python', 'Visualisasi'],
        description: 'Gunakan analisis statistik karakter untuk memecahkan cipher substitusi tanpa mengetahui kunci.',
        content: `
            <div class="tutorial-content">
                <h2>Frequency Analysis</h2>
                <p>Teknik kriptanalisis yang menganalisis frekuensi kemunculan huruf dalam teks terenkripsi.</p>
                
                <h3>Google Search References:</h3>
                <div class="google-links">
                    <a href="https://en.wikipedia.org/wiki/Frequency_analysis" target="_blank" rel="noopener noreferrer">
                        <i class="fab fa-wikipedia-w"></i> Wikipedia - Frequency Analysis
                    </a>
                    <a href="https://www.youtube.com/watch?v=LaWp_Kq0cKs" target="_blank" rel="noopener noreferrer">
                        <i class="fab fa-youtube"></i> Computerphile Explanation
                    </a>
                </div>
            </div>
        `
    },
    'hash-functions': {
        title: 'Hash Functions: Keamanan Password & Integritas Data',
        difficulty: 'intermediate',
        duration: '55 menit',
        tags: ['Hash', 'Password', 'Blockchain', 'Keamanan'],
        description: 'Pelajari MD5, SHA-256, bcrypt, dan aplikasinya dalam keamanan password, digital signatures, dan blockchain.',
        content: `
            <div class="tutorial-content">
                <h2>Hash Functions</h2>
                <p>Fungsi satu arah yang mengubah data menjadi nilai hash dengan panjang tetap.</p>
                
                <h3>Google Search References:</h3>
                <div class="google-links">
                    <a href="https://en.wikipedia.org/wiki/Cryptographic_hash_function" target="_blank" rel="noopener noreferrer">
                        <i class="fab fa-wikipedia-w"></i> Wikipedia - Cryptographic Hash Function
                    </a>
                </div>
            </div>
        `
    },
    'blockchain-crypto': {
        title: 'Kriptografi dalam Blockchain & Cryptocurrency',
        difficulty: 'advanced',
        duration: '75 menit',
        tags: ['Blockchain', 'Bitcoin', 'Cryptocurrency', 'Hash'],
        description: 'Pahami cryptographic hash functions, digital signatures, dan consensus algorithms yang mendukung Bitcoin dan Ethereum.',
        content: `
            <div class="tutorial-content">
                <h2>Blockchain Cryptography</h2>
                <p>Penerapan kriptografi dalam teknologi blockchain dan cryptocurrency.</p>
                
                <h3>Google Search References:</h3>
                <div class="google-links">
                    <a href="https://en.wikipedia.org/wiki/Blockchain" target="_blank" rel="noopener noreferrer">
                        <i class="fab fa-wikipedia-w"></i> Wikipedia - Blockchain
                    </a>
                </div>
            </div>
        `
    }
};

// Global Variables
let currentTutorial = null;
let isPremiumUser = false;

// Check Premium Status
function checkPremiumStatus() {
    const premium = localStorage.getItem('decoDify_premium');
    isPremiumUser = premium === 'true';
}

// Open Tutorial
function openTutorial(tutorialId) {
    const tutorial = tutorials[tutorialId];
    if (!tutorial) return;
    
    currentTutorial = tutorialId;
    
    const modal = document.getElementById('tutorialModal');
    const modalBody = document.getElementById('modalBody');
    
    modalBody.innerHTML = `
        <div class="tutorial-header">
            <h2 style="color: var(--text);">${tutorial.title}</h2>
            <div class="tutorial-meta">
                <span class="difficulty-badge difficulty-${tutorial.difficulty}">
                    ${tutorial.difficulty === 'beginner' ? 'Pemula' : 
                      tutorial.difficulty === 'intermediate' ? 'Menengah' : 'Lanjutan'}
                </span>
                <span class="meta-item">
                    <i class="fas fa-clock"></i> ${tutorial.duration}
                </span>
            </div>
        </div>
        
        <div class="tutorial-description" style="margin: 1.5rem 0;">
            <p style="color: var(--text-muted);">${tutorial.description}</p>
        </div>
        
        ${tutorial.content}
        
        <div class="tutorial-actions" style="margin-top: 2rem; display: flex; gap: 1rem;">
            <button class="view-tutorial-btn" onclick="startTutorial('${tutorialId}')">
                <i class="fas fa-play"></i> Mulai Tutorial
            </button>
            <button class="btn-secondary" onclick="searchGoogleReferences('${tutorialId}')" style="background: rgba(255,255,255,0.1); border: 1px solid var(--glass); padding: 0.75rem 1.5rem; border-radius: 10px; color: var(--text);">
                <i class="fab fa-google"></i> Cari Referensi di Google
            </button>
        </div>
    `;
    
    modal.style.display = 'flex';
    document.body.style.overflow = 'hidden';
}

// Open Premium Tutorial
function openPremiumTutorial(tutorialId) {
    if (!isPremiumUser) {
        showUpgradeModal();
        return;
    }
    openTutorial(tutorialId);
}

// Close Modal
function closeModal() {
    const modal = document.getElementById('tutorialModal');
    modal.style.display = 'none';
    document.body.style.overflow = 'auto';
}

// Start Tutorial
function startTutorial(tutorialId) {
    showToast(`Memulai tutorial: ${tutorials[tutorialId].title}`, 'success');
    closeModal();
    // In real app: window.location.href = `/tutorial/${tutorialId}/start`;
}

// Search Google References
function searchGoogleReferences(tutorialId) {
    const tutorial = tutorials[tutorialId];
    const searchQuery = encodeURIComponent(tutorial.title + ' cryptography tutorial');
    window.open(`https://www.google.com/search?q=${searchQuery}`, '_blank');
}

// Handle Search
function handleSearch(event) {
    if (event.key === 'Enter') {
        const searchTerm = document.getElementById('searchTutorials').value;
        if (searchTerm.trim()) {
            filterTutorials(searchTerm.toLowerCase());
            trackTutorialSearch(searchTerm);
        }
    }
}

// Search Tutorial from hint
function searchTutorial(term) {
    document.getElementById('searchTutorials').value = term;
    filterTutorials(term.toLowerCase());
    trackTutorialSearch(term);
}

// Search Google from input
function searchGoogle(event) {
    if (event.key === 'Enter') {
        const searchTerm = document.getElementById('googleSearch').value;
        if (searchTerm.trim()) {
            const query = encodeURIComponent(searchTerm + ' cryptography');
            window.open(`https://www.google.com/search?q=${query}`, '_blank');
        }
    }
}

// Filter Tutorials
function filterTutorials(searchTerm) {
    const tutorialCards = document.querySelectorAll('.tutorial-card');
    let found = false;
    
    tutorialCards.forEach(card => {
        const title = card.querySelector('h3').textContent.toLowerCase();
        const description = card.querySelector('p').textContent.toLowerCase();
        const tags = Array.from(card.querySelectorAll('.tutorial-tag')).map(tag => tag.textContent.toLowerCase());
        
        if (title.includes(searchTerm) || 
            description.includes(searchTerm) || 
            tags.some(tag => tag.includes(searchTerm))) {
            card.style.display = 'block';
            card.style.animation = 'slideUp 0.5s ease';
            found = true;
        } else {
            card.style.display = 'none';
        }
    });
    
    if (!found) {
        showNoResultsMessage(searchTerm);
    }
}

// Show No Results Message
function showNoResultsMessage(searchTerm) {
    const modal = document.getElementById('tutorialModal');
    const modalBody = document.getElementById('modalBody');
    
    modalBody.innerHTML = `
        <div class="no-results" style="text-align: center; padding: 2rem;">
            <i class="fas fa-search" style="font-size: 3rem; color: var(--text-muted); margin-bottom: 1rem;"></i>
            <h3 style="color: var(--text);">Tidak ada hasil untuk "${searchTerm}"</h3>
            <p style="color: var(--text-muted);">Mungkin tutorial ini belum tersedia. Coba cari di Google untuk referensi:</p>
            <div class="google-search-suggestion" style="margin: 1.5rem 0;">
                <a href="https://www.google.com/search?q=${encodeURIComponent(searchTerm + ' cryptography tutorial')}" 
                   target="_blank" 
                   rel="noopener noreferrer"
                   class="view-tutorial-btn" style="display: inline-flex;">
                    <i class="fab fa-google"></i> Cari di Google
                </a>
            </div>
            <p class="suggestion" style="color: var(--text-muted); font-size: 0.9rem;">Saran: Coba dengan kata kunci: "caesar cipher", "RSA", "AES", "hash functions"</p>
        </div>
    `;
    
    modal.style.display = 'flex';
}

// Show Upgrade Modal
function showUpgradeModal() {
    const modal = document.getElementById('tutorialModal');
    const modalBody = document.getElementById('modalBody');
    
    modalBody.innerHTML = `
        <div class="upgrade-prompt" style="text-align: center; padding: 2rem;">
            <i class="fas fa-crown" style="font-size: 3rem; background: linear-gradient(135deg, #f59e0b, #d97706); -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin-bottom: 1rem;"></i>
            <h3 style="color: var(--text);">Akses Tutorial Premium</h3>
            <p style="color: var(--text-muted);">Upgrade ke DecoDify Premium untuk mengakses semua tutorial lanjutan:</p>
            <ul class="premium-features" style="list-style: none; padding: 0; margin: 1.5rem 0;">
                <li style="padding: 0.5rem 0; color: var(--text); display: flex; align-items: center; gap: 0.5rem; justify-content: center;">
                    <i class="fas fa-check" style="color: #f59e0b;"></i> RSA, AES, Diffie-Hellman
                </li>
                <li style="padding: 0.5rem 0; color: var(--text); display: flex; align-items: center; gap: 0.5rem; justify-content: center;">
                    <i class="fas fa-check" style="color: #f59e0b;"></i> Blockchain Cryptography
                </li>
                <li style="padding: 0.5rem 0; color: var(--text); display: flex; align-items: center; gap: 0.5rem; justify-content: center;">
                    <i class="fas fa-check" style="color: #f59e0b;"></i> Advanced Cryptanalysis
                </li>
                <li style="padding: 0.5rem 0; color: var(--text); display: flex; align-items: center; gap: 0.5rem; justify-content: center;">
                    <i class="fas fa-check" style="color: #f59e0b;"></i> Video Course Premium
                </li>
            </ul>
            <div class="upgrade-actions" style="display: flex; gap: 1rem; justify-content: center; margin-top: 2rem;">
                <button class="view-tutorial-btn premium" onclick="window.location.href='{{ url_for('premium.upgrade') }}'">
                    <i class="fas fa-crown"></i> Upgrade Sekarang
                </button>
                <button class="btn-secondary" onclick="closeModal()" style="background: rgba(255,255,255,0.1); border: 1px solid var(--glass); padding: 0.75rem 1.5rem; border-radius: 10px; color: var(--text);">
                    Nanti Saja
                </button>
            </div>
        </div>
    `;
    
    modal.style.display = 'flex';
}

// Track tutorial searches
function trackTutorialSearch(searchTerm) {
    console.log('Search:', searchTerm);
    // Send to analytics in real app
}

// Toast function (jika tidak ada di base.html)
function showToast(message, type = 'success') {
    // Gunakan toast dari base.js jika ada
    if (typeof window.showToast === 'function') {
        window.showToast(message, type);
        return;
    }
    
    // Fallback toast
    const toastContainer = document.getElementById('toastContainer') || createToastContainer();
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.innerHTML = `
        <div class="toast-icon">
            <i class="fas fa-${type === 'success' ? 'check-circle' : type === 'warning' ? 'exclamation-triangle' : 'exclamation-circle'}"></i>
        </div>
        <div class="toast-content">
            <p>${message}</p>
        </div>
        <button class="toast-close">
            <i class="fas fa-times"></i>
        </button>
    `;
    
    toastContainer.appendChild(toast);
    
    setTimeout(() => {
        toast.classList.add('show');
    }, 10);
    
    setTimeout(() => {
        toast.classList.remove('show');
        setTimeout(() => {
            toast.remove();
        }, 300);
    }, 5000);
    
    toast.querySelector('.toast-close').addEventListener('click', function() {
        toast.classList.remove('show');
        setTimeout(() => {
            toast.remove();
        }, 300);
    });
}

// Create toast container if not exists
function createToastContainer() {
    const container = document.createElement('div');
    container.id = 'toastContainer';
    container.className = 'toast-container';
    document.body.appendChild(container);
    return container;
}

// Initialize
document.addEventListener('DOMContentLoaded', function() {
    checkPremiumStatus();
    
    // Close modal on outside click
    const modal = document.getElementById('tutorialModal');
    if (modal) {
        modal.addEventListener('click', function(e) {
            if (e.target === this) {
                closeModal();
            }
        });
    }
    
    // Add click animations to cards
    document.querySelectorAll('.tutorial-card').forEach(card => {
        card.addEventListener('click', function() {
            this.style.transform = 'scale(0.98)';
            setTimeout(() => {
                this.style.transform = '';
            }, 150);
        });
    });

    // Track external link clicks
    document.querySelectorAll('a[target="_blank"]').forEach(link => {
        link.addEventListener('click', function() {
            console.log('External link clicked:', this.href);
            // Analytics tracking bisa ditambahkan di sini
        });
    });
});

// Add additional styles for modal
const styleSheet = document.createElement('style');
styleSheet.textContent = `
    .google-links {
        display: flex;
        flex-direction: column;
        gap: 1rem;
        margin: 1.5rem 0;
    }
    
    .google-links a {
        display: flex;
        align-items: center;
        gap: 0.75rem;
        padding: 1rem;
        background: rgba(66, 133, 244, 0.1);
        border: 1px solid rgba(66, 133, 244, 0.2);
        border-radius: 10px;
        color: var(--text);
        text-decoration: none;
        transition: all 0.3s ease;
    }
    
    .google-links a:hover {
        background: rgba(66, 133, 244, 0.2);
        transform: translateX(5px);
    }
    
    .google-links i {
        font-size: 1.2rem;
        color: #4285F4;
    }
    
    .dark-theme .google-links a {
        background: rgba(66, 133, 244, 0.15);
        border-color: rgba(66, 133, 244, 0.3);
    }
`;
document.head.appendChild(styleSheet);