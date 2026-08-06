/* ==========================================================================
   RITYM TECHNOLOGIES — CLIENT LOGIC, WIZARD, ENTERPRISE VISUAL CANVAS CAPTCHA,
   EMAIL DISPATCH & PROJECT LIFECYCLE TRACKER ENGINE
   ========================================================================== */

document.addEventListener('DOMContentLoaded', () => {
    initThemeToggler();
    initVisualCanvasCaptcha();
    initAppWizard();
    initProjectTracker();
    initDirectContactForm();
    initSuccessModal();
});

/* --------------------------------------------------------------------------
   1. ENTERPRISE DISTORTED VISUAL CANVAS CAPTCHA ENGINE
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
            showToast('New security code generated.');
            hideInlineError('c-captcha-error');
        });
    }

    const btnRefreshW = document.getElementById('btn-refresh-w-captcha');
    if (btnRefreshW) {
        btnRefreshW.addEventListener('click', (e) => {
            e.preventDefault();
            refreshWizardCaptcha();
            showToast('New security code generated.');
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
   2. ANTI-SPAM RATE LIMITING SYSTEM (STRICT 5 SUBMISSIONS / 10 MINS)
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
        closeBtn.addEventListener('click', () => {
            modal.classList.remove('active');
            modal.style.display = 'none';
        });
    }

    if (doneBtn && modal) {
        doneBtn.addEventListener('click', () => {
            modal.classList.remove('active');
            modal.style.display = 'none';
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

    if (modal) {
        modal.style.display = 'flex';
        modal.classList.add('active');
    }
}

/* --------------------------------------------------------------------------
   3. ENCRYPTED BACKEND DISPATCH ENGINE
   -------------------------------------------------------------------------- */
function sendRealEmailToAssist(payload) {
    const endpointUser = "assist";
    const endpointDomain = "ritym.com";
    const targetAddress = `${endpointUser}@${endpointDomain}`;
    const formUrl = `https://formsubmit.co/ajax/${targetAddress}`;

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
        console.log('[RITYM Dispatch Status]', data);
    })
    .catch(err => {
        console.warn('[RITYM Dispatch Notice]', err);
    });
}

/* --------------------------------------------------------------------------
   4. INTERACTIVE APP CONFIGURATOR WIZARD
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
        if (hp) return;

        const userInput = document.getElementById('w-captcha-code-input').value.trim().toUpperCase();
        if (!userInput || userInput !== wizardCanvasCaptchaCode) {
            showInlineError('w-captcha-error', 'Security Verification Failed. Incorrect CAPTCHA code. Please type the exact 5 characters shown.');
            showToast('Security verification failed. Incorrect CAPTCHA code.', 'error');
            refreshWizardCaptcha();
            document.getElementById('w-captcha-code-input').value = '';
            document.getElementById('w-captcha-code-input').focus();
            return;
        }

        if (!checkRateLimit()) {
            showInlineError('w-captcha-error', 'Submission limit reached (Maximum 5 requests per 10 minutes per device). Please wait.');
            showToast('Rate limit reached (Max 5 requests per 10 minutes). Please wait.', 'warn');
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
            showInlineError('w-captcha-error', 'Please enter your full name and valid work email address.');
            showToast('Please enter your full name and work email address.', 'warn');
            return;
        }

        const trackId = `RITYM-${Math.floor(10000 + Math.random() * 90000)}`;

        const orderData = {
            id: trackId,
            clientName: name,
            clientEmail: email,
            stage: 1,
            type: "Custom App Configurator",
            details: notes || "No additional concept notes provided.",
            platforms: selectedPlatforms,
            features: selectedFeatures,
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
        openSuccessModal(orderData);

        showToast(`Project Inquiry ${trackId} submitted successfully.`, 'success');

        form.reset();
        hideInlineError('w-captcha-error');
        refreshWizardCaptcha();
        goToStep(1);
    });
}

/* --------------------------------------------------------------------------
   5. PROJECT LIFECYCLE TRACKER ENGINE
   -------------------------------------------------------------------------- */
const STAGE_CONFIG = {
    1: {
        title: "Stage 1: REQUEST_RECEIVED (Open)",
        pill: "Stage 1: REQUEST_RECEIVED",
        pct: "15%",
        desc: "Request logged into engineering queue. Scope documentation issued for sign-off."
    },
    2: {
        title: "Stage 2: IN_REVIEW (Architect Review)",
        pill: "Stage 2: IN_REVIEW",
        pct: "30%",
        desc: "Senior engineering architect reviewing project specifications, tech stack compatibility, and security requirements."
    },
    3: {
        title: "Stage 3: ASSIGNED (Team Allocated)",
        pill: "Stage 3: ASSIGNED",
        pct: "45%",
        desc: "Lead Android developer, backend engineer, and QA specialist allocated. Architecture diagram & sprint plan approved."
    },
    4: {
        title: "Stage 4: IN_DEVELOPMENT (Active Build)",
        pill: "Stage 4: IN_DEVELOPMENT",
        pct: "65%",
        desc: "Core sprint execution in progress. MVVM modules, UI components, and API integration are actively compiling."
    },
    5: {
        title: "Stage 5: VALIDATION (QA & Testing)",
        pill: "Stage 5: VALIDATION",
        pct: "80%",
        desc: "Automated unit testing, security audit, memory checks, and multi-device Android validation underway."
    },
    6: {
        title: "Stage 6: DOCUMENTATION (Docs & Specs)",
        pill: "Stage 6: DOCUMENTATION",
        pct: "90%",
        desc: "API documentation, user manuals, deployment manifests, and clean source code packaging prepared."
    },
    7: {
        title: "Stage 7: BUILD_RELEASE (Play Store Release)",
        pill: "Stage 7: BUILD_RELEASE",
        pct: "100%",
        desc: "Final App Bundle (.aab) compiled, Play Store submission completed, and full IP codebase delivered."
    },
    8: {
        title: "Action Required: Waiting for Additional Information",
        pill: "WAITING_ON_CLIENT",
        pct: "Paused",
        desc: "Our engineering team requires additional specifications regarding your project requirements. Please check your inbox or respond to our latest update."
    },
    9: {
        title: "Project Status: Request Closed",
        pill: "REJECTED / CLOSED",
        pct: "Closed",
        desc: "This project request could not be accepted due to scope constraints or technical feasibility. Please submit a new inquiry or contact our team."
    }
};

function initProjectTracker() {
    const btnLookup = document.getElementById('btn-lookup-status');
    const inputTrackId = document.getElementById('track-id-input');

    if (btnLookup && inputTrackId) {
        btnLookup.addEventListener('click', () => {
            const queryId = inputTrackId.value.trim().toUpperCase();
            if (queryId) {
                updateTrackerUI(queryId);
            } else {
                showToast('Please enter a valid Tracking ID.', 'warn');
            }
        });
    }
}

function getStoredProjectOrders() {
    return JSON.parse(localStorage.getItem('ritym_project_orders') || '{}');
}

function saveProjectOrder(order) {
    const orders = getStoredProjectOrders();
    orders[order.id] = order;
    localStorage.setItem('ritym_project_orders', JSON.stringify(orders));
}

function updateTrackerUI(trackId) {
    const orders = getStoredProjectOrders();
    const outputCard = document.getElementById('tracker-output-card');

    let order = orders[trackId];
    if (!order) {
        showToast(`No project found with Tracking ID: ${trackId}`, 'warn');
        if (outputCard) outputCard.style.display = 'none';
        return;
    }

    if (outputCard) outputCard.style.display = 'block';

    const stageNum = order.stage || 1;
    const stageData = STAGE_CONFIG[stageNum] || STAGE_CONFIG[1];

    const tOrderId = document.getElementById('t-order-id');
    const tClientName = document.getElementById('t-client-name');
    const tCurrentStatus = document.getElementById('t-current-status');
    const tStageHeading = document.getElementById('t-stage-heading');
    const tProgressPct = document.getElementById('t-progress-pct');
    const tStageDesc = document.getElementById('t-stage-desc');

    if (tOrderId) tOrderId.textContent = order.id;
    if (tClientName) tClientName.textContent = `${order.clientName}`;

    if (tCurrentStatus) {
        tCurrentStatus.className = 't-status-pill';
        if (stageNum === 8) {
            tCurrentStatus.classList.add('status-waiting');
        } else if (stageNum === 9) {
            tCurrentStatus.classList.add('status-rejected');
        } else {
            tCurrentStatus.classList.add('status-in-dev');
        }
        tCurrentStatus.innerHTML = `<span class="status-dot"></span> ${stageData.pill}`;
    }

    if (tStageHeading) tStageHeading.textContent = stageData.title;
    if (tProgressPct) tProgressPct.textContent = `Progress: ${stageData.pct}`;
    if (tStageDesc) tStageDesc.textContent = stageData.desc;

    document.querySelectorAll('.pipe-step').forEach(step => {
        const stepNum = parseInt(step.getAttribute('data-stage'), 10);
        step.classList.remove('completed', 'active');

        if (stageNum === 8 || stageNum === 9) {
            if (stepNum === 1) step.classList.add('active');
        } else {
            if (stepNum < stageNum) {
                step.classList.add('completed');
            } else if (stepNum === stageNum) {
                step.classList.add('active');
            }
        }
    });

    document.querySelectorAll('.pipe-line').forEach((line, idx) => {
        line.classList.remove('completed', 'active');
        if (stageNum !== 8 && stageNum !== 9) {
            if (idx + 1 < stageNum) {
                line.classList.add('completed');
            } else if (idx + 1 === stageNum) {
                line.classList.add('active');
            }
        }
    });
}

/* --------------------------------------------------------------------------
   6. DIRECT CONTACT FORM ENGINE
   -------------------------------------------------------------------------- */
function initDirectContactForm() {
    const form = document.getElementById('direct-contact-form');
    if (!form) return;

    form.addEventListener('submit', (e) => {
        e.preventDefault();
        hideInlineError('c-captcha-error');

        const hp = document.getElementById('c-hp').value;
        if (hp) return;

        const userInput = document.getElementById('c-captcha-code-input').value.trim().toUpperCase();
        if (!userInput || userInput !== contactCanvasCaptchaCode) {
            showInlineError('c-captcha-error', 'Security Verification Failed. Incorrect CAPTCHA code. Please type the exact 5 characters shown.');
            showToast('Security verification failed. Incorrect CAPTCHA code.', 'error');
            refreshContactCaptcha();
            document.getElementById('c-captcha-code-input').value = '';
            document.getElementById('c-captcha-code-input').focus();
            return;
        }

        if (!checkRateLimit()) {
            showInlineError('c-captcha-error', 'Submission limit reached (Maximum 5 requests per 10 minutes per device). Please wait.');
            showToast('Rate limit reached (Max 5 requests per 10 minutes). Please wait.', 'warn');
            return;
        }

        const name = document.getElementById('c-name').value.trim();
        const email = document.getElementById('c-email').value.trim();
        const message = document.getElementById('c-message').value.trim();

        if (!name || !email || !message) {
            showInlineError('c-captcha-error', 'Please fill in all fields (Name, Work Email, and Description).');
            showToast('Please fill in all fields.', 'warn');
            return;
        }

        const trackId = `RITYM-${Math.floor(10000 + Math.random() * 90000)}`;
        const orderData = {
            id: trackId,
            clientName: name,
            clientEmail: email,
            type: "Direct Contact Inquiry",
            details: message,
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
        openSuccessModal(orderData);

        showToast(`Inquiry ${trackId} submitted successfully.`, 'success');

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

/* Theme Toggler Logic */
function initThemeToggler() {
    const currentTheme = localStorage.getItem('ritym-theme') || 'light';
    if (currentTheme === 'dark') {
        document.body.classList.add('dark-theme');
    }

    const toggleBtn = document.getElementById('theme-toggle-btn');
    if (toggleBtn) {
        toggleBtn.addEventListener('click', () => {
            document.body.classList.toggle('dark-theme');
            let theme = 'light';
            if (document.body.classList.contains('dark-theme')) {
                theme = 'dark';
            }
            localStorage.setItem('ritym-theme', theme);
            showToast(`Theme switched to ${theme} mode.`);
        });
    }
}

/* Portal & Licensing Simulator (Strictly client-side mock for payment validation/restores) */
function initPortalSimulator() {
    const actBtn = document.getElementById('activate-license-btn');
    if (actBtn) {
        actBtn.addEventListener('click', (e) => {
            e.preventDefault();
            const keyInput = document.getElementById('license-key');
            if (keyInput && keyInput.value.trim().length > 10) {
                showToast("License key validated and activated successfully!", "success");
            } else {
                showToast("Invalid license key format. Please verify.", "error");
            }
        });
    }

    const restoreBtn = document.getElementById('restore-purchase-btn');
    if (restoreBtn) {
        restoreBtn.addEventListener('click', (e) => {
            e.preventDefault();
            const emailInput = document.getElementById('restore-email');
            if (emailInput && emailInput.value.includes('@')) {
                showToast("Verification code sent to your email to restore purchase history.", "success");
            } else {
                showToast("Please enter a valid email address.", "error");
            }
        });
    }
}

// Automatically bind portal logic if forms exist
document.addEventListener('DOMContentLoaded', initPortalSimulator);

