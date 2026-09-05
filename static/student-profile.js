// Student Profile JavaScript

let allAssessments = []; // Store all assessments for filtering
let performanceTrendChart = null; // Store chart instance

document.addEventListener('DOMContentLoaded', function() {
    loadProfileData();
    setupEditModeHandlers();
    setupFormHandlers();
    setupPhotoUpload();
    loadFaculties();
});

// Load profile data
async function loadProfileData() {
    try {
        console.log('Loading profile data...');
        const response = await fetch('/api/student/profile');
        
        console.log('Response status:', response.status);
        
        if (response.status === 401) {
            console.error('Not authenticated');
            showError('Please log in to view your profile');
            window.location.href = '/login';
            return;
        }
        
        if (!response.ok) {
            const errorData = await response.json();
            console.error('API Error:', errorData);
            showError('Failed to load profile: ' + (errorData.error || 'Unknown error'));
            return;
        }

        const data = await response.json();
        console.log('Profile data received:', data);
        console.log('Profile object:', data.profile);
        console.log('Profile name:', data.profile.name);
        console.log('Profile email:', data.profile.email);

        if (data.status === 'ok') {
            populateProfileData(data);
        } else {
            showError('Failed to load profile: ' + (data.error || 'Unknown error'));
        }
    } catch (err) {
        console.error('Error loading profile:', err);
        showError('Unable to load profile data: ' + err.message);
    }
}

// Populate profile data in forms and view
function populateProfileData(data) {
    const profile = data.profile;
    const stats = data.statistics || {};

    console.log('Populating profile data:', profile);
    console.log('Statistics:', stats);

    // Display in view mode FIRST (before form filling)
    console.log('Setting displayName to:', profile.name);
    if (document.getElementById('displayName')) {
        document.getElementById('displayName').textContent = profile.name || '-';
        console.log('✓ displayName updated to:', document.getElementById('displayName').textContent);
    } else {
        console.warn('✗ displayName element NOT found!');
    }

    if (document.getElementById('displayEmail')) {
        document.getElementById('displayEmail').textContent = profile.email || '-';
        console.log('✓ displayEmail updated to:', document.getElementById('displayEmail').textContent);
    } else {
        console.warn('✗ displayEmail element NOT found!');
    }

    if (document.getElementById('displayContact')) {
        document.getElementById('displayContact').textContent = profile.contact || '-';
        console.log('✓ displayContact updated to:', document.getElementById('displayContact').textContent);
    } else {
        console.warn('✗ displayContact element NOT found!');
    }

    if (document.getElementById('displayClass')) {
        document.getElementById('displayClass').textContent = profile.class || '-';
        console.log('✓ displayClass updated to:', document.getElementById('displayClass').textContent);
    } else {
        console.warn('✗ displayClass element NOT found!');
    }

    if (document.getElementById('displayFaculty')) {
        document.getElementById('displayFaculty').textContent = profile.faculty_name || '-';
        console.log('✓ displayFaculty updated to:', document.getElementById('displayFaculty').textContent);
    } else {
        console.warn('✗ displayFaculty element NOT found!');
    }

    // Fill forms
    if (document.getElementById('fullName')) {
        document.getElementById('fullName').value = profile.name || '';
    }
    if (document.getElementById('email')) {
        document.getElementById('email').value = profile.email || '';
    }
    if (document.getElementById('contact')) {
        document.getElementById('contact').value = profile.contact || '';
    }
    if (document.getElementById('class')) {
        document.getElementById('class').value = profile.class || '';
    }
    if (document.getElementById('faculty')) {
        document.getElementById('faculty').value = profile.faculty_id || '';
    }

    // Update stats with null checks
    const totalAssessments = stats.total_assessments || 0;
    const avgScore = stats.average_score || 0;
    const disordersAttempted = stats.disorders_attempted || 0;

    if (document.getElementById('totalAssessmentsStat')) {
        document.getElementById('totalAssessmentsStat').textContent = totalAssessments;
    }
    if (document.getElementById('averageScoreStat')) {
        document.getElementById('averageScoreStat').textContent = avgScore > 0 ? avgScore.toFixed(1) + '%' : '0%';
    }
    if (document.getElementById('disordersStat')) {
        document.getElementById('disordersStat').textContent = disordersAttempted;
    }

    // Update summary view
    if (document.getElementById('summaryAssessments')) {
        document.getElementById('summaryAssessments').textContent = totalAssessments;
    }
    if (document.getElementById('summaryAvgScore')) {
        document.getElementById('summaryAvgScore').textContent = avgScore > 0 ? avgScore.toFixed(1) + '%' : '0%';
    }
    if (document.getElementById('summaryDisorders')) {
        document.getElementById('summaryDisorders').textContent = disordersAttempted;
    }

    // Update performance indicator
    updatePerformanceIndicator(avgScore, totalAssessments);

    // Update achievement badges
    updateAchievementBadges(stats);

    // Update profile photo
    if (profile.profile_photo && document.getElementById('profilePhotoImg')) {
        document.getElementById('profilePhotoImg').src = profile.profile_photo;
    }

    // Populate disorder breakdown
    populateDisorderBreakdown(data.disorder_breakdown || []);
}

// Populate profile data in forms and view
function populateProfileData(data) {
    const profile = data.profile;
    const stats = data.statistics || {};

    console.log('Populating profile data:', profile);
    console.log('Statistics:', stats);

    // Fill forms
    if (document.getElementById('fullName')) {
        document.getElementById('fullName').value = profile.name || '';
    }
    if (document.getElementById('email')) {
        document.getElementById('email').value = profile.email || '';
    }
    if (document.getElementById('contact')) {
        document.getElementById('contact').value = profile.contact || '';
    }
    if (document.getElementById('class')) {
        document.getElementById('class').value = profile.class || '';
    }
    if (document.getElementById('faculty')) {
        document.getElementById('faculty').value = profile.faculty_id || '';
    }

    // Display in view mode
    if (document.getElementById('displayName')) {
        document.getElementById('displayName').textContent = profile.name || '-';
    }
    if (document.getElementById('displayEmail')) {
        document.getElementById('displayEmail').textContent = profile.email || '-';
    }
    if (document.getElementById('displayContact')) {
        document.getElementById('displayContact').textContent = profile.contact || '-';
    }
    if (document.getElementById('displayClass')) {
        document.getElementById('displayClass').textContent = profile.class || '-';
    }
    if (document.getElementById('displayFaculty')) {
        document.getElementById('displayFaculty').textContent = profile.faculty_name || '-';
    }

    // Update stats with null checks
    const totalAssessments = stats.total_assessments || 0;
    const avgScore = stats.average_score || 0;
    const disordersAttempted = stats.disorders_attempted || 0;

    if (document.getElementById('totalAssessmentsStat')) {
        document.getElementById('totalAssessmentsStat').textContent = totalAssessments;
    }
    if (document.getElementById('averageScoreStat')) {
        document.getElementById('averageScoreStat').textContent = avgScore > 0 ? avgScore.toFixed(1) + '%' : '0%';
    }
    if (document.getElementById('disordersStat')) {
        document.getElementById('disordersStat').textContent = disordersAttempted;
    }

    // Update summary view
    if (document.getElementById('summaryAssessments')) {
        document.getElementById('summaryAssessments').textContent = totalAssessments;
    }
    if (document.getElementById('summaryAvgScore')) {
        document.getElementById('summaryAvgScore').textContent = avgScore > 0 ? avgScore.toFixed(1) + '%' : '0%';
    }
    if (document.getElementById('summaryDisorders')) {
        document.getElementById('summaryDisorders').textContent = disordersAttempted;
    }

    // Update performance indicator
    updatePerformanceIndicator(avgScore, totalAssessments);

    // Update achievement badges
    updateAchievementBadges(stats);

    // Update profile photo
    if (profile.profile_photo && document.getElementById('profilePhotoImg')) {
        document.getElementById('profilePhotoImg').src = profile.profile_photo;
    }

    // Populate disorder breakdown
    populateDisorderBreakdown(data.disorder_breakdown || []);
}

// Populate disorder breakdown
function populateDisorderBreakdown(disorders) {
    const container = document.getElementById('disorderList');
    
    if (!container) {
        console.warn('Disorder list container not found');
        return;
    }

    console.log('Populating disorder breakdown:', disorders);

    const defaultDisorders = [
        { disorder: 'dyslexia', assessment_id: 1, attempts: 0, best_score: 0, average_score: 0 },
        { disorder: 'dyscalculia', assessment_id: 2, attempts: 0, best_score: 0, average_score: 0 },
        { disorder: 'dysgraphia', assessment_id: 3, attempts: 0, best_score: 0, average_score: 0 }
    ];

    const map = {};
    (disorders || []).forEach(d => {
        const key = (d.disorder || d.disorder_type || '').toLowerCase();
        if (key) map[key] = d;
    });

    const displayList = defaultDisorders.map(def => {
        const key = def.disorder.toLowerCase();
        return map[key] ? { ...def, ...map[key] } : def;
    });

    container.innerHTML = displayList.map(d => {
        const dType = (d.disorder || d.disorder_type || 'dyslexia').toLowerCase();
        const dName = capitalizeDisorder(dType);
        const attempts = d.attempts || 0;
        const best = typeof d.best_score === 'number' ? d.best_score.toFixed(1) : Number(d.best_score || 0).toFixed(1);
        const avg = typeof d.average_score === 'number' ? d.average_score.toFixed(1) : Number(d.average_score || 0).toFixed(1);
        const aid = d.assessment_id || (dType === 'dyslexia' ? 1 : (dType === 'dyscalculia' ? 2 : 3));
        
        return `
        <div class="disorder-item" style="cursor: pointer; transition: all 0.2s ease; margin-bottom: 10px;" onclick="window.location.href='/assessment/${aid}'" title="Click to take or view ${dName} assessment">
            <div>
                <div class="disorder-name" style="color: #4facfe; font-weight: 600;">${dName} ➔</div>
                <div class="disorder-attempts">${attempts} attempt(s) • Best: ${best}%</div>
            </div>
            <div style="text-align: right; font-size: 0.9rem; color: #00f2fe; font-weight: 600;">
                Avg: ${avg}%
            </div>
        </div>`;
    }).join('') + `
    <div style="margin-top: 15px; text-align: center;">
        <a href="/assessments" class="btn btn-primary" style="display: block; text-decoration: none; padding: 10px 14px; border-radius: 8px; font-weight: 600; text-align: center;">🎯 Take An Assessment</a>
    </div>`;
}

// Update performance indicator
function updatePerformanceIndicator(avgScore, totalAssessments) {
    const performanceFill = document.getElementById('performanceFill');
    const performanceText = document.getElementById('performanceText');

    if (!performanceFill || !performanceText) return;

    const percentage = Math.min(avgScore || 0, 100);
    performanceFill.style.width = percentage + '%';

    if (totalAssessments === 0) {
        performanceText.textContent = 'Get started with your first assessment!';
    } else if (avgScore >= 90) {
        performanceText.textContent = '🌟 Outstanding! Keep up the excellent work!';
    } else if (avgScore >= 80) {
        performanceText.textContent = '⭐ Excellent progress! You\'re on the right track!';
    } else if (avgScore >= 70) {
        performanceText.textContent = '👍 Good job! Keep practicing to improve further!';
    } else if (avgScore >= 50) {
        performanceText.textContent = '💪 You\'re making progress! Keep going!';
    } else {
        performanceText.textContent = '📚 Keep practicing! Every assessment helps you improve!';
    }
}

// Update achievement badges
function updateAchievementBadges(stats) {
    const badgesContainer = document.getElementById('badgesContainer');
    if (!badgesContainer) return;

    const totalAssessments = stats.total_assessments || 0;
    const avgScore = stats.average_score || 0;
    const disordersAttempted = stats.disorders_attempted || 0;

    // Clear and rebuild badges
    badgesContainer.innerHTML = '';

    // Badge 1: First Assessment
    const starterBadge = document.createElement('div');
    starterBadge.className = totalAssessments > 0 ? 'badge unlocked' : 'badge locked';
    starterBadge.title = 'Complete your first assessment';
    starterBadge.innerHTML = '<span class="badge-icon">🎯</span><span class="badge-name">Starter</span>';
    badgesContainer.appendChild(starterBadge);

    // Badge 2: Excellent Score
    const excellentBadge = document.createElement('div');
    excellentBadge.className = avgScore >= 80 ? 'badge unlocked' : 'badge locked';
    excellentBadge.title = 'Score 80% or higher';
    excellentBadge.innerHTML = '<span class="badge-icon">⭐</span><span class="badge-name">Excellent</span>';
    badgesContainer.appendChild(excellentBadge);

    // Badge 3: Master All Disorders
    const masterBadge = document.createElement('div');
    masterBadge.className = disordersAttempted >= 3 ? 'badge unlocked' : 'badge locked';
    masterBadge.title = 'Complete all 3 disorder assessments';
    masterBadge.innerHTML = '<span class="badge-icon">🏆</span><span class="badge-name">Master</span>';
    badgesContainer.appendChild(masterBadge);

    // Badge 4: Perfect Score
    const perfectBadge = document.createElement('div');
    perfectBadge.className = avgScore === 100 ? 'badge unlocked' : 'badge locked';
    perfectBadge.title = 'Achieve a perfect 100% score';
    perfectBadge.innerHTML = '<span class="badge-icon">👑</span><span class="badge-name">Perfect</span>';
    badgesContainer.appendChild(perfectBadge);
}

// Setup edit mode handlers
function setupEditModeHandlers() {
    // Edit buttons
    document.querySelectorAll('.btn-edit').forEach(btn => {
        btn.addEventListener('click', function() {
            const section = this.dataset.section;
            enterEditMode(section);
        });
    });

    // Form submission handlers
    if (document.getElementById('personalForm')) {
        document.getElementById('personalForm').addEventListener('submit', async function(e) {
            e.preventDefault();
            await updatePersonalInfo();
        });
    }

    if (document.getElementById('academicForm')) {
        document.getElementById('academicForm').addEventListener('submit', async function(e) {
            e.preventDefault();
            await updateAcademicInfo();
        });
    }

    if (document.getElementById('securityForm')) {
        document.getElementById('securityForm').addEventListener('submit', async function(e) {
            e.preventDefault();
            await changePassword();
        });
    }
}

// Enter edit mode for a section
function enterEditMode(section) {
    const viewMode = document.getElementById('viewMode');
    const editMode = document.getElementById('editMode');
    const editForms = document.querySelectorAll('.edit-form');

    if (viewMode && editMode) {
        viewMode.classList.remove('active');
        editMode.classList.add('active');

        // Hide all forms
        editForms.forEach(form => form.classList.remove('active'));

        // Show selected form
        const formId = 'edit' + section.charAt(0).toUpperCase() + section.slice(1) + 'Form';
        const form = document.getElementById(formId);
        if (form) {
            form.style.display = 'block';
            form.classList.add('active');
        }
    }
}

// Cancel edit mode
function cancelEdit() {
    const viewMode = document.getElementById('viewMode');
    const editMode = document.getElementById('editMode');
    const editForms = document.querySelectorAll('.edit-form');

    if (viewMode && editMode) {
        editMode.classList.remove('active');
        viewMode.classList.add('active');

        // Hide all forms
        editForms.forEach(form => {
            form.classList.remove('active');
            form.style.display = 'none';
        });

        // Reload to reset form values
        loadProfileData();
    }
}

// Load faculties for dropdown
async function loadFaculties() {
    try {
        console.log('Loading faculties...');
        const response = await fetch('/api/faculties');
        
        if (!response.ok) {
            console.error('Failed to load faculties:', response.status);
            return;
        }

        const data = await response.json();
        console.log('Faculties loaded:', data);

        if (data.faculties && Array.isArray(data.faculties)) {
            const facultySelect = document.getElementById('faculty');
            
            if (!facultySelect) {
                console.warn('Faculty select element not found');
                return;
            }

            const currentFacultyId = facultySelect.value;

            // Clear existing options except the first one
            while (facultySelect.options.length > 1) {
                facultySelect.remove(1);
            }

            data.faculties.forEach(f => {
                const option = document.createElement('option');
                option.value = f.id;
                option.textContent = f.name;
                facultySelect.appendChild(option);
            });

            facultySelect.value = currentFacultyId || '';
        }
    } catch (err) {
        console.error('Error loading faculties:', err);
    }
}

// Update personal information
async function updatePersonalInfo() {
    const name = document.getElementById('fullName').value.trim();
    const email = document.getElementById('email').value.trim();
    const contact = document.getElementById('contact').value.trim();

    if (!name || !email) {
        showError('Name and email are required');
        return;
    }

    console.log('Updating personal info:', { name, email, contact });

    try {
        const response = await fetch('/api/student/profile', {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ name, email, contact })
        });

        const data = await response.json();
        console.log('Update response:', data);

        if (response.ok) {
            showSuccess('Personal information updated successfully');
            loadProfileData();
            cancelEdit();
        } else {
            showError(data.error || 'Failed to update information');
        }
    } catch (err) {
        console.error('Error updating personal info:', err);
        showError('Unable to update profile: ' + err.message);
    }
}

// Update academic information
async function updateAcademicInfo() {
    const classValue = document.getElementById('class').value.trim();
    const facultyId = document.getElementById('faculty').value;

    try {
        const response = await fetch('/api/student/profile', {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                class: classValue,
                faculty_id: facultyId || null
            })
        });

        const data = await response.json();

        if (response.ok) {
            showSuccess('Academic information updated successfully');
            loadProfileData();
            cancelEdit();
        } else {
            showError(data.error || 'Failed to update information');
        }
    } catch (err) {
        console.error('Error updating academic info:', err);
        showError('Unable to update profile');
    }
}

// Change password
async function changePassword() {
    const currentPassword = document.getElementById('currentPassword').value;
    const newPassword = document.getElementById('newPassword').value;
    const confirmPassword = document.getElementById('confirmPassword').value;

    if (!currentPassword || !newPassword || !confirmPassword) {
        showError('All fields are required');
        return;
    }

    if (newPassword.length < 8) {
        showError('Password must be at least 8 characters long');
        return;
    }

    if (newPassword !== confirmPassword) {
        showError('Passwords do not match');
        return;
    }

    try {
        const response = await fetch('/api/update-password', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                current_password: currentPassword,
                new_password: newPassword
            })
        });

        const data = await response.json();

        if (response.ok) {
            showSuccess('Password changed successfully');
            document.getElementById('securityForm').reset();
            cancelEdit();
        } else {
            showError(data.error || 'Failed to change password');
        }
    } catch (err) {
        console.error('Error changing password:', err);
        showError('Unable to change password');
    }
}

// Enhanced photo upload with progress tracking
function setupPhotoUpload() {
    const uploadBtn = document.getElementById('uploadPhotoBtn');
    const photoInput = document.getElementById('photoInput');
    const photoProgress = document.getElementById('photoProgress');

    if (!uploadBtn) return;

    uploadBtn.addEventListener('click', function() {
        photoInput.click();
    });

    photoInput.addEventListener('change', async function(e) {
        const file = e.target.files[0];
        if (!file) return;

        // Validate file size (max 5MB)
        if (file.size > 5 * 1024 * 1024) {
            showError('File size must be less than 5MB');
            return;
        }

        // Validate file type
        if (!file.type.startsWith('image/')) {
            showError('Please select a valid image file');
            return;
        }

        // Show progress
        if (photoProgress) {
            photoProgress.style.display = 'block';
        }

        // Upload file with progress
        const formData = new FormData();
        formData.append('photo', file);

        try {
            const xhr = new XMLHttpRequest();

            // Track progress
            xhr.upload.addEventListener('progress', function(e) {
                if (e.lengthComputable && photoProgress) {
                    const percentComplete = (e.loaded / e.total) * 100;
                    const progressFill = photoProgress.querySelector('.progress-fill');
                    if (progressFill) {
                        progressFill.style.width = percentComplete + '%';
                    }
                }
            });

            // Handle completion
            xhr.addEventListener('load', function() {
                if (photoProgress) {
                    photoProgress.style.display = 'none';
                }

                if (xhr.status === 200) {
                    const response = JSON.parse(xhr.responseText);
                    showSuccess('Profile photo updated successfully');
                    loadProfileData();
                } else {
                    const response = JSON.parse(xhr.responseText);
                    showError(response.error || 'Failed to upload photo');
                }
            });

            // Handle error
            xhr.addEventListener('error', function() {
                if (photoProgress) {
                    photoProgress.style.display = 'none';
                }
                showError('Failed to upload photo');
            });

            xhr.open('POST', '/upload-profile-photo');
            xhr.send(formData);
        } catch (err) {
            console.error('Error uploading photo:', err);
            if (photoProgress) {
                photoProgress.style.display = 'none';
            }
            showError('Unable to upload photo');
        }
    });
}

// Setup form handlers
function setupFormHandlers() {
    // Already handled in setupEditModeHandlers
}

// Show messages
function showSuccess(message) {
    const msgEl = document.getElementById('successMessage');
    msgEl.textContent = message;
    msgEl.style.display = 'block';
    setTimeout(() => {
        msgEl.style.display = 'none';
    }, 4000);
}

function showError(message) {
    const msgEl = document.getElementById('errorMessage');
    msgEl.textContent = message;
    msgEl.style.display = 'block';
    setTimeout(() => {
        msgEl.style.display = 'none';
    }, 4000);
}

// Capitalize disorder names
function capitalizeDisorder(disorder) {
    if (!disorder || typeof disorder !== 'string') return 'General';
    return disorder.charAt(0).toUpperCase() + disorder.slice(1);
}

// Update achievement badges
function updateAchievementBadges(stats) {
    const badgesContainer = document.getElementById('badgesContainer');
    if (!badgesContainer) return;

    const totalAssessments = stats.total_assessments || 0;
    const avgScore = stats.average_score || 0;
    const disordersAttempted = stats.disorders_attempted || 0;

    // Clear and rebuild badges
    badgesContainer.innerHTML = '';

    // Badge 1: First Assessment
    const starterBadge = document.createElement('div');
    starterBadge.className = totalAssessments > 0 ? 'badge unlocked' : 'badge locked';
    starterBadge.title = 'Complete your first assessment';
    starterBadge.innerHTML = '<span class="badge-icon">🎯</span><span class="badge-name">Starter</span>';
    badgesContainer.appendChild(starterBadge);

    // Badge 2: Excellent Score
    const excellentBadge = document.createElement('div');
    excellentBadge.className = avgScore >= 80 ? 'badge unlocked' : 'badge locked';
    excellentBadge.title = 'Score 80% or higher';
    excellentBadge.innerHTML = '<span class="badge-icon">⭐</span><span class="badge-name">Excellent</span>';
    badgesContainer.appendChild(excellentBadge);

    // Badge 3: Master All Disorders
    const masterBadge = document.createElement('div');
    masterBadge.className = disordersAttempted >= 3 ? 'badge unlocked' : 'badge locked';
    masterBadge.title = 'Complete all 3 disorder assessments';
    masterBadge.innerHTML = '<span class="badge-icon">🏆</span><span class="badge-name">Master</span>';
    badgesContainer.appendChild(masterBadge);

    // Badge 4: Perfect Score
    const perfectBadge = document.createElement('div');
    perfectBadge.className = avgScore === 100 ? 'badge unlocked' : 'badge locked';
    perfectBadge.title = 'Achieve a perfect 100% score';
    perfectBadge.innerHTML = '<span class="badge-icon">👑</span><span class="badge-name">Perfect</span>';
    badgesContainer.appendChild(perfectBadge);
}

// Load faculties for dropdown
async function loadFaculties() {
    try {
        console.log('Loading faculties...');
        const response = await fetch('/api/faculties');
        
        if (!response.ok) {
            console.error('Failed to load faculties:', response.status);
            return;
        }

        const data = await response.json();
        console.log('Faculties loaded:', data);

        if (data.faculties && Array.isArray(data.faculties)) {
            const facultySelect = document.getElementById('faculty');
            
            if (!facultySelect) {
                console.warn('Faculty select element not found');
                return;
            }

            const currentFacultyId = facultySelect.value;

            // Clear existing options except the first one
            while (facultySelect.options.length > 1) {
                facultySelect.remove(1);
            }

            data.faculties.forEach(f => {
                const option = document.createElement('option');
                option.value = f.id;
                option.textContent = f.name;
                facultySelect.appendChild(option);
            });

            facultySelect.value = currentFacultyId || '';
        }
    } catch (err) {
        console.error('Error loading faculties:', err);
    }
}

// Tab navigation
function setupTabNavigation() {
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            const tabName = this.dataset.tab;

            // Hide all tabs
            document.querySelectorAll('.tab-content').forEach(t => t.classList.remove('active'));
            document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));

            // Show selected tab
            document.getElementById(tabName + '-tab').classList.add('active');
            this.classList.add('active');

            // Load assessments when assessments tab is clicked
            if (tabName === 'assessments') {
                loadAssessments();
            }
        });
    });
}

// Load assessments
async function loadAssessments() {
    try {
        console.log('Loading assessments...');
        const response = await fetch('/api/student/dashboard');
        
        if (!response.ok) {
            throw new Error('Failed to load assessments');
        }

        const data = await response.json();
        console.log('Assessments data:', data);

        if (data.status === 'ok' && data.history) {
            allAssessments = data.history;
            displayAssessments(allAssessments);
            renderPerformanceTrendChart(allAssessments);
            renderDisorderPerformanceCards(allAssessments);
        } else {
            showAssessmentsMessage('No assessments found');
        }
    } catch (err) {
        console.error('Error loading assessments:', err);
        showAssessmentsMessage('Unable to load assessments');
    }
}

// Display assessments
function displayAssessments(assessments) {
    const container = document.getElementById('assessmentsList');
    
    if (!container) {
        console.warn('Assessments list container not found');
        return;
    }

    if (!assessments || assessments.length === 0) {
        container.innerHTML = '<p class="loading">No assessments completed yet. Take an assessment to see your history.</p>';
        return;
    }

    container.innerHTML = assessments.map(assessment => {
        const date = new Date(assessment.date);
        const formattedDate = date.toLocaleDateString('en-US', { 
            year: 'numeric', 
            month: 'short', 
            day: 'numeric' 
        });
        const formattedTime = date.toLocaleTimeString('en-US', { 
            hour: '2-digit', 
            minute: '2-digit'
        });

        const scoreClass = assessment.score >= 80 ? 'score-excellent' : 
                          assessment.score >= 60 ? 'score-good' : 
                          assessment.score >= 40 ? 'score-average' : 'score-poor';

        return `
            <div class="assessment-item">
                <div class="assessment-info">
                    <div class="assessment-disorder">
                        ${capitalizeDisorder(assessment.disorder_type || 'unknown')}
                        <span class="disorder-badge">${assessment.status || 'completed'}</span>
                    </div>
                    <div class="assessment-meta">
                        <span class="meta-item">📅 ${formattedDate}</span>
                        <span class="meta-item">⏰ ${formattedTime}</span>
                    </div>
                </div>
                <div class="assessment-score">
                    <div class="score-value ${scoreClass}">${assessment.score}%</div>
                    <div class="score-label">Score</div>
                </div>
            </div>
        `;
    }).join('');
}

// Show assessments message
function showAssessmentsMessage(message) {
    const container = document.getElementById('assessmentsList');
    if (container) {
        container.innerHTML = `<p class="loading">${message}</p>`;
    }
}

// Render performance trend chart
function renderPerformanceTrendChart(assessments) {
    const canvas = document.getElementById('performanceTrendChart');
    if (!canvas) return;

    // Sort assessments by date
    const sorted = [...assessments].sort((a, b) => new Date(a.date) - new Date(b.date));

    // Prepare data for chart
    const labels = sorted.map(a => {
        const date = new Date(a.date);
        return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
    });

    const scores = sorted.map(a => a.score);

    // Destroy existing chart if any
    if (performanceTrendChart) {
        performanceTrendChart.destroy();
    }

    const ctx = canvas.getContext('2d');
    performanceTrendChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: 'Performance Score',
                data: scores,
                borderColor: '#4facfe',
                backgroundColor: 'rgba(79, 172, 254, 0.1)',
                borderWidth: 3,
                fill: true,
                tension: 0.4,
                pointBackgroundColor: '#4facfe',
                pointBorderColor: '#fff',
                pointBorderWidth: 2,
                pointRadius: 5,
                pointHoverRadius: 7,
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: {
                    display: true,
                    labels: {
                        color: '#1a1a2e',
                        font: { weight: 'bold' }
                    }
                }
            },
            scales: {
                y: {
                    min: 0,
                    max: 100,
                    ticks: {
                        callback: function(value) {
                            return value + '%';
                        }
                    },
                    grid: {
                        color: 'rgba(0, 0, 0, 0.05)'
                    }
                },
                x: {
                    grid: {
                        display: false
                    }
                }
            }
        }
    });
}

// Render disorder performance cards
function renderDisorderPerformanceCards(assessments) {
    const container = document.getElementById('disorderPerformanceCards');
    if (!container) return;

    // Group assessments by disorder
    const byDisorder = {};
    assessments.forEach(a => {
        const disorder = a.disorder_type || 'unknown';
        if (!byDisorder[disorder]) {
            byDisorder[disorder] = [];
        }
        byDisorder[disorder].push(a);
    });

    // Build cards for each disorder
    let html = '';
    Object.entries(byDisorder).forEach(([disorder, disorderAssessments]) => {
        const scores = disorderAssessments.map(a => a.score);
        const avgScore = scores.reduce((a, b) => a + b, 0) / scores.length;
        const maxScore = Math.max(...scores);
        const minScore = Math.min(...scores);

        html += `
            <div class="disorder-card ${disorder.toLowerCase()}">
                <div class="disorder-card-title">${capitalizeDisorder(disorder)}</div>
                <div class="disorder-card-stat">
                    <span>Attempts:</span>
                    <span class="disorder-card-stat-value">${disorderAssessments.length}</span>
                </div>
                <div class="disorder-card-stat">
                    <span>Average:</span>
                    <span class="disorder-card-stat-value">${avgScore.toFixed(1)}%</span>
                </div>
                <div class="disorder-card-stat">
                    <span>Best Score:</span>
                    <span class="disorder-card-stat-value">${maxScore}%</span>
                </div>
                <div class="disorder-card-stat">
                    <span>Lowest Score:</span>
                    <span class="disorder-card-stat-value">${minScore}%</span>
                </div>
            </div>
        `;
    });

    if (html) {
        container.innerHTML = html;
    } else {
        container.innerHTML = '<p class="loading">No assessment data yet.</p>';
    }
}

// Setup assessment filters
function setupAssessmentFilters() {
    document.querySelectorAll('.assessment-filter-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            const filter = this.dataset.filter;
            
            // Update active button
            document.querySelectorAll('.assessment-filter-btn').forEach(b => b.classList.remove('active'));
            this.classList.add('active');

            // Filter and display assessments
            if (filter === 'all') {
                displayAssessments(allAssessments);
            } else {
                const filtered = allAssessments.filter(a => 
                    (a.disorder_type || '').toLowerCase() === filter.toLowerCase()
                );
                displayAssessments(filtered);
            }
        });
    });
}

// Setup form handlers
function setupFormHandlers() {
    // Personal form
    document.getElementById('personalForm').addEventListener('submit', async function(e) {
        e.preventDefault();
        await updatePersonalInfo();
    });

    // Academic form
    document.getElementById('academicForm').addEventListener('submit', async function(e) {
        e.preventDefault();
        await updateAcademicInfo();
    });

    // Security form
    document.getElementById('securityForm').addEventListener('submit', async function(e) {
        e.preventDefault();
        await changePassword();
    });
}

// Update personal information
async function updatePersonalInfo() {
    const name = document.getElementById('fullName').value.trim();
    const email = document.getElementById('email').value.trim();
    const contact = document.getElementById('contact').value.trim();

    if (!name || !email) {
        showError('Name and email are required');
        return;
    }

    console.log('Updating personal info:', { name, email, contact });

    try {
        const response = await fetch('/api/student/profile', {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ name, email, contact })
        });

        const data = await response.json();
        console.log('Update response:', data);

        if (response.ok) {
            showSuccess('Personal information updated successfully');
        } else {
            showError(data.error || 'Failed to update information');
        }
    } catch (err) {
        console.error('Error updating personal info:', err);
        showError('Unable to update profile: ' + err.message);
    }
}

// Update academic information
async function updateAcademicInfo() {
    const classValue = document.getElementById('class').value.trim();
    const facultyId = document.getElementById('faculty').value;

    try {
        const response = await fetch('/api/student/profile', {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                class: classValue,
                faculty_id: facultyId || null
            })
        });

        const data = await response.json();

        if (response.ok) {
            showSuccess('Academic information updated successfully');
        } else {
            showError(data.error || 'Failed to update information');
        }
    } catch (err) {
        console.error('Error updating academic info:', err);
        showError('Unable to update profile');
    }
}

// Change password
async function changePassword() {
    const currentPassword = document.getElementById('currentPassword').value;
    const newPassword = document.getElementById('newPassword').value;
    const confirmPassword = document.getElementById('confirmPassword').value;

    if (!currentPassword || !newPassword || !confirmPassword) {
        showError('All fields are required');
        return;
    }

    if (newPassword.length < 8) {
        showError('Password must be at least 8 characters long');
        return;
    }

    if (newPassword !== confirmPassword) {
        showError('Passwords do not match');
        return;
    }

    try {
        const response = await fetch('/api/update-password', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                current_password: currentPassword,
                new_password: newPassword
            })
        });

        const data = await response.json();

        if (response.ok) {
            showSuccess('Password changed successfully');
            document.getElementById('securityForm').reset();
        } else {
            showError(data.error || 'Failed to change password');
        }
    } catch (err) {
        console.error('Error changing password:', err);
        showError('Unable to change password');
    }
}

// Photo upload
function setupPhotoUpload() {
    document.getElementById('uploadPhotoBtn').addEventListener('click', function() {
        document.getElementById('photoInput').click();
    });

    document.getElementById('photoInput').addEventListener('change', async function(e) {
        const file = e.target.files[0];
        if (!file) return;

        // Validate file size (max 5MB)
        if (file.size > 5 * 1024 * 1024) {
            showError('File size must be less than 5MB');
            return;
        }

        // Validate file type
        if (!file.type.startsWith('image/')) {
            showError('Please select a valid image file');
            return;
        }

        // Upload file
        const formData = new FormData();
        formData.append('photo', file);

        try {
            const response = await fetch('/upload-profile-photo', {
                method: 'POST',
                body: formData
            });

            const data = await response.json();

            if (response.ok) {
                showSuccess('Profile photo updated successfully');
                // Reload profile to get new photo
                loadProfileData();
            } else {
                showError(data.error || 'Failed to upload photo');
            }
        } catch (err) {
            console.error('Error uploading photo:', err);
            showError('Unable to upload photo');
        }
    });
}

// Reset forms
function resetPersonalForm() {
    loadProfileData();
}

function resetAcademicForm() {
    loadProfileData();
}

function resetSecurityForm() {
    document.getElementById('securityForm').reset();
}

// Show messages
function showSuccess(message) {
    const msgEl = document.getElementById('successMessage');
    msgEl.textContent = message;
    msgEl.style.display = 'block';
    setTimeout(() => {
        msgEl.style.display = 'none';
    }, 4000);
}

function showError(message) {
    const msgEl = document.getElementById('errorMessage');
    msgEl.textContent = message;
    msgEl.style.display = 'block';
    setTimeout(() => {
        msgEl.style.display = 'none';
    }, 4000);
}

// Capitalize disorder names
function capitalizeDisorder(disorder) {
    if (!disorder || typeof disorder !== 'string') return 'General';
    return disorder.charAt(0).toUpperCase() + disorder.slice(1);
}
