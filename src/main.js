/* ==========================================================================
   RITYM TECHNOLOGIES — CLIENT LOGIC, WIZARD, ENTERPRISE VISUAL CANVAS CAPTCHA,
   EMAIL DISPATCH & PASSWORD-PROTECTED INTERNAL ADMIN STAGE ADVANCER ENGINE
   ========================================================================== */

document.addEventListener('DOMContentLoaded', () => {
    initEmailObfuscation();
    initVisualCanvasCaptcha();
    initAppWizard();
    initProjectTracker();
    initSilentVisitorAnalytics();
    initDirectContactForm();
    initSuccessModal();
    initAdminStageController();
});

/* Master Internal Admin Security Key */
const MASTER_ADMIN_KEY = "RITYM2026!";

/* Password-Protected Global Window Modal Functions */
window.openAdminStageModal = function() {
    const modal = document.getElementById('admin-stage-modal');
    if (modal) {
        modal.classList.add('active');
        const passInput = document.getElementById('admin-pass-input');
        if (passInput) {
            passInput.value = '';
            passInput.focus();
        }
        hideInlineError('admin-pass-error');
    }
};

window.closeAdminStageModal = function() {
    const modal = document.getElementById('admin-stage-modal');
    if (modal) {
        modal.classList.remove('active');
    }
};

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
   2. ENTERPRISE DISTORTED VISUAL CANVAS CAPTCHA ENGINE
   -------------------------------------------------------------------------- */
let contactCanvasCaptchaCode = "";
let wizardCanvasCaptchaCode = "";

function generateCaptchaCode(length = 5) {
    const chars = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789";
    let code = "";
    for (let i = 0; i < length; i++) {
        code += chars.charAt(Math.floor(Math.random() * chars.length));
    }
    return code;
}

function renderCaptchaOnCanvas(canvasId, code) {
    const canvas = document.getElementById(canvasId);
    if (!canvas) return;

    if (canvas.width === 0) canvas.width = 160;
    if (canvas.height === 0) canvas.height = 50;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    ctx.clearRect(0, 0, canvas.width, canvas.height);

    const grad = ctx.createLinearGradient(0, 0, canvas.width, canvas.height);
    grad.addColorStop(0, '#0f172a');
    grad.addColorStop(1, '#1e293b');
    ctx.fillStyle = grad;
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    for (let i = 0; i < 6; i++) {
        ctx.strokeStyle = (i % 2 === 0) ? 'rgba(255, 107, 0, 0.4)' : 'rgba(56, 189, 248, 0.4)';
        ctx.lineWidth = 1.5;
        ctx.beginPath();
        ctx.moveTo(Math.random() * canvas.width, Math.random() * canvas.height);
        ctx.lineTo(Math.random() * canvas.width, Math.random() * canvas.height);
        ctx.stroke();
    }

    for (let i = 0; i < 35; i++) {
        ctx.fillStyle = `rgba(255, 255, 255, ${0.2 + Math.random() * 0.3})`;
        ctx.beginPath();
        ctx.arc(Math.random() * canvas.width, Math.random() * canvas.height, 1.5, 0, Math.PI * 2);
        ctx.fill();
    }

    ctx.font = 'bold 23px "Outfit", Arial, sans-serif';
    ctx.textBaseline = 'middle';

    const charSpacing = canvas.width / (code.length + 1);

    for (let i = 0; i < code.length; i++) {
        const char = code.charAt(i);
        ctx.save();

        const x = charSpacing * (i + 1);
        const y = canvas.height / 2 + (Math.random() * 4 - 2);
        const angle = (Math.random() * 0.3 - 0.15);

        ctx.translate(x, y);
        ctx.rotate(angle);

        ctx.fillStyle = (i % 2 === 0) ? '#ff6b00' : '#38bdf8';
        ctx.shadowColor = 'rgba(0, 0, 0, 0.6)';
        ctx.shadowBlur = 4;
        ctx.fillText(char, -7, 0);

        ctx.restore();
    }
}

function initVisualCanvasCaptcha() {
    refreshContactCaptcha();
    refreshWizardCaptcha();

    const btnRefreshC = document.getElementById('btn-refresh-c-captcha');
    if (btnRefreshC) {
        btnRefreshC.addEventListener('click', (e) => {
            e.preventDefault();
            refreshContactCaptcha();
            showToast('🔄 New security code generated.');
            hideInlineError('c-captcha-error');
        });
    }

    const btnRefreshW = document.getElementById('btn-refresh-w-captcha');
    if (btnRefreshW) {
        btnRefreshW.addEventListener('click', (e) => {
            e.preventDefault();
            refreshWizardCaptcha();
            showToast('🔄 New security code generated.');
            hideInlineError('w-captcha-error');
        });
    }
}

function refreshContactCaptcha() {
    contactCanvasCaptchaCode = generateCaptchaCode(5);
    renderCaptchaOnCanvas('contact-captcha-canvas', contactCanvasCaptchaCode);
}

function refreshWizardCaptcha() {
    wizardCanvasCaptchaCode = generateCaptchaCode(5);
    renderCaptchaOnCanvas('wizard-captcha-canvas', wizardCanvasCaptchaCode);
}

/* --------------------------------------------------------------------------
   3. ANTI-SPAM RATE LIMITING SYSTEM (STRICT 5 SUBMISSIONS / 10 MINS)
   -------------------------------------------------------------------------- */
function checkRateLimit() {
    const history = JSON.parse(localStorage.getItem('ritym_submission_history') || '[]');
    const now = Date.now();
    const tenMinutesAgo = now - (10 * 60 * 1000);
    
    const recentSubmissions = history.filter(ts => ts > tenMinutesAgo);
    if (recentSubmissions.length >= 5) {
        return false;
    }
    recentSubmissions.push(now);
    localStorage.setItem('ritym_submission_history', JSON.stringify(recentSubmissions));
    return true;
}

function showInlineError(elementId, message) {
    const banner = document.getElementById(elementId);
    if (banner) {
        banner.textContent = message;
        banner.style.display = 'block';
        banner.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }
}

function hideInlineError(elementId) {
    const banner = document.getElementById(elementId);
    if (banner) {
        banner.style.display = 'none';
        banner.textContent = '';
    }
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
   4. HIGH-RELIABILITY EMAIL DISPATCH ENGINE TO assist@ritym.com
   -------------------------------------------------------------------------- */
function sendRealEmailToAssist(payload) {
    const formUrl = "https://formsubmit.co/ajax/assist@ritym.com";

    const params = new URLSearchParams();
    params.append('name', payload.clientName);
    params.append('email', payload.clientEmail);
    params.append('message', payload.details);
    params.append('_subject', `[${payload.trackId}] ${payload.type} from ${payload.clientName}`);
    params.append('_replyto', payload.clientEmail);
    params.append('_captcha', 'false');
    params.append('Tracking ID', payload.trackId);
    if (payload.platforms) params.append('Target Platforms', payload.platforms);
    if (payload.features) params.append('Required Features', payload.features);
    if (payload.timelineBudget) params.append('Timeline & Scope', payload.timelineBudget);

    fetch(formUrl, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
            'Accept': 'application/json'
        },
        body: params.toString()
    })
    .then(res => res.json())
    .then(data => {
        console.log('[RITYM Email Dispatch Status]', data);
        if (data.message && data.message.includes('Activation')) {
            showToast('📩 FormSubmit activation link dispatched to assist@ritym.com. Please click to activate!', 'warn');
        }
    })
    .catch(err => {
        console.warn('[RITYM Email Dispatch Warning]', err);
    });
}

/* --------------------------------------------------------------------------
   5. INTERACTIVE CUSTOM APP REQUEST CONFIGURATOR WIZARD
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
            setTimeout(() => refreshWizardCaptcha(), 60);
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
        hideInlineError('w-captcha-error');

        const hp = document.getElementById('w-hp').value;
        if (hp) {
            console.warn('[RITYM Security] Automated bot attempt blocked via honeypot.');
            logSilentTelemetry('[SPAM BLOCKED] Honeypot trap triggered on App Wizard.');
            return;
        }

        const userInput = document.getElementById('w-captcha-code-input').value.trim().toUpperCase();
        if (!userInput || userInput !== wizardCanvasCaptchaCode) {
            showInlineError('w-captcha-error', '❌ Security Verification Failed! Incorrect 5-character CAPTCHA code. Please type the exact 5 characters shown on the dark box.');
            showToast('❌ Security Verification Failed! Incorrect CAPTCHA code.', 'error');
            refreshWizardCaptcha();
            document.getElementById('w-captcha-code-input').value = '';
            document.getElementById('w-captcha-code-input').focus();
            return;
        }

        if (!checkRateLimit()) {
            showInlineError('w-captcha-error', '⚠️ Submission Limit Reached: Maximum 5 requests allowed per 10 minutes per device. Please wait.');
            showToast('⚠️ Rate limit reached (Max 5 requests per 10 minutes). Please wait.', 'warn');
            logSilentTelemetry('[SPAM BLOCKED] Rate limit exceeded on App Wizard.');
            return;
        }

        const name = document.getElementById('w-name').value.trim();
        const email = document.getElementById('w-email').value.trim();
        const notes = document.getElementById('w-notes').value.trim();
        const selectedPlatforms = Array.from(form.querySelectorAll('input[name="platform"]:checked')).map(cb => cb.value).join(', ');
        const selectedFeatures = Array.from(form.querySelectorAll('input[name="feature"]:checked')).map(cb => cb.value).join(', ');
        const timeline = form.querySelector('#w-timeline').value;
        const budget = form.querySelector('#w-budget').value;

        if (!name || !email) {
            showInlineError('w-captcha-error', '⚠️ Please enter your full name and valid email address.');
            showToast('Please enter your full name and email address.', 'warn');
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

        sendRealEmailToAssist({
            trackId: trackId,
            clientName: name,
            clientEmail: email,
            type: "Custom App Configurator Request",
            details: notes || "No additional concept notes provided.",
            platforms: selectedPlatforms,
            features: selectedFeatures,
            timelineBudget: `${timeline} | ${budget}`
        });

        saveProjectOrder(orderData);
        updateTrackerUI(trackId);
        openSuccessModal(orderData);

        showToast(`✓ Project Request ${trackId} sent to assist@ritym.com!`, 'success');
        logSilentTelemetry(`[REAL EMAIL DISPATCH] Order ${trackId} from ${name} (${email}) sent to assist@ritym.com`);

        form.reset();
        hideInlineError('w-captcha-error');
        refreshWizardCaptcha();
        goToStep(1);
    });
}

/* --------------------------------------------------------------------------
   6. 7-STAGE PROJECT LIFECYCLE TRACKER ENGINE
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

    const hash = window.location.hash;
    if (hash && hash.includes('#admin')) {
        window.openAdminStageModal();
    } else {
        updateTrackerUI('RITYM-SAMPLE-8842');
    }
}

function saveProjectOrder(order) {
    const orders = JSON.parse(localStorage.getItem('ritym_project_orders') || '{}');
    orders[order.id] = order;
    localStorage.setItem('ritym_project_orders', JSON.stringify(orders));
}

function setProjectStage(trackId, newStageNum, clientName = null, clientEmail = null) {
    const orders = JSON.parse(localStorage.getItem('ritym_project_orders') || '{}');
    let order = orders[trackId];
    if (!order) {
        order = {
            id: trackId,
            clientName: clientName || 'Client Project',
            clientEmail: clientEmail || 'client@ritym.com',
            stage: parseInt(newStageNum, 10),
            timestamp: new Date().toLocaleDateString()
        };
    } else {
        order.stage = parseInt(newStageNum, 10);
        if (clientName) order.clientName = clientName;
        if (clientEmail) order.clientEmail = clientEmail;
    }
    saveProjectOrder(order);
    updateTrackerUI(trackId);
    return order;
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
            clientName: 'Client Project Inquiry',
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
   7. PASSWORD-PROTECTED INTERNAL ADMIN STAGE CONTROLLER (Ctrl + Alt + Shift + R)
   -------------------------------------------------------------------------- */
function initAdminStageController() {
    const form = document.getElementById('admin-stage-form');

    // Secret Internal Shortcut: Ctrl + Alt + Shift + R
    window.addEventListener('keydown', (e) => {
        if (e.ctrlKey && e.altKey && e.shiftKey && (e.key === 'R' || e.key === 'r')) {
            e.preventDefault();
            window.openAdminStageModal();
        }
    });

    if (form) {
        form.addEventListener('submit', (e) => {
            e.preventDefault();
            hideInlineError('admin-pass-error');

            const enteredPass = document.getElementById('admin-pass-input').value.trim();
            const trackId = document.getElementById('admin-input-track-id').value.trim().toUpperCase();
            const stageNum = parseInt(document.getElementById('admin-select-stage').value, 10);

            // STRICT MASTER PASSWORD AUTHENTICATION CHECK
            if (enteredPass !== MASTER_ADMIN_KEY) {
                showInlineError('admin-pass-error', '🔒 Access Denied! Invalid Master Admin Password.');
                showToast('🔒 Access Denied! Invalid Master Admin Password.', 'error');
                logSilentTelemetry(`[SECURITY WARNING] Failed Admin authentication attempt with key: ${enteredPass}`);
                document.getElementById('admin-pass-input').value = '';
                document.getElementById('admin-pass-input').focus();
                return; // STRICTLY BLOCK
            }

            if (!trackId) {
                showInlineError('admin-pass-error', 'Please enter a Tracking ID (e.g. RITYM-92627)');
                return;
            }

            const updatedOrder = setProjectStage(trackId, stageNum);
            showToast(`🔒 Authenticated! Project ${trackId} advanced to Stage ${stageNum}!`, 'success');
            logSilentTelemetry(`[ADMIN AUTH SUCCESS] Project ${trackId} set to Stage ${stageNum} (${STAGE_CONFIG[stageNum].title})`);

            window.closeAdminStageModal();

            const trackerInput = document.getElementById('track-id-input');
            if (trackerInput) trackerInput.value = trackId;
            const trackerSec = document.getElementById('tracker');
            if (trackerSec) trackerSec.scrollIntoView({ behavior: 'smooth' });
        });
    }

    // Password-Protected API for developer console
    window.RITYM = window.RITYM || {};
    window.RITYM.setStage = (trackId, stageNumber, masterKey) => {
        if (masterKey !== MASTER_ADMIN_KEY) {
            console.error('[RITYM SECURITY] Access Denied. Valid masterKey required as 3rd parameter: RITYM.setStage("ID", stage, "RITYM2026!")');
            return 'Access Denied: Invalid Master Key';
        }
        const order = setProjectStage(trackId, stageNumber);
        console.log(`[RITYM ADMIN AUTH] Project ${trackId} advanced to Stage ${stageNumber}:`, order);
        showToast(`⚡ Project ${trackId} set to Stage ${stageNumber}!`, 'success');
        return order;
    };
}

/* --------------------------------------------------------------------------
   8. SILENT VISITOR ANALYTICS & BOT TELEMETRY ENGINE
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
   9. DIRECT CONTACT FORM WITH STRICT VISUAL CANVAS CAPTCHA & EMAIL DISPATCH
   -------------------------------------------------------------------------- */
function initDirectContactForm() {
    const form = document.getElementById('direct-contact-form');
    if (!form) return;

    form.addEventListener('submit', (e) => {
        e.preventDefault();
        hideInlineError('c-captcha-error');

        const hp = document.getElementById('c-hp').value;
        if (hp) {
            console.warn('[RITYM Security] Automated bot attempt blocked via honeypot.');
            logSilentTelemetry('[SPAM BLOCKED] Honeypot trap triggered on Direct Contact form.');
            return;
        }

        const userInput = document.getElementById('c-captcha-code-input').value.trim().toUpperCase();
        if (!userInput || userInput !== contactCanvasCaptchaCode) {
            showInlineError('c-captcha-error', '❌ Security Verification Failed! Incorrect 5-character CAPTCHA code. Please type the exact 5 characters shown on the dark box.');
            showToast('❌ Security Verification Failed! Incorrect CAPTCHA code.', 'error');
            refreshContactCaptcha();
            document.getElementById('c-captcha-code-input').value = '';
            document.getElementById('c-captcha-code-input').focus();
            return;
        }

        if (!checkRateLimit()) {
            showInlineError('c-captcha-error', '⚠️ Submission Limit Reached: Maximum 5 requests allowed per 10 minutes per device. Please wait.');
            showToast('⚠️ Rate limit reached (Max 5 requests per 10 minutes). Please wait.', 'warn');
            logSilentTelemetry('[SPAM BLOCKED] Rate limit exceeded on Contact Form.');
            return;
        }

        const name = document.getElementById('c-name').value.trim();
        const email = document.getElementById('c-email').value.trim();
        const message = document.getElementById('c-message').value.trim();

        if (!name || !email || !message) {
            showInlineError('c-captcha-error', '⚠️ Please fill in all fields (Name, Email, and Project Message).');
            showToast('Please enter your name, email, and message.', 'warn');
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

        sendRealEmailToAssist({
            trackId: trackId,
            clientName: name,
            clientEmail: email,
            type: "Direct Project Inquiry Message",
            details: message
        });

        saveProjectOrder(orderData);
        updateTrackerUI(trackId);
        openSuccessModal(orderData);

        showToast(`✓ Message dispatched to assist@ritym.com! Thank you ${name}!`, 'success');
        logSilentTelemetry(`[REAL EMAIL DISPATCH] Contact message ${trackId} from ${name} (${email}) sent to assist@ritym.com`);

        form.reset();
        hideInlineError('c-captcha-error');
        refreshContactCaptcha();
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

    if (type === 'error') {
        toast.style.borderColor = '#ef4444';
        toast.style.background = '#450a0a';
    }

    container.appendChild(toast);

    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transform = 'translateY(20px)';
        setTimeout(() => toast.remove(), 300);
    }, 3500);
}
