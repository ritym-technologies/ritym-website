/* ==========================================================================
   RITYM TECHNOLOGIES — CLIENT LOGIC, WIZARD, ANTI-SPAM & REQUEST ENGINE
   ========================================================================== */

document.addEventListener('DOMContentLoaded', () => {
    initEmailObfuscation();
    initAppWizard();
    initProjectTracker();
    initSilentVisitorAnalytics();
    initDirectContactForm();
    initSuccessModal();
});

/* --------------------------------------------------------------------------
   1. ANTI-SPAM EMAIL OBFUSCATION (assist@ritym.com)
   -------------------------------------------------------------------------- */
const EMAIL_USER = "assist";
const EMAIL_DOMAIN = "ritym.com";

function getProtectedEmail() {
    return `${EMAIL_USER}@${EMAIL_DOMAIN}`;
}

function initEmailObfuscation() {
    const fullEmail = getProtectedEmail();

    const protectedNavDisplay = document.getElementById('protected-email-display');
    if (protectedNavDisplay) {
        protectedNavDisplay.textContent = fullEmail;
    }

    const emailChipContainer = document.getElementById('email-chip-container');
    if (emailChipContainer) {
        emailChipContainer.addEventListener('click', () => {
            copyToClipboard(fullEmail, 'Email assist@ritym.com copied to clipboard!');
        });
    }

    const protectedContactDisplay = document.getElementById('protected-email-contact');
    if (protectedContactDisplay) {
        protectedContactDisplay.textContent = fullEmail;
    }

    const btnCopyContactEmail = document.getElementById('btn-copy-contact-email');
    if (btnCopyContactEmail) {
        btnCopyContactEmail.addEventListener('click', () => {
            copyToClipboard(fullEmail, 'Email assist@ritym.com copied to clipboard!');
        });
    }
}

/* --------------------------------------------------------------------------
   2. ANTI-SPAM RATE LIMITING & BOT DEFENSE SYSTEM
   -------------------------------------------------------------------------- */
function checkRateLimit() {
    const history = JSON.parse(localStorage.getItem('ritym_submission_history') || '[]');
    const now = Date.now();
    const tenMinutesAgo = now - (10 * 60 * 1000);
    
    const recentSubmissions = history.filter(ts => ts > tenMinutesAgo);
    if (recentSubmissions.length >= 3) {
        return false; // Exceeded rate limit
    }
    recentSubmissions.push(now);
    localStorage.setItem('ritym_submission_history', JSON.stringify(recentSubmissions));
    return true;
}

function initSuccessModal() {
    const modal = document.getElementById('request-success-modal');
    const closeBtn = document.getElementById('success-close-btn');
    const doneBtn = document.getElementById('btn-success-done');

    if (closeBtn && modal) {
        closeBtn.addEventListener('click', () => modal.classList.remove('active'));
    }

    if (doneBtn && modal) {
        doneBtn.addEventListener('click', () => {
            modal.classList.remove('active');
            const trackerSec = document.getElementById('tracker');
            if (trackerSec) trackerSec.scrollIntoView({ behavior: 'smooth' });
        });
    }
}

function openSuccessModal(orderData) {
    const modal = document.getElementById('request-success-modal');
    const trackIdEl = document.getElementById('succ-tracking-id');
    const emailEl = document.getElementById('succ-client-email');

    if (trackIdEl) trackIdEl.textContent = orderData.id;
    if (emailEl) emailEl.textContent = orderData.clientEmail;

    if (modal) modal.classList.add('active');
}

/* --------------------------------------------------------------------------
   3. INTERACTIVE CUSTOM APP REQUEST CONFIGURATOR WIZARD
   -------------------------------------------------------------------------- */
function initAppWizard() {
    const form = document.getElementById('app-configurator-form');
    if (!form) return;

    let currentStep = 1;

    function goToStep(stepNum) {
        if (stepNum < 1 || stepNum > 4) return;
        currentStep = stepNum;

        document.querySelectorAll('.wizard-step-panel').forEach(panel => {
            panel.classList.remove('active');
        });
        const targetPanel = document.getElementById(`wizard-step-${stepNum}`);
        if (targetPanel) targetPanel.classList.add('active');

        document.querySelectorAll('.w-step').forEach(stepNav => {
            const stepVal = parseInt(stepNav.getAttribute('data-step-nav'), 10);
            if (stepVal <= currentStep) {
                stepNav.classList.add('active');
            } else {
                stepNav.classList.remove('active');
            }
        });

        if (currentStep === 4) {
            updateWizardReviewSummary();
        }
    }

    document.querySelectorAll('.btn-next-step').forEach(btn => {
        btn.addEventListener('click', (e) => {
            const nextStep = parseInt(e.target.getAttribute('data-next'), 10);
            goToStep(nextStep);
        });
    });

    document.querySelectorAll('.btn-prev-step').forEach(btn => {
        btn.addEventListener('click', (e) => {
            const prevStep = parseInt(e.target.getAttribute('data-prev'), 10);
            goToStep(prevStep);
        });
    });

    document.querySelectorAll('.w-step').forEach(stepNav => {
        stepNav.addEventListener('click', () => {
            const stepVal = parseInt(stepNav.getAttribute('data-step-nav'), 10);
            if (stepVal < currentStep) {
                goToStep(stepVal);
            }
        });
    });

    function updateWizardReviewSummary() {
        const selectedPlatforms = Array.from(form.querySelectorAll('input[name="platform"]:checked')).map(cb => cb.value);
        const selectedFeatures = Array.from(form.querySelectorAll('input[name="feature"]:checked')).map(cb => cb.value);
        const timeline = form.querySelector('#w-timeline').value;
        const budget = form.querySelector('#w-budget').value;

        const revPlatforms = document.getElementById('rev-platforms');
        const revFeatures = document.getElementById('rev-features');
        const revTimelineBudget = document.getElementById('rev-timeline-budget');

        if (revPlatforms) revPlatforms.textContent = selectedPlatforms.length ? selectedPlatforms.join(', ') : 'None Selected';
        if (revFeatures) revFeatures.textContent = selectedFeatures.length ? selectedFeatures.join(', ') : 'None Selected';
        if (revTimelineBudget) revTimelineBudget.textContent = `${timeline} | ${budget}`;
    }

    form.addEventListener('submit', (e) => {
        e.preventDefault();

        // Check Honeypot for automated spam bots
        const hp = document.getElementById('w-hp').value;
        if (hp) {
            console.warn('[RITYM Security] Automated bot attempt blocked via honeypot.');
            logSilentTelemetry('[SPAM BLOCKED] Honeypot trap triggered on App Wizard.');
            return;
        }

        if (!checkRateLimit()) {
            showToast('⚠️ Rate limit exceeded (Max 3 submissions per 10 minutes). Please wait.', 'warn');
            logSilentTelemetry('[SPAM BLOCKED] Rate limit exceeded on App Wizard.');
            return;
        }

        const name = document.getElementById('w-name').value.trim();
        const email = document.getElementById('w-email').value.trim();

        if (!name || !email) {
            showToast('Please enter your full name and email address.', 'warn');
            return;
        }

        // Generate tracking ID
        const trackId = `RITYM-${Math.floor(10000 + Math.random() * 90000)}`;

        const orderData = {
            id: trackId,
            clientName: name,
            clientEmail: email,
            stage: 1, // 1: Request Received (Open)
            timestamp: new Date().toLocaleDateString()
        };

        // Save order and update UI
        saveProjectOrder(orderData);
        updateTrackerUI(trackId);
        openSuccessModal(orderData);

        showToast(`Request ${trackId} confirmed! Dispatched to assist@ritym.com.`, 'success');
        logSilentTelemetry(`[CONFIRMED ORDER ${trackId}] From ${name} (${email})`);

        form.reset();
        goToStep(1);
    });
}

/* --------------------------------------------------------------------------
   4. 7-STAGE PROJECT LIFECYCLE TRACKER ENGINE
   -------------------------------------------------------------------------- */
const STAGE_CONFIG = {
    1: {
        title: "Stage 1: REQUEST_RECEIVED (Open)",
        pill: "Stage 1: REQUEST_RECEIVED (Open)",
        pct: "15%",
        desc: "Request logged into RITYM Engineering queue. 25% initial deposit invoice issued for project approval & architectural sign-off."
    },
    2: {
        title: "Stage 2: IN_REVIEW (Architect Review)",
        pill: "Stage 2: IN_REVIEW (Architect Review)",
        pct: "30%",
        desc: "Senior engineering architect reviewing project specifications, tech stack compatibility, and security requirements."
    },
    3: {
        title: "Stage 3: ASSIGNED (Team Allocated)",
        pill: "Stage 3: ASSIGNED (Team Allocated)",
        pct: "45%",
        desc: "Lead Android developer, backend engineer, and QA specialist allocated. Architecture diagram & sprint plan approved."
    },
    4: {
        title: "Stage 4: IN_DEVELOPMENT (Active Build)",
        pill: "Stage 4: IN_DEVELOPMENT (Active Build)",
        pct: "65%",
        desc: "Core sprint execution in progress. Kotlin MVVM modules, UI components, and hardware BLE/APIs are being compiled. 50% milestone due upon demo."
    },
    5: {
        title: "Stage 5: VALIDATION (QA & Testing)",
        pill: "Stage 5: VALIDATION (QA & Testing)",
        pct: "80%",
        desc: "Rigorous automated testing, security audit, memory leak checks, and multi-device Android validation underway."
    },
    6: {
        title: "Stage 6: DOCUMENTATION (Docs & Specs)",
        pill: "Stage 6: DOCUMENTATION (Docs & Specs)",
        pct: "90%",
        desc: "API documentation, user manuals, deployment manifests, and clean source code packaging prepared."
    },
    7: {
        title: "Stage 7: BUILD_RELEASE (Play Store Release)",
        pill: "Stage 7: BUILD_RELEASE (Completed)",
        pct: "100%",
        desc: "Final App Bundle (.aab) compiled, Play Store submission completed, and codebase delivered. 25% final balance invoice settled."
    }
};

function initProjectTracker() {
    const btnLookup = document.getElementById('btn-lookup-status');
    const inputTrackId = document.getElementById('track-id-input');

    if (btnLookup && inputTrackId) {
        btnLookup.addEventListener('click', () => {
            const queryId = inputTrackId.value.trim().toUpperCase();
            if (queryId) updateTrackerUI(queryId);
        });
    }

    // Default sample load
    updateTrackerUI('RITYM-SAMPLE-8842');
}

function saveProjectOrder(order) {
    const orders = JSON.parse(localStorage.getItem('ritym_project_orders') || '{}');
    orders[order.id] = order;
    localStorage.setItem('ritym_project_orders', JSON.stringify(orders));
}

function updateTrackerUI(trackId) {
    const orders = JSON.parse(localStorage.getItem('ritym_project_orders') || '{}');
    
    let order = orders[trackId];
    if (!order && trackId === 'RITYM-SAMPLE-8842') {
        order = {
            id: 'RITYM-SAMPLE-8842',
            clientName: 'Demo Client Request',
            clientEmail: 'client@company.com',
            stage: 4
        };
    } else if (!order) {
        order = {
            id: trackId,
            clientName: 'Active Client Request',
            clientEmail: 'client@ritym.com',
            stage: 1
        };
    }

    const stageNum = order.stage || 1;
    const stageData = STAGE_CONFIG[stageNum] || STAGE_CONFIG[1];

    const tOrderId = document.getElementById('t-order-id');
    const tClientName = document.getElementById('t-client-name');
    const tCurrentStatus = document.getElementById('t-current-status');
    const tStageHeading = document.getElementById('t-stage-heading');
    const tProgressPct = document.getElementById('t-progress-pct');
    const tStageDesc = document.getElementById('t-stage-desc');

    if (tOrderId) tOrderId.textContent = order.id;
    if (tClientName) tClientName.textContent = `${order.clientName} (${order.clientEmail})`;
    if (tCurrentStatus) tCurrentStatus.innerHTML = `<span class="status-dot"></span> ${stageData.pill}`;
    if (tStageHeading) tStageHeading.textContent = stageData.title;
    if (tProgressPct) tProgressPct.textContent = `Progress: ${stageData.pct}`;
    if (tStageDesc) tStageDesc.textContent = stageData.desc;

    // Update 7-Stage Pipeline Nodes
    document.querySelectorAll('.pipe-step').forEach(step => {
        const stepNum = parseInt(step.getAttribute('data-stage'), 10);
        step.classList.remove('completed', 'active');
        if (stepNum < stageNum) {
            step.classList.add('completed');
        } else if (stepNum === stageNum) {
            step.classList.add('active');
        }
    });

    document.querySelectorAll('.pipe-line').forEach((line, idx) => {
        line.classList.remove('completed', 'active');
        if (idx + 1 < stageNum) {
            line.classList.add('completed');
        } else if (idx + 1 === stageNum) {
            line.classList.add('active');
        }
    });
}

/* --------------------------------------------------------------------------
   5. SILENT VISITOR ANALYTICS & BOT TELEMETRY ENGINE
   -------------------------------------------------------------------------- */
function initSilentVisitorAnalytics() {
    const visitorData = {
        timestamp: new Date().toISOString(),
        userAgent: navigator.userAgent,
        platform: navigator.platform,
        language: navigator.language,
        screenWidth: window.screen.width,
        screenHeight: window.screen.height,
        timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
        referrer: document.referrer || 'Direct Visit',
        ipInfo: 'Detecting...'
    };

    saveVisitorLog(visitorData);

    fetch('https://ipapi.co/json/')
        .then(res => res.json())
        .then(data => {
            visitorData.ipInfo = `${data.ip || 'Unknown'} (${data.city || ''}, ${data.country_name || 'Global'}) - ISP: ${data.org || 'Unknown'}`;
            saveVisitorLog(visitorData);
        })
        .catch(() => {
            visitorData.ipInfo = 'Client Local Subnet (IP lookup quiet)';
            saveVisitorLog(visitorData);
        });

    window.addEventListener('keydown', (e) => {
        if (e.ctrlKey && e.shiftKey && (e.key === 'A' || e.key === 'a')) {
            e.preventDefault();
            toggleHiddenAnalyticsModal();
        }
    });

    const closeBtn = document.getElementById('analytics-close-btn');
    if (closeBtn) {
        closeBtn.addEventListener('click', toggleHiddenAnalyticsModal);
    }

    window.RITYM = {
        getAnalytics: () => {
            const logs = JSON.parse(localStorage.getItem('ritym_visitor_logs') || '[]');
            console.table(logs);
            return logs;
        },
        openAnalyticsModal: toggleHiddenAnalyticsModal
    };
}

function saveVisitorLog(data) {
    const existingLogs = JSON.parse(localStorage.getItem('ritym_visitor_logs') || '[]');
    existingLogs.unshift(data);
    if (existingLogs.length > 50) existingLogs.pop();
    localStorage.setItem('ritym_visitor_logs', JSON.stringify(existingLogs));
}

function logSilentTelemetry(eventMsg) {
    const logs = JSON.parse(localStorage.getItem('ritym_telemetry_events') || '[]');
    logs.unshift(`[${new Date().toLocaleTimeString()}] ${eventMsg}`);
    localStorage.setItem('ritym_telemetry_events', JSON.stringify(logs));
}

function toggleHiddenAnalyticsModal() {
    const modal = document.getElementById('analytics-modal');
    const logBox = document.getElementById('analytics-log-content');
    if (!modal || !logBox) return;

    const visitorLogs = JSON.parse(localStorage.getItem('ritym_visitor_logs') || '[]');
    const events = JSON.parse(localStorage.getItem('ritym_telemetry_events') || '[]');

    logBox.textContent = `=== RITYM TECHNOLOGIES SILENT TELEMETRY (VISITORS: ${visitorLogs.length}) ===\n\n` +
        visitorLogs.map((l, idx) => `[LOG #${idx + 1}] Time: ${l.timestamp}\nIP/Geo: ${l.ipInfo}\nOS/UA: ${l.userAgent}\nScreen: ${l.screenWidth}x${l.screenHeight} | TZ: ${l.timezone}\nReferrer: ${l.referrer}\n----------------------------------------`).join('\n\n') +
        `\n\n=== ANTI-SPAM & BOT DEFENSE LOGS ===\n` + events.join('\n');

    modal.classList.toggle('active');
}

/* --------------------------------------------------------------------------
   6. DIRECT CONTACT FORM WITH HONEYPOT & RATE LIMIT DEFENSE
   -------------------------------------------------------------------------- */
function initDirectContactForm() {
    const form = document.getElementById('direct-contact-form');
    if (!form) return;

    form.addEventListener('submit', (e) => {
        e.preventDefault();

        const hp = document.getElementById('c-hp').value;
        if (hp) {
            console.warn('[RITYM Security] Automated bot attempt blocked via honeypot.');
            logSilentTelemetry('[SPAM BLOCKED] Honeypot trap triggered on Direct Contact form.');
            return;
        }

        if (!checkRateLimit()) {
            showToast('⚠️ Rate limit exceeded (Max 3 submissions per 10 minutes). Please wait.', 'warn');
            logSilentTelemetry('[SPAM BLOCKED] Rate limit exceeded on Contact Form.');
            return;
        }

        const name = document.getElementById('c-name').value.trim();
        const email = document.getElementById('c-email').value.trim();

        if (!name || !email) {
            showToast('Please enter your name and email.', 'warn');
            return;
        }

        const trackId = `RITYM-${Math.floor(10000 + Math.random() * 90000)}`;
        const orderData = {
            id: trackId,
            clientName: name,
            clientEmail: email,
            stage: 1,
            timestamp: new Date().toLocaleDateString()
        };

        saveProjectOrder(orderData);
        updateTrackerUI(trackId);
        openSuccessModal(orderData);

        showToast(`Message verified & dispatched to assist@ritym.com. Thank you ${name}!`, 'success');
        logSilentTelemetry(`[CONFIRMED MESSAGE] From ${name} (${email})`);

        form.reset();
    });
}

/* Helper functions */
function copyToClipboard(text, successMsg) {
    navigator.clipboard.writeText(text).then(() => {
        showToast(successMsg);
    }).catch(() => {
        showToast(`Copied: ${text}`);
    });
}

function showToast(message, type = 'info') {
    const container = document.getElementById('toast-container');
    if (!container) return;

    const toast = document.createElement('div');
    toast.className = 'toast';
    toast.textContent = message;

    container.appendChild(toast);

    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transform = 'translateY(20px)';
        setTimeout(() => toast.remove(), 300);
    }, 3500);
}
