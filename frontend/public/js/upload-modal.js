/**
 * Upload Candidates Modal Logic
 * Extracted from jobs.html to be used in React pages
 */

// Authentication Helper
async function fetchWithAuth(endpoint, options = {}) {
    const token = localStorage.getItem('token');
    if (!token) {
        window.location.href = '/landing.html';
        return null;
    }

    const headers = {
        'Authorization': `Bearer ${token}`,
        ...options.headers
    };

    if (!(options.body instanceof FormData) && !headers['Content-Type']) {
        headers['Content-Type'] = 'application/json';
    }

    const url = endpoint.startsWith('http') ? endpoint : `/api/v1${endpoint}`;

    try {
        const response = await fetch(url, { ...options, headers });
        if (response.status === 401) {
            localStorage.removeItem('token');
            window.location.href = '/landing.html';
            return null;
        }
        return response;
    } catch (error) {
        console.error('Fetch Error:', error);
        return null;
    }
}

// Defensive JSON Helper
async function getSafeJson(response) {
    if (!response) return null;
    try {
        const text = await response.text();
        return text ? JSON.parse(text) : {};
    } catch (e) {
        console.error('JSON Parse Error:', e);
        return null;
    }
}

// Upload Candidates Modal State
window.uploadState = {
    currentStep: 1,
    jobId: null,
    uploadedFiles: [],
    selectedCandidates: [],
    allJobs: [],
    currentJobCandidates: [],
    sourceJobCandidates: [],
    duplicateEmails: new Set(),
    tempSelectedInPanel: new Set(),
    currentSourceJobId: null,
    currentSearchQuery: ''
};

// Show Upload Modal
window.showUploadCandidatesModal = function (jobId) {
    window.uploadState.jobId = jobId;
    window.uploadState.currentStep = 1;
    window.uploadState.uploadedFiles = [];
    window.uploadState.selectedCandidates = [];
    window.uploadState.tempSelectedInPanel = new Set();

    const modal = document.getElementById('upload-candidates-modal');
    if (modal) {
        modal.style.display = 'flex';
        document.body.style.overflow = 'hidden';

        loadJobsForImport();
        loadCurrentJobCandidates();
    } else {
        console.error('Upload modal element not found');
    }
}

// Hide Upload Modal
window.hideUploadCandidatesModal = function () {
    const modal = document.getElementById('upload-candidates-modal');
    if (modal) {
        modal.style.display = 'none';
        document.body.style.overflow = 'auto';
        resetUploadModal();
    }
}

// Reset Modal
function resetUploadModal() {
    window.uploadState.currentStep = 1;
    window.uploadState.uploadedFiles = [];
    window.uploadState.selectedCandidates = [];
    window.uploadState.tempSelectedInPanel = new Set();
    goToUploadStep(1);
    renderUploadFilesList();
}

// Navigate Steps
window.goToUploadStep = function (step) {
    if (window.uploadState.currentStep === 2 && step === 3) {
        const sourceJob = window.uploadState.allJobs.find(j => j.id === window.uploadState.currentSourceJobId);
        if (sourceJob && window.uploadState.tempSelectedInPanel.size > 0) {
            window.uploadState.tempSelectedInPanel.forEach(candidateId => {
                const candidate = window.uploadState.sourceJobCandidates.find(c => c.id === candidateId);
                if (candidate && !window.uploadState.selectedCandidates.find(sc => sc.id === candidate.id)) {
                    window.uploadState.selectedCandidates.push({
                        ...candidate,
                        sourceJobId: window.uploadState.currentSourceJobId,
                        sourceJobTitle: sourceJob.title
                    });
                }
            });
            window.uploadState.tempSelectedInPanel.clear();
        }
    }

    document.querySelectorAll('.upload-step-content').forEach(el => el.classList.remove('active'));

    const stepEl = document.getElementById(`upload-step-${step}`);
    if (stepEl) {
        stepEl.classList.add('active');
        window.uploadState.currentStep = step;

        if (step === 3) {
            renderReviewSummary();
        }
    }
}

window.skipToStep2 = function () {
    goToUploadStep(2);
}

// File Upload Handling
window.handleUploadFiles = function (files) {
    const validTypes = ['application/pdf', 'application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'];

    Array.from(files).forEach(file => {
        if (validTypes.includes(file.type)) {
            window.uploadState.uploadedFiles.push({
                file: file,
                name: file.name,
                size: formatFileSize(file.size),
                type: file.type,
                uploadedAt: new Date()
            });
        } else {
            alert(`File type not supported: ${file.name}`);
        }
    });

    renderUploadFilesList();
}

window.removeUploadFile = function (index) {
    window.uploadState.uploadedFiles.splice(index, 1);
    renderUploadFilesList();
}

function renderUploadFilesList() {
    const list = document.getElementById('upload-files-list');
    const count = document.getElementById('upload-file-count');

    if (!list || !count) return;

    count.textContent = `(${window.uploadState.uploadedFiles.length})`;

    if (window.uploadState.uploadedFiles.length === 0) {
        list.innerHTML = '<p class="text-sm text-gray-400 text-center py-8">No files uploaded yet</p>';
        return;
    }

    list.innerHTML = window.uploadState.uploadedFiles.map((fileData, index) => {
        const icon = fileData.type.includes('pdf') ? 'picture_as_pdf' : 'description';
        const iconBg = fileData.type.includes('pdf') ? 'bg-red-50 dark:bg-red-900/20 text-red-500 dark:text-red-400' : 'bg-blue-50 dark:bg-blue-900/20 text-blue-500 dark:text-blue-400';

        return `
            <div class="flex items-center gap-4 bg-white dark:bg-gray-700 border border-gray-100 dark:border-gray-600 rounded-xl p-3 shadow-sm hover:shadow-md transition-shadow shrink-0">
                <div class="flex items-center justify-center rounded-lg ${iconBg} shrink-0 w-12 h-12">
                    <span class="material-symbols-outlined">${icon}</span>
                </div>
                <div class="flex flex-col flex-1 min-w-0">
                    <p class="text-gray-900 dark:text-white text-sm font-medium truncate">${fileData.name}</p>
                    <p class="text-gray-400 dark:text-gray-400 text-xs">${fileData.size} • Just now</p>
                </div>
                <div class="shrink-0 pr-2">
                    <button onclick="removeUploadFile(${index})" class="text-sm font-medium text-red-500 hover:text-red-700 dark:text-red-400 dark:hover:text-red-300 transition-colors">
                        Remove
                    </button>
                </div>
            </div>
        `;
    }).join('');
}

// Load Jobs for Import
async function loadJobsForImport() {
    try {
        const response = await fetchWithAuth('/jobs');
        if (response && response.ok) {
            window.uploadState.allJobs = await getSafeJson(response) || [];
            renderJobsDropdown();
        }
    } catch (error) {
        console.error('Failed to load jobs:', error);
    }
}

function renderJobsDropdown() {
    const panel = document.getElementById('jobs-list-panel');
    if (!panel) return;

    const availableJobs = window.uploadState.allJobs.filter(job => job.id !== window.uploadState.jobId);

    if (availableJobs.length === 0) {
        panel.innerHTML = '<p class="text-sm text-gray-400 text-center py-8">No other jobs available</p>';
        return;
    }

    panel.innerHTML = availableJobs.map(job => {
        const isActive = window.uploadState.currentSourceJobId === job.id;
        return `
            <div onclick="selectJobUnified('${job.id}')" class="cursor-pointer p-3 rounded-lg border transition-all ${isActive
                ? 'border-primary bg-[#E9FBEF] dark:bg-green-900/10'
                : 'border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 hover:border-primary/50'
            }">
                <div class="flex items-center gap-2 mb-1">
                    <span class="material-symbols-outlined text-primary text-[18px]">work</span>
                    <p class="text-sm font-bold text-gray-900 dark:text-white truncate flex-1">${job.title}</p>
                </div>
                <p class="text-xs text-gray-500 dark:text-gray-400 pl-6">Candidates available</p>
            </div>
        `;
    }).join('');
}

async function loadCurrentJobCandidates() {
    try {
        const response = await fetchWithAuth(`/jobs/${window.uploadState.jobId}/candidates`);
        if (response && response.ok) {
            window.uploadState.currentJobCandidates = await getSafeJson(response) || [];
            window.uploadState.duplicateEmails = new Set(window.uploadState.currentJobCandidates.map(c => c.email.toLowerCase()));
        }
    } catch (error) {
        console.error('Failed to load current job candidates:', error);
    }
}

window.selectJobUnified = async function (jobId) {
    // Finalize any temp selections from previous job before switching
    if (window.uploadState.currentSourceJobId && window.uploadState.tempSelectedInPanel.size > 0) {
        const prevJob = window.uploadState.allJobs.find(j => j.id === window.uploadState.currentSourceJobId);
        if (prevJob) {
            window.uploadState.tempSelectedInPanel.forEach(candidateId => {
                const candidate = window.uploadState.sourceJobCandidates.find(c => c.id === candidateId);
                if (candidate && !window.uploadState.selectedCandidates.find(sc => sc.id === candidate.id)) {
                    window.uploadState.selectedCandidates.push({
                        ...candidate,
                        sourceJobId: window.uploadState.currentSourceJobId,
                        sourceJobTitle: prevJob.title
                    });
                }
            });
            window.uploadState.tempSelectedInPanel.clear();
        }
    }

    window.uploadState.currentSourceJobId = jobId;
    renderJobsDropdown();

    try {
        const response = await fetchWithAuth(`/jobs/${jobId}/candidates`);
        if (response && response.ok) {
            window.uploadState.sourceJobCandidates = await getSafeJson(response) || [];
            window.uploadState.currentSearchQuery = '';
            const searchInput = document.getElementById('candidate-search-unified');
            if (searchInput) searchInput.value = '';
            renderCandidatesUnified();
            renderImportSelectedListUnified();
        }
    } catch (error) {
        console.error('Failed to load candidates:', error);
        const panel = document.getElementById('candidates-list-panel');
        if (panel) panel.innerHTML = '<p class="text-sm text-red-400 text-center py-8">Failed to load candidates</p>';
    }
}

window.renderCandidatesUnified = function (searchQuery = '') {
    const panel = document.getElementById('candidates-list-panel');
    if (!panel) return;

    const filtered = window.uploadState.sourceJobCandidates.filter(c => {
        if (searchQuery) {
            return c.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
                c.email.toLowerCase().includes(searchQuery.toLowerCase());
        }
        return true;
    });

    if (filtered.length === 0) {
        panel.innerHTML = '<p class="text-sm text-gray-400 text-center py-8">No candidates found</p>';
        return;
    }

    panel.innerHTML = filtered.map(candidate => {
        const isSelected = window.uploadState.tempSelectedInPanel.has(candidate.id);
        const skills = candidate.parsed_skills || [];

        return `
            <div class="relative group">
                <label class="flex items-start gap-3 p-3 rounded-xl border border-gray-100 dark:border-gray-700 bg-white dark:bg-gray-800 hover:border-primary/40 transition-colors cursor-pointer ${isSelected ? 'border-primary/50 bg-[#E9FBEF]/30 dark:bg-primary/5' : ''}">
                    <input onchange="toggleCandidateUnified('${candidate.id}')" ${isSelected ? 'checked' : ''} type="checkbox" class="mt-1 w-4 h-4 text-primary border-gray-300 rounded focus:ring-primary bg-gray-50 dark:bg-gray-700"/>
                    <div class="flex flex-col flex-1 min-w-0">
                        <div class="flex justify-between items-start">
                            <span class="text-sm font-bold text-gray-700 dark:text-gray-200">${candidate.name}</span>
                        </div>
                        <span class="text-xs text-gray-400 mb-2 truncate">${candidate.email}</span>
                        ${skills.length > 0 ? `
                            <div class="flex flex-wrap gap-1.5">
                                ${skills.slice(0, 3).map(skill =>
            `<span class="px-1.5 py-0.5 rounded-md bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300 text-[10px] font-medium border border-gray-200 dark:border-gray-600">${skill}</span>`
        ).join('')}
                                ${skills.length > 3 ? `<span class="px-1.5 py-0.5 rounded-md text-[10px] text-gray-400">+${skills.length - 3}</span>` : ''}
                            </div>
                        ` : ''}
                    </div>
                </label>
            </div>
        `;
    }).join('');
}

window.toggleCandidateUnified = function (candidateId) {
    if (window.uploadState.tempSelectedInPanel.has(candidateId)) {
        window.uploadState.tempSelectedInPanel.delete(candidateId);
    } else {
        window.uploadState.tempSelectedInPanel.add(candidateId);
    }
    renderCandidatesUnified(window.uploadState.currentSearchQuery);
    renderImportSelectedListUnified();
}

window.filterCandidatesUnified = function (query) {
    window.uploadState.currentSearchQuery = query;
    renderCandidatesUnified(query);
}

function renderImportSelectedListUnified() {
    const list = document.getElementById('import-selected-list-unified');
    const count = document.getElementById('import-selected-count-unified');
    if (!list || !count) return;

    const tempList = Array.from(window.uploadState.tempSelectedInPanel).map(id =>
        window.uploadState.sourceJobCandidates.find(c => c.id === id)
    ).filter(Boolean);

    const finalList = window.uploadState.selectedCandidates;
    const allSelected = [...finalList, ...tempList];

    count.textContent = `${allSelected.length} Selected`;

    if (allSelected.length === 0) {
        list.innerHTML = '<p class="text-sm text-gray-400 w-full text-center py-4">No candidates selected yet</p>';
        return;
    }

    list.innerHTML = allSelected.map((candidate, index) => {
        const colors = ['bg-blue-100 text-blue-600', 'bg-purple-100 text-purple-600', 'bg-orange-100 text-orange-600', 'bg-pink-100 text-pink-600', 'bg-green-100 text-green-600'];
        const colorClass = colors[index % colors.length];
        const initials = candidate.name.split(' ').map(n => n[0]).join('').toUpperCase().slice(0, 2);
        const isTemp = window.uploadState.tempSelectedInPanel.has(candidate.id);

        return `
            <div class="inline-flex items-center gap-2 px-3 py-2 rounded-lg bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 shadow-sm">
                <div class="h-6 w-6 rounded-full ${colorClass} flex items-center justify-center text-[10px] font-bold shrink-0">${initials}</div>
                <span class="text-xs font-medium text-gray-700 dark:text-gray-300">${candidate.name}</span>
                <button onclick="${isTemp ? `toggleCandidateUnified('${candidate.id}')` : `removeImportedCandidateUnified('${candidate.id}')`}" class="text-gray-400 hover:text-red-500 transition-colors shrink-0">
                    <span class="material-symbols-outlined text-[16px]">close</span>
                </button>
            </div>
        `;
    }).join('');
}

window.removeImportedCandidateUnified = function (candidateId) {
    window.uploadState.selectedCandidates = window.uploadState.selectedCandidates.filter(c => c.id !== candidateId);
    renderImportSelectedListUnified();
}

// Review & Confirm
function renderReviewSummary() {
    const filesList = document.getElementById('review-files-list');
    const filesCount = document.getElementById('review-files-count');
    if (!filesList || !filesCount) return;

    filesCount.textContent = window.uploadState.uploadedFiles.length;

    if (window.uploadState.uploadedFiles.length === 0) {
        filesList.innerHTML = '<p class="text-sm text-gray-400 text-center py-4">No files uploaded</p>';
    } else {
        filesList.innerHTML = window.uploadState.uploadedFiles.map((fileData, index) => {
            const icon = fileData.type.includes('pdf') ? 'picture_as_pdf' : 'description';
            const iconBg = fileData.type.includes('pdf') ? 'bg-red-50 dark:bg-red-900/20 text-red-600 dark:text-red-400' : 'bg-blue-50 dark:bg-blue-900/20 text-blue-600 dark:text-blue-400';

            return `
                <div class="group flex items-center justify-between p-4 rounded-xl border border-gray-200 dark:border-gray-700 hover:border-primary/40 hover:shadow-md transition-all bg-white dark:bg-gray-800">
                    <div class="flex items-center gap-4">
                        <div class="w-10 h-10 rounded-lg ${iconBg} flex items-center justify-center">
                            <span class="material-symbols-outlined">${icon}</span>
                        </div>
                        <div>
                            <p class="text-sm font-bold text-gray-900 dark:text-white group-hover:text-primary transition-colors">${fileData.name}</p>
                            <p class="text-xs text-gray-500 dark:text-gray-400 mt-0.5">${fileData.size} • Just now</p>
                        </div>
                    </div>
                    <button onclick="removeUploadFile(${index}); renderReviewSummary();" class="text-gray-400 hover:text-red-500 transition-colors p-2 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-lg">
                        <span class="text-sm font-medium hidden group-hover:inline mr-1">Remove</span>
                        <span class="material-symbols-outlined text-[20px] align-middle">delete</span>
                    </button>
                </div>
            `;
        }).join('');
    }
    // Render Candidates with duplicate analysis
    const candidatesList = document.getElementById('review-candidates-list');
    const candidatesCount = document.getElementById('review-candidates-count');
    const totalCandidates = window.uploadState.selectedCandidates.length;

    if (candidatesCount) candidatesCount.textContent = totalCandidates;

    // Calculate duplicates
    const dupeSet = window.uploadState.duplicateEmails || new Set();
    const duplicates = window.uploadState.selectedCandidates.filter(c => dupeSet.has(c.email.toLowerCase()));
    const duplicateCount = duplicates.length;
    const newCount = totalCandidates - duplicateCount;

    let summaryHTML = '';
    if (duplicateCount > 0) {
        summaryHTML = `
            <div class="mb-4 p-4 rounded-xl bg-orange-50 dark:bg-orange-900/10 border border-orange-200 dark:border-orange-800 flex items-start gap-3">
                <span class="material-symbols-outlined text-orange-500 mt-0.5">info</span>
                <div>
                    <h4 class="text-sm font-bold text-orange-700 dark:text-orange-400">Import Analysis</h4>
                    <p class="text-xs text-orange-600 dark:text-orange-300 mt-1">
                        You have selected <strong>${totalCandidates}</strong> candidates. 
                        <strong>${duplicateCount}</strong> are already in this job and will be skipped. 
                        <strong>${newCount}</strong> new candidates will be added.
                    </p>
                </div>
            </div>
        `;
    }

    if (totalCandidates === 0) {
        if (candidatesList) candidatesList.innerHTML = summaryHTML + '<p class="text-sm text-gray-400 text-center py-4">No candidates imported</p>';
    } else {
        const listHTML = window.uploadState.selectedCandidates.map((candidate, index) => {
            const colors = ['bg-indigo-100 text-indigo-600', 'bg-emerald-100 text-emerald-600', 'bg-purple-100 text-purple-600', 'bg-pink-100 text-pink-600'];
            const colorClass = colors[index % colors.length];
            const initials = candidate.name.split(' ').map(n => n[0]).join('').toUpperCase().slice(0, 2);
            const skills = candidate.parsed_skills || [];
            const isDupe = dupeSet.has(candidate.email.toLowerCase());

            return `
                <div class="flex items-center justify-between p-3 rounded-xl border border-gray-100 dark:border-gray-700 hover:border-primary/40 hover:bg-[#E9FBEF]/30 dark:hover:bg-primary/5 transition-all group bg-white dark:bg-gray-800 ${isDupe ? 'opacity-70' : ''}">
                    <div class="flex items-center gap-4 flex-1">
                        <div class="w-10 h-10 rounded-full ${colorClass} dark:bg-${colorClass.split(' ')[0].replace('bg-', '')}-900/30 flex items-center justify-center text-sm font-bold shadow-sm">
                            ${initials}
                        </div>
                        <div class="flex flex-col min-w-0">
                            <div class="flex items-center gap-2">
                                <span class="text-sm font-bold text-gray-900 dark:text-white truncate">${candidate.name}</span>
                                ${isDupe ? '<span class="px-1.5 py-0.5 rounded text-[10px] font-medium bg-orange-100 text-orange-600 border border-orange-200">Duplicate</span>' : ''}
                            </div>
                            <span class="text-xs text-gray-500 dark:text-gray-400 truncate">${candidate.email}</span>
                        </div>
                    </div>
                    ${skills.length > 0 ? `
                        <div class="hidden sm:flex items-center gap-2 mr-4">
                            ${skills.slice(0, 2).map(skill =>
                `<span class="px-2 py-1 rounded-md bg-[#E9FBEF] dark:bg-primary/10 text-[#14a081] dark:text-primary text-[10px] font-semibold border border-primary/20">${skill}</span>`
            ).join('')}
                        </div>
                    ` : ''}
                    <button onclick="removeImportedCandidateUnified('${candidate.id}'); renderReviewSummary();" class="w-8 h-8 flex items-center justify-center rounded-lg text-gray-400 hover:text-red-500 hover:bg-red-50 dark:hover:bg-red-900/20 transition-colors">
                        <span class="material-symbols-outlined text-[20px]">close</span>
                    </button>
                </div>
            `;
        }).join('');

        if (candidatesList) candidatesList.innerHTML = summaryHTML + listHTML;
    }

    const total = window.uploadState.uploadedFiles.length + window.uploadState.selectedCandidates.length;
    const totalCountEl = document.getElementById('review-total-count');
    if (totalCountEl) totalCountEl.textContent = `${total} items selected`;
}

window.confirmAndSubmit = async function () {
    const btn = document.getElementById('confirm-submit-btn');
    const total = window.uploadState.uploadedFiles.length + window.uploadState.selectedCandidates.length;

    if (total === 0) {
        alert('Please upload files or import candidates before submitting.');
        return;
    }

    btn.disabled = true;
    btn.innerHTML = '<span class="material-symbols-outlined animate-spin">refresh</span> Submitting...';

    // Show rudimentary loader if page-loader missing
    const loader = document.getElementById('page-loader');
    if (loader) loader.style.display = 'flex';

    try {
        let uploadedCount = 0;
        let uploadFailures = 0;
        let importedCount = 0;
        let duplicateCount = 0;
        let importFailures = 0;

        for (const fileData of window.uploadState.uploadedFiles) {
            try {
                const formData = new FormData();
                formData.append('file', fileData.file);

                const res = await fetchWithAuth(`/jobs/${window.uploadState.jobId}/candidates`, {
                    method: 'POST',
                    headers: {
                        'Authorization': `Bearer ${localStorage.getItem('token')}`
                    },
                    body: formData
                });

                if (res && res.ok) {
                    uploadedCount++;
                } else {
                    const errData = await getSafeJson(res) || {};
                    const detail = (errData.detail || '').toString().toLowerCase();
                    if (res && res.status === 400 && (detail.includes('exists') || detail.includes('duplicate'))) {
                        duplicateCount++;
                    } else {
                        throw new Error(errData.detail || 'Upload failed');
                    }
                }
            } catch (e) {
                console.error('File upload failed', e);
                uploadFailures++;
            }
        }

        if (window.uploadState.selectedCandidates.length > 0) {
            const bySourceJob = {};
            window.uploadState.selectedCandidates.forEach(c => {
                if (!bySourceJob[c.sourceJobId]) {
                    bySourceJob[c.sourceJobId] = [];
                }
                bySourceJob[c.sourceJobId].push(c.id);
            });

            for (const [sourceJobId, candidateIds] of Object.entries(bySourceJob)) {
                try {
                    const res = await fetchWithAuth(`/jobs/${window.uploadState.jobId}/import_candidates`, {
                        method: 'POST',
                        body: JSON.stringify({
                            source_job_id: sourceJobId,
                            candidate_ids: candidateIds
                        })
                    });
                    const data = await getSafeJson(res) || {};
                    importedCount += Number(data.imported || 0);
                    duplicateCount += Number(data.skipped || 0);
                } catch (e) {
                    console.error('Import failed', e);
                    importFailures++;
                }
            }
        }

        const totalSuccess = uploadedCount + importedCount;
        const totalFailed = uploadFailures + importFailures;

        // Show detailed toast
        showToast(
            'Upload Complete',
            `Added: ${totalSuccess} | Duplicates: ${duplicateCount} | Failed: ${totalFailed}`,
            totalFailed > 0 ? 'warning' : 'success'
        );

        // Auto-redirect removed - let user close manually
        // setTimeout(() => {
        //     const params = new URLSearchParams({
        //         upload_success: 'true',
        //         total: (totalSuccess + duplicateCount + totalFailed).toString(),
        //         added: totalSuccess.toString(),
        //         duplicates: duplicateCount.toString(),
        //         failed: totalFailed.toString()
        //     });
        //     window.location.href = `/jobs/${window.uploadState.jobId}/candidates?${params.toString()}`;
        // }, 1000);

    } catch (error) {
        console.error('Upload failed:', error);
        alert('Failed to upload candidates. Please try again.');
        btn.disabled = false;
        btn.innerHTML = 'Confirm & Submit <span class="material-symbols-outlined text-[18px]">check</span>';
        if (loader) loader.style.display = 'none';
    }
}

function formatFileSize(bytes) {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
}

function showToast(title, message, type = 'info') {
    const toast = document.createElement('div');
    toast.className = 'fixed bottom-6 right-6 z-[100] bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 shadow-xl rounded-xl p-4 flex items-start gap-3 transition-all duration-500 transform translate-y-10 opacity-0 max-w-sm';

    const icon = type === 'success' ? 'check_circle' : (type === 'error' || type === 'warning' ? 'error' : 'info');
    const iconColor = type === 'success' ? 'text-green-500' : (type === 'error' ? 'text-red-500' : (type === 'warning' ? 'text-orange-500' : 'text-blue-500'));

    toast.innerHTML = `
        <span class="material-symbols-outlined ${iconColor} mt-0.5">${icon}</span>
        <div>
            <h4 class="font-bold text-sm text-gray-900 dark:text-white">${title}</h4>
            <p class="text-xs text-gray-500 dark:text-gray-400 mt-1">${message}</p>
        </div>
        <button onclick="this.parentElement.remove()" class="ml-auto text-gray-400 hover:text-gray-600">
            <span class="material-symbols-outlined text-[18px]">close</span>
        </button>
    `;

    document.body.appendChild(toast);

    requestAnimationFrame(() => {
        toast.classList.remove('translate-y-10', 'opacity-0');
    });

    // Auto dismiss removed - user must close manually
    // setTimeout(() => {
    //     toast.classList.add('translate-y-10', 'opacity-0');
    //     setTimeout(() => toast.remove(), 500);
    // }, 5000);
}
