// Variáveis Globais (Preserva valores injetados pelo servidor se existirem)
window.currentRole = window.currentRole || null;
window.currentUser = window.currentUser || null;
window.editMode = false;
window.currentSchedule = [];
window.currentResource = 'lab1';
window.currentShift = 'Matutino';

const DIAS = ['Segunda', 'Terça', 'Quarta', 'Quinta', 'Sexta'];
const HORARIOS_PERIODOS = {
    'Matutino': { 'Aula 1': '07:00', 'Aula 2': '07:47', 'Aula 3': '08:34', 'INT': '09:15', 'Aula 4': '09:35', 'Aula 5': '10:23', 'Aula 6': '11:11' },
    'Vespertino': { 'Aula 1': '13:00', 'Aula 2': '13:45', 'Aula 3': '14:30', 'INT': '15:15', 'Aula 4': '15:35', 'Aula 5': '16:23', 'Aula 6': '17:11' },
    'Noturno': { 'Aula 1': '18:40', 'Aula 2': '19:25', 'INT': '20:10', 'Aula 3': '20:25', 'Aula 4': '21:12' }
};

// Inicialização
document.addEventListener('DOMContentLoaded', () => {
    const monday = getMonday(new Date()).toISOString().split('T')[0];
    const semanaInput = document.getElementById('semanaSelect');
    if (semanaInput) semanaInput.value = monday;

    updateShift('Matutino');

    checkAuth();
    loadConfig();
    loadResources();
    loadProfessores();

    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
            document.querySelectorAll('.modal-overlay').forEach(modal => {
                modal.style.display = 'none';
            });
        }
    });

    document.addEventListener('click', (e) => {
        if (e.target.classList.contains('modal-overlay')) {
            e.target.style.display = 'none';
        }
    });
});

async function checkAuth() {
    try {
        const res = await fetch('/api/auth/me');
        const data = await res.json();
        if (!data.logged) {
            window.currentUser = null;
            window.currentRole = null;
            updateUserUI("Visitante");
        } else {
            window.currentUser = data.user;
            window.currentRole = data.role;
            updateUserUI(data.nome);
        }
    } catch (e) {
        console.error("Erro na autenticação:", e);
    }
}

function updateUserUI(nome) {
    const userNameEl = document.getElementById('userName');
    if (userNameEl) userNameEl.innerText = nome === "Visitante" ? "Visitante (Apenas Leitura)" : `Usuário: ${nome}`;

    const schoolNameLabel = document.getElementById('schoolName');
    const coordinatorNameLabel = document.getElementById('coordinatorName');
    const loginBtn = document.getElementById('loginBtnHeader');
    const exitBtn = document.getElementById('logoutBtn');
    const btnChangePassword = document.getElementById('btnChangePassword');
    const selectionBar = document.getElementById('selectionBar');

    const shiftSelectorVisitor = document.getElementById('shiftSelectorVisitor');
    const resourceSelectorVisitor = document.getElementById('resourceSelectorVisitor');
    if (shiftSelectorVisitor) shiftSelectorVisitor.style.display = 'flex';
    if (resourceSelectorVisitor) resourceSelectorVisitor.style.display = 'flex';

    const groupTurma = document.getElementById('group-turma');
    const groupProf = document.getElementById('group-professor');
    const groupFreq = document.getElementById('group-frequencia');
    const groupTipo = document.getElementById('group-tipo-agendamento');
    const btnEditGrid = document.getElementById('btnEditGrid');

    if (selectionBar) selectionBar.style.display = 'flex';

    if (window.currentRole === 'admin' || window.currentRole === 'root') {
        if (schoolNameLabel) schoolNameLabel.contentEditable = true;
        if (coordinatorNameLabel) coordinatorNameLabel.contentEditable = true;
        setupBrandListeners();

        ['btnUploadProf', 'btnUploadTurma', 'btnExportUsers', 'btnResetSystem', 'btnOpenDashboard', 'btnSettings'].forEach(id => {
            const el = document.getElementById(id);
            if (el) {
                // btnSettings uses flex for centering the icon
                el.style.display = (id === 'btnSettings') ? 'flex' : 'block';
            }
        });

        if (groupTipo) groupTipo.style.display = 'flex';
        if (groupTurma) groupTurma.style.display = 'flex';
        if (groupProf) groupProf.style.display = 'flex';
        if (groupFreq) groupFreq.style.display = 'flex';
        if (btnEditGrid) btnEditGrid.style.display = 'block';
    } else if (window.currentRole === 'professor') {
        if (schoolNameLabel) schoolNameLabel.contentEditable = false;

        const profSelect = document.getElementById('profSelect');
        if (profSelect) {
            profSelect.value = nome;
            profSelect.disabled = true;
        }

        const freqSelect = document.getElementById('freqSelect');
        if (freqSelect) {
            freqSelect.value = 'diaria';
            // Ocultar seleções recorrentes para professores (ele não precisa saber que existem)
            Array.from(freqSelect.options).forEach(opt => {
                if (opt.value !== 'diaria') opt.style.display = 'none';
                else opt.style.display = 'block';
            });
        }

        if (groupTipo) groupTipo.style.display = 'none';
        if (groupTurma) groupTurma.style.display = 'flex';
        if (groupProf) groupProf.style.display = 'flex';
        if (groupFreq) groupFreq.style.display = 'flex';
        if (btnEditGrid) btnEditGrid.style.display = 'block';
    } else {
        if (schoolNameLabel) schoolNameLabel.contentEditable = false;
        if (groupTipo) groupTipo.style.display = 'none';
        if (groupTurma) groupTurma.style.display = 'none';
        if (groupProf) groupProf.style.display = 'none';
        if (groupFreq) groupFreq.style.display = 'none';
        if (btnEditGrid) btnEditGrid.style.display = 'none';

        ['btnUploadProf', 'btnUploadTurma', 'btnExportUsers', 'btnResetSystem'].forEach(id => {
            const el = document.getElementById(id);
            if (el) el.style.display = 'none';
        });
    }

    if (exitBtn) exitBtn.style.display = (window.currentUser ? 'block' : 'none');
    if (btnChangePassword) btnChangePassword.style.display = (window.currentUser ? 'block' : 'none');
    if (loginBtn) loginBtn.style.display = (window.currentUser ? 'none' : 'block');

    // Avisar o módulo de debug sobre a possível mudança de papel (Role)
    if (window.DebugResolution) window.DebugResolution.update();

    enableGrid();
}

async function handleLogin(e) {
    e.preventDefault();
    const formData = new FormData(e.target);
    const data = Object.fromEntries(formData);
    const res = await fetch('/api/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
    });
    const result = await res.json();
    if (result.success) {
        closeModal('loginModal');
        window.currentUser = result.user;
        window.currentRole = result.role;
        updateUserUI(result.nome);
        await loadConfig();
        loadSchedule();
    } else {
        alert(result.error);
    }
}

async function logout() {
    await fetch('/api/auth/logout', { method: 'POST' });
    location.reload();
}

async function loadResources() {
    const res = await fetch('/api/recursos');
    const recursos = await res.json();
    const containerVisitor = document.getElementById('resourceSelectorVisitor');

    // Filter out inactive resources for the selector
    const activeRecursos = recursos.filter(r => r.active !== false);

    if (containerVisitor) containerVisitor.innerHTML = '';

    activeRecursos.forEach(r => {
        const isActive = r.id === window.currentResource;
        if (containerVisitor) {
            const btn = document.createElement('button');
            btn.className = isActive ? 'active' : '';
            btn.textContent = r.nome.toUpperCase();
            btn.dataset.id = r.id;
            btn.onclick = () => selectResource(r.id);
            containerVisitor.appendChild(btn);
        }
    });

    // Also update global resource list if needed
    window.allResources = recursos;
}

function selectResource(id) {
    window.currentResource = id;
    document.querySelectorAll('.floating-resource-selector button').forEach(c => {
        c.classList.toggle('active', c.dataset.id === id);
    });
    loadSchedule();
}

async function loadProfessores() {
    const res = await fetch('/api/professores');
    const profs = await res.json();
    const select = document.getElementById('profSelect');
    if (select) {
        select.innerHTML = '<option value="">Selecione</option>';
        profs.forEach(p => select.innerHTML += `<option value="${p}">${p}</option>`);
    }
}

async function onTurnoChange() {
    const turno = window.currentShift;
    const turmaSelect = document.getElementById('turmaSelect');

    const res = await fetch(`/api/turmas?turno=${turno}`);
    const turmas = await res.json();
    if (turmaSelect) {
        turmaSelect.disabled = false;
        turmaSelect.innerHTML = '<option value="">Selecione</option>';
        // Filtra turmas ativas
        const activeTurmas = turmas.filter(t => t.active !== false);
        activeTurmas.forEach(t => turmaSelect.innerHTML += `<option value="${t.turma}">${t.turma}</option>`);
    }

    renderGridStructure(turno);
    loadSchedule();
    enableGrid();
}

function renderGridStructure(turno) {
    const tbody = document.getElementById('gridBody');
    if (!tbody) return;
    tbody.innerHTML = '';
    const periodos = Object.keys(HORARIOS_PERIODOS[turno]);

    periodos.forEach(p => {
        const tr = document.createElement('tr');
        const horaStart = HORARIOS_PERIODOS[turno][p];
        if (p === 'INT') {
            tr.className = 'intervalo-row';
            tr.innerHTML = `<td class="period-label">INT<br><small>${horaStart}</small></td>`;
            DIAS.forEach(() => {
                const td = document.createElement('td');
                td.className = 'intervalo-cell';
                td.textContent = 'INTERVALO';
                tr.appendChild(td);
            });
        } else {
            tr.innerHTML = `<td class="period-label">${p}<br><small>${horaStart}</small></td>`;
            DIAS.forEach((dia, index) => {
                const semanaInput = document.getElementById('semanaSelect');
                const semana = semanaInput ? semanaInput.value : '';
                const isDisabled = checkIsPast(semana, index, horaStart);
                const td = document.createElement('td');
                const slot = document.createElement('div');
                slot.className = 'slot' + (isDisabled ? ' disabled' : '');
                slot.id = `slot-${dia}-${p}`;
                if (!isDisabled) slot.onclick = () => onSlotClick(dia, p);
                slot.innerHTML = '<span class="placeholder">+</span>';
                td.appendChild(slot);
                tr.appendChild(td);
            });
        }
        tbody.appendChild(tr);
    });
}

function checkIsPast(semanaStr, diaIndex, horaStr) {
    if (!semanaStr || !horaStr) return false;
    const [year, month, day] = semanaStr.split('-').map(Number);
    const date = new Date(year, month - 1, day, 12, 0, 0);
    date.setDate(date.getDate() + diaIndex);
    const [h, m] = horaStr.split(':').map(Number);
    date.setHours(h, m, 0, 0);
    return date < new Date();
}

function enableGrid() {
    const btnEdit = document.getElementById('btnEditGrid');
    if (!btnEdit) return;
    const tipo = document.getElementById('tipoAgendamentoSelect')?.value || 'aula';
    const turno = window.currentShift;

    if (tipo === 'evento') {
        const resp = document.getElementById('eventoRespInput')?.value || '';
        const desc = document.getElementById('eventoDescInput')?.value || '';
        btnEdit.disabled = !(turno && resp && desc);
    } else {
        const turma = document.getElementById('turmaSelect')?.value || '';
        const prof = document.getElementById('profSelect')?.value || '';
        btnEdit.disabled = !(turno && turma && prof);
    }
}

function toggleEditMode() {
    if (!window.currentUser) return openModal('loginModal');
    window.editMode = !window.editMode;
    const btn = document.getElementById('btnEditGrid');
    if (btn) {
        btn.innerText = window.editMode ? 'Finalizar Edição' : 'Editar Horários';
        btn.classList.toggle('active', window.editMode);
    }
    document.querySelectorAll('.slot').forEach(s => {
        if (!s.classList.contains('locked') || window.currentRole === 'admin' || window.currentRole === 'root') {
            s.classList.toggle('editable', window.editMode);
        }
    });
}

async function loadSchedule() {
    const semanaInput = document.getElementById('semanaSelect');
    if (!semanaInput) return;
    const semana = semanaInput.value;
    const turno = window.currentShift;
    if (!semana || !turno) return;
    updateHeaderDates(semana);
    setLoading(true);
    try {
        const res = await fetch(`/api/agendamentos?semana=${semana}&recurso=${window.currentResource}`);
        window.currentSchedule = await res.json();
    } catch (e) {
        showToast("Erro ao carregar agenda", "error");
    } finally {
        setLoading(false);
    }
    updateGridUI(window.currentSchedule.filter(a => a.turno === turno));
}

function updateGridUI(agendamentos) {
    const semana = document.getElementById('semanaSelect')?.value || '';
    const turno = window.currentShift;
    document.querySelectorAll('.slot').forEach(s => {
        const [, dia, p] = s.id.split('-');
        const horaStart = HORARIOS_PERIODOS[turno][p];
        const isDisabled = checkIsPast(semana, DIAS.indexOf(dia), horaStart);
        s.innerHTML = isDisabled ? '' : '<span class="placeholder">+</span>';
        s.className = 'slot' + (isDisabled ? ' disabled' : '');
    });
    agendamentos.forEach(a => {
        const slot = document.getElementById(`slot-${a.dia}-${a.periodo}`);
        if (!slot) return;
        const isNotStaff = window.currentRole !== 'admin' && window.currentRole !== 'root';
        const isOther = isNotStaff && a.criado_por !== window.currentUser;
        slot.className = `slot filled ${a.locked ? 'locked' : ''} ${isOther ? 'other-user' : ''} ${a.tipo === 'evento' ? 'evento' : ''}`;
        slot.innerHTML = `<div class="professor">${a.professor_id}</div><div class="turma">${a.turma_id}</div>`;
        const actions = document.createElement('div');
        actions.className = 'actions';
        if (window.currentRole === 'admin' || window.currentRole === 'root' || (a.criado_por === window.currentUser && !a.locked)) {
            const del = document.createElement('button');
            del.className = 'btn-small'; del.textContent = '✕';
            del.onclick = (e) => deleteSlot(e, a.id, a.dia, a.periodo, a.turma_id, a.turno);
            actions.appendChild(del);
        }
        if (window.currentRole === 'admin' || window.currentRole === 'root') {
            const lock = document.createElement('button');
            lock.className = 'btn-small'; lock.textContent = a.locked ? '🔓' : '🔒';
            lock.onclick = (e) => toggleLock(e, a.id, a.dia, a.periodo, !a.locked, a.turma_id, a.turno);
            actions.appendChild(lock);
        }
        slot.appendChild(actions);
        if (a.locked) {
            const icon = document.createElement('div'); icon.className = 'lock-indicator'; icon.textContent = '🔒';
            slot.appendChild(icon);
        }
    });
}

function onTipoAgendamentoChange() {
    const tipo = document.getElementById('tipoAgendamentoSelect')?.value || 'aula';
    const labelProf = document.querySelector('#group-professor label');
    const labelTurma = document.querySelector('#group-turma label');
    const profS = document.getElementById('profSelect');
    const respI = document.getElementById('eventoRespInput');
    const turmaS = document.getElementById('turmaSelect');
    const descI = document.getElementById('eventoDescInput');
    if (tipo === 'evento') {
        if (labelProf) labelProf.textContent = 'Responsável';
        if (labelTurma) labelTurma.textContent = 'Descrição do Evento';
        if (profS) profS.style.display = 'none';
        if (respI) respI.style.display = 'block';
        if (turmaS) turmaS.style.display = 'none';
        if (descI) descI.style.display = 'block';
    } else {
        if (labelProf) labelProf.textContent = 'Professor';
        if (labelTurma) labelTurma.textContent = 'Turma';
        if (profS) profS.style.display = 'block';
        if (respI) respI.style.display = 'none';
        if (turmaS) turmaS.style.display = 'block';
        if (descI) descI.style.display = 'none';
    }
    enableGrid();
}

async function onSlotClick(dia, periodo) {
    if (!window.currentUser) return openModal('loginModal');
    if (!window.editMode) return;
    const tipo = document.getElementById('tipoAgendamentoSelect')?.value || 'aula';
    const turno = window.currentShift;
    const semana = document.getElementById('semanaSelect')?.value || '';
    let turma, prof;
    if (tipo === 'evento') {
        turma = document.getElementById('eventoDescInput')?.value || '';
        prof = document.getElementById('eventoRespInput')?.value || '';
    } else {
        turma = document.getElementById('turmaSelect')?.value || '';
        prof = document.getElementById('profSelect')?.value || '';
    }
    if (!turma || !prof) return showToast("Selecione os dados na barra superior", "warning");
    const res = await fetch('/api/agendamentos', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ semana_inicio: semana, periodo, dia, turno, turma_id: turma, professor_id: prof, recurso_id: window.currentResource, tipo, frequencia: document.getElementById('freqSelect').value })
    });
    if ((await res.json()).success) loadSchedule();
    else showToast("Erro ao agendar", "error");
}

async function deleteSlot(e, id, dia, periodo, turmaId, turnoId) {
    e.stopPropagation();
    const res = await fetch('/api/agendamentos/delete', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ id, semana_inicio: document.getElementById('semanaSelect').value, periodo, dia, turno: turnoId, turma_id: turmaId, recurso_id: window.currentResource })
    });
    if ((await res.json()).success) loadSchedule();
}

async function toggleLock(e, id, dia, periodo, lockState, turmaId, turnoId) {
    e.stopPropagation();
    const res = await fetch('/api/agendamentos/lock', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ id, semana_inicio: document.getElementById('semanaSelect').value, periodo, dia, turno: turnoId, turma_id: turmaId, recurso_id: window.currentResource, locked: lockState })
    });
    if (res.ok) loadSchedule();
}

function openModal(id) {
    console.log("Debug: Opening modal", id);
    if (id === 'settingsModal') {
        loadAppVersion();
    }
    // Carregar configurações do GitHub ao abrir os modais
    if (id === 'githubBackupModal' || id === 'githubProjectModal') {
        fetch('/api/config/github')
            .then(r => r.json())
            .then(data => {
                if (id === 'githubBackupModal') {
                    if (data.repo) document.getElementById('ghRepoUrl').value = data.repo;
                    if (data.user) document.getElementById('ghUser').value = data.user;
                    updateGithubTokenLink('backup');
                } else {
                    if (data.repo_proj) {
                        document.getElementById('ghRepoUrlProj').value = data.repo_proj;
                        // Mostra o botão se já estiver configurado
                        const btnSync = document.getElementById('btnSyncProject');
                        if (btnSync) btnSync.style.display = 'block';
                    }
                    updateGithubTokenLink('project');
                }
            })
            .catch(err => console.error("Erro ao carregar config GitHub:", err));
    }
    const m = document.getElementById(id);
    if (m) {
        m.style.display = 'flex';
        console.log("Debug: Modal display set to flex");
    } else {
        console.error("Debug: Modal not found", id);
    }
}

function closeModal(id) {
    const m = document.getElementById(id); if (m) m.style.display = 'none';
}

function openProjectGithubModal() {
    openModal('githubProjectModal');
}

async function uploadFiles(type) {
    let inputId, modalId;
    if (type === 'professores') { inputId = 'fileProf'; modalId = 'uploadProfModal'; }
    else if (type === 'turmas') { inputId = 'fileTurma'; modalId = 'uploadTurmaModal'; }
    else if (type === 'recursos') { inputId = 'fileRecurso'; modalId = 'uploadRecursoModal'; }

    const input = document.getElementById(inputId);
    if (!input || !input.files.length) return;

    const fd = new FormData();
    fd.append('file', input.files[0]);

    const loadingToast = showToast('Processando arquivo...', 'info');

    try {
        const res = await fetch(`/api/${type}/upload`, {
            method: 'POST',
            body: fd
        });
        const result = await res.json();

        if (result.success) {
            showToast(result.message, 'success');
            closeModal(modalId);

            // Recarregar a lista específica
            if (type === 'professores') loadSettingsProfessors();
            else if (type === 'turmas') loadSettingsTurmas();
            else if (type === 'recursos') openSettingsModal(); // Recarrega tudo pois recursos afetam menus
        } else {
            showToast(result.message, 'error');
        }
    } catch (e) {
        showToast('Erro no upload: ' + e, 'error');
    }
}

async function exportUsers() {
    if (!confirm("Deseja baixar o arquivo Excel com as credenciais de acesso de todos os professores?")) return;
    window.location.href = '/api/admin/export-users';
}

async function resetSystem() {
    const confirm1 = confirm("⚠️ ATENÇÃO: Isso irá apagar TODOS os agendamentos, professores e turmas!\n\nDeseja continuar?");
    if (!confirm1) return;

    const confirm2 = confirm("ESTA AÇÃO NÃO PODE SER DESFEITA.\nTem certeza absoluta?");
    if (!confirm2) return;

    try {
        const res = await fetch('/api/admin/system-reset', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ confirm: true })
        });
        const result = await res.json();
        if (result.success) {
            alert("Sistema resetado com sucesso!");
            location.reload();
        } else {
            alert("Erro: " + result.error);
        }
    } catch (e) {
        alert("Erro na conexão com o servidor.");
    }
}

async function loadConfig() {
    const res = await fetch('/api/config');
    const config = await res.json();
    ['schoolName', 'modalSchoolName'].forEach(id => {
        const el = document.getElementById(id); if (el) el.innerText = config.nome_escola;
    });
    const cl = document.getElementById('coordinatorName'); if (cl) cl.innerText = config.coordenador_pedagogico || "Definir Coordenador";
    if (config.logo_url) {
        ['schoolLogo', 'modalSchoolLogo'].forEach(id => {
            const img = document.getElementById(id); if (img) { img.src = config.logo_url; img.style.display = 'block'; }
        });
        const ph = document.getElementById('logoPlaceholder'); if (ph) ph.style.display = 'none';
    }
}

function setupBrandListeners() {
    const nl = document.getElementById('schoolName');
    if (nl) nl.onblur = async () => {
        await fetch('/api/config', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ nome_escola: nl.innerText.trim() }) });
    };
    const cl = document.getElementById('coordinatorName');
    if (cl) cl.onblur = async () => {
        await fetch('/api/config', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ coordenador_pedagogico: cl.innerText.trim() }) });
    };
}

// Exposto globalmente para debug.js
window.showToast = function (m, t = 'success') {
    const c = document.getElementById('toastContainer'); if (!c) return;
    const toast = document.createElement('div'); toast.className = `toast ${t}`; toast.textContent = m;
    c.appendChild(toast); setTimeout(() => toast.remove(), 4000);
}

function setLoading(v) {
    const g = document.querySelector('.schedule-container'); if (!g) return;
    let o = g.querySelector('.loading-overlay');
    if (v && !o) {
        o = document.createElement('div'); o.className = 'loading-overlay';
        o.innerHTML = '<div class="spinner"></div>'; g.appendChild(o);
    } else if (!v && o) o.remove();
}

function updateShift(turno) {
    window.currentShift = turno;
    onTurnoChange();
    document.querySelectorAll('.floating-shift-selector button').forEach(btn => {
        btn.classList.toggle('active', btn.innerText.toUpperCase() === turno.toUpperCase() || btn.getAttribute('title') === turno);
    });
}

function changeWeek(offset) {
    const input = document.getElementById('semanaSelect');
    if (!input) return;
    const current = new Date(input.value + 'T12:00:00');
    current.setDate(current.getDate() + (offset * 7));
    input.value = current.toISOString().split('T')[0];
    loadSchedule();
}

function getMonday(d) {
    const date = new Date(d); date.setHours(12, 0, 0, 0);
    const day = date.getDay();
    const diff = date.getDate() - day + (day === 0 ? -6 : 1);
    return new Date(date.setDate(diff));
}

function updateHeaderDates(s) {
    if (!s) return;
    const start = new Date(s + 'T12:00:00');
    const hs = document.querySelectorAll('#scheduleGrid thead th');
    DIAS.forEach((d, i) => {
        const curr = new Date(start); curr.setDate(start.getDate() + i);
        if (hs[i + 1]) hs[i + 1].innerHTML = `${d}<br><small style="color: var(--accent-color);">${curr.toLocaleDateString('pt-BR', { day: '2-digit', month: '2-digit' })}</small>`;
    });
}

// --- Lógica do Modal de Configurações ---

async function openSettingsModal() {
    console.log("Debug: openSettingsModal called");
    try {
        // 1. Carregar Configurações Gerais
        const resConfig = await fetch('/api/config');
        const config = await resConfig.json();

        // Nome da Escola e Logo URL
        const settingsSchoolName = document.getElementById('settingsSchoolName');
        if (settingsSchoolName) settingsSchoolName.value = config.nome_escola || '';
        const settingsLogoUrl = document.getElementById('settingsLogoUrl');
        if (settingsLogoUrl) settingsLogoUrl.value = config.logo_url || '';

        // Debug Mode
        const elDebug = document.getElementById('settingsDebugToggle');
        if (elDebug) elDebug.checked = config.debug_mode !== false;

        // Backup Time
        const backupTime = document.getElementById('backupTime');
        if (backupTime) backupTime.value = config.backup_time || '00:00';

        // Backup Status
        const lastBackupEl = document.getElementById('lastBackupStatus');
        if (lastBackupEl) {
            if (config.last_backup_at) {
                lastBackupEl.innerHTML = `Último Backup: <b>${config.last_backup_at}</b><br><span style="font-size:0.7rem">${config.last_backup_status || ''}</span>`;
                lastBackupEl.style.color = (config.last_backup_status && config.last_backup_status.includes('Sucesso')) ? '#10b981' : '#ef4444';
            } else {
                lastBackupEl.innerText = "Último Backup: Nenhum registro";
            }
        }

        // 2. Carregar Lista de Recursos para Gerenciamento
        const resRec = await fetch('/api/recursos');
        const recursos = await resRec.json();
        const listContainer = document.getElementById('settingsResourcesList');

        if (listContainer) {
            listContainer.innerHTML = '';
            recursos.forEach(r => {
                const item = document.createElement('div');
                item.className = 'settings-section'; // Reuse styling for spacing
                item.style.padding = '10px 0';
                item.style.marginBottom = '10px';

                item.innerHTML = `
                    <label class="toggle-switch">
                        <div class="toggle-label">
                            <span>${r.nome}</span>
                            <small>${r.tipo.toUpperCase()}</small>
                        </div>
                        <input type="checkbox" class="resource-toggle" data-id="${r.id}" data-nome="${r.nome}" data-tipo="${r.tipo}" ${r.active !== false ? 'checked' : ''}>
                    </label>
                `;
                listContainer.appendChild(item);
            });
        }

        // 3. Carregar Lista de Professores
        const resUsers = await fetch('/api/users');
        const users = await resUsers.json();
        const profListContainer = document.getElementById('settingsProfessorsList');

        if (profListContainer) {
            profListContainer.innerHTML = '';
            // Filtrar apenas professores e ordenar por nome
            const professors = users.filter(u => u.role === 'professor').sort((a, b) => a.nome.localeCompare(b.nome));

            professors.forEach(p => {
                const item = document.createElement('div');
                item.className = 'settings-section';
                item.style.padding = '10px 0';
                item.style.marginBottom = '10px';

                item.innerHTML = `
                    <label class="toggle-switch">
                        <div class="toggle-label">
                            <span>${p.nome}</span>
                            <small>${p.username}</small>
                        </div>
                        <input type="checkbox" class="professor-toggle" data-username="${p.username}" ${p.active !== false ? 'checked' : ''}>
                    </label>
                `;
                profListContainer.appendChild(item);
            });
        }

        // 4. Carregar Lista de Turmas
        const resTurmas = await fetch('/api/turmas'); // Traz todas
        const turmas = await resTurmas.json();
        const turmasListContainer = document.getElementById('settingsTurmasList');

        if (turmasListContainer) {
            turmasListContainer.innerHTML = '';
            // Ordenar por nome
            const sortedTurmas = turmas.sort((a, b) => a.turma.localeCompare(b.turma));

            sortedTurmas.forEach(t => {
                const item = document.createElement('div');
                item.className = 'settings-section';
                item.style.padding = '10px 0';
                item.style.marginBottom = '10px';

                item.innerHTML = `
                    <label class="toggle-switch">
                        <div class="toggle-label">
                            <span>${t.turma}</span>
                            <small>${t.turno}</small>
                        </div>
                        <input type="checkbox" class="turma-toggle" data-turma="${t.turma}" data-turno="${t.turno}" ${t.active !== false ? 'checked' : ''}>
                    </label>
                `;
                turmasListContainer.appendChild(item);
            });
        }

        openModal('settingsModal');
    } catch (e) {
        console.error("Erro ao abrir configurações:", e);
        alert("Erro ao carregar configurações.");
    }
}


async function saveSettings() {
    const debugToggle = document.getElementById('settingsDebugToggle');
    const debugMode = debugToggle ? debugToggle.checked : null;

    // Se o elemento não existe (usuário não root), não envia o campo para não sobrescrever
    const payload = {
        backup_time: document.getElementById('backupTime').value
    };

    if (debugMode !== null) {
        payload.debug_mode = debugMode;
    }

    console.log("Saving Settings:", payload);

    try {
        // 1. Salvar Configurações Gerais
        const res = await fetch('/api/config', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        if (!res.ok) {
            const err = await res.json();
            throw new Error(err.message || "Falha ao salvar configurações gerais");
        }

        // 2. Salvar Status dos Recursos
        const resourceToggles = document.querySelectorAll('.resource-toggle');
        const updatedResources = Array.from(resourceToggles).map(toggle => ({
            id: toggle.dataset.id,
            nome: toggle.dataset.nome,
            tipo: toggle.dataset.tipo,
            active: toggle.checked
        }));

        const resRec = await fetch('/api/recursos/update', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(updatedResources)
        });

        if (!resRec.ok) throw new Error("Falha ao salvar status dos recursos");

        // 3. Salvar Status dos Professores
        const professorToggles = document.querySelectorAll('.professor-toggle');
        const updatedUsers = Array.from(professorToggles).map(toggle => ({
            username: toggle.dataset.username,
            active: toggle.checked
        }));

        const resUsers = await fetch('/api/users/update_status', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(updatedUsers)
        });

        if (!resUsers.ok) throw new Error("Falha ao salvar status dos professores");

        // 4. Salvar Status das Turmas
        const turmaToggles = document.querySelectorAll('.turma-toggle');
        const updatedTurmas = Array.from(turmaToggles).map(toggle => ({
            turma: toggle.dataset.turma,
            turno: toggle.dataset.turno,
            active: toggle.checked
        }));

        const resTurmas = await fetch('/api/turmas/update_status', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(updatedTurmas)
        });

        if (!resTurmas.ok) throw new Error("Falha ao salvar status das turmas");

        // 5. Atualizar UI
        await loadConfig();
        await loadResources(); // Recarrega a barra lateral flutuante
        if (typeof loadProfessores === 'function') await loadProfessores(); // Recarrega dropdown de professores
        showToast("Configurações salvas com sucesso!", "success");
        closeModal('settingsModal');

    } catch (e) {
        console.error(e);
        showToast("Erro ao salvar configurações", "error");
    }
}

// Override no loadConfig original para aplicar Debug Mode
const originalLoadConfig = loadConfig;
loadConfig = async function () {
    // Chama a original para carregar textos e logos
    // Nota: Como a original faz fetch interno, vamos fazer um fetch aqui também para pegar o flag
    // O ideal seria refatorar, mas para não quebrar a original mantemos assim.

    const res = await fetch('/api/config');
    const config = await res.json();
    window.debugModeAllowed = (config.debug_mode !== false);
    if (window.DebugResolution && typeof window.DebugResolution.update === 'function') {
        window.DebugResolution.update();
    }

    // Aplicar textos e logos (lógica antiga duplicada ou reaproveitada se possível, mas aqui garantimos o update)
    ['schoolName', 'modalSchoolName'].forEach(id => {
        const el = document.getElementById(id); if (el) el.innerText = config.nome_escola;
    });
    const cl = document.getElementById('coordinatorName'); if (cl) cl.innerText = config.coordenador_pedagogico || "Definir Coordenador";
    if (config.logo_url) {
        ['schoolLogo', 'modalSchoolLogo'].forEach(id => {
            const img = document.getElementById(id); if (img) { img.src = config.logo_url; img.style.display = 'block'; }
        });
        const ph = document.getElementById('logoPlaceholder'); if (ph) ph.style.display = 'none';
    }

    // Lógica do Debug Badge
    const badge = document.getElementById('debugResolution');
    const dCheck = document.getElementById('settingsDebugToggle');
    if (dCheck) dCheck.checked = (config.debug_mode === true);

    const bTime = document.getElementById('backupTime');
    if (bTime && config.backup_time) bTime.value = config.backup_time;

    if (badge) {
        if (config.debug_mode === false) {
            badge.style.display = 'none';
        } else if (window.currentRole === 'admin' || window.currentRole === 'root') {
            badge.style.display = 'block'; // Só mostra se for admin E estiver ativado
        } else {
            badge.style.display = 'none';
        }
    }
}

// Ajuste na abertura do modal pelo botão
document.addEventListener('DOMContentLoaded', () => {
    // ... listeners existentes ...
    const btnParams = document.getElementById('btnSettings');
    if (btnParams) btnParams.onclick = () => openSettingsModal();
});

// Sistema de Backup
function backupSystem() {
    window.location.href = '/api/backup';
    showToast('Iniciando download do backup...', 'info');
}

async function handleRestore(event) {
    const file = event.target.files[0];
    if (!file) return;

    if (!confirm('ATENÇÃO: Isso irá substituir TODOS os dados atuais pelos do backup. Deseja continuar?')) {
        event.target.value = ''; // Limpar input
        return;
    }

    const formData = new FormData();
    formData.append('file', file);

    const loadingToast = showToast('Restaurando sistema...', 'info');

    try {
        const response = await fetch('/api/restore', {
            method: 'POST',
            body: formData
        });

        const result = await response.json();

        if (result.success) {
            let msg = '✅ Sistema Restaurado com Sucesso!\n\n';
            if (result.stats) {
                msg += `📅 Data do Backup: ${result.stats.backup_date}\n`;
                msg += `⚠️ Atenção: Dados criados após esta data foram perdidos.\n\n`;
                msg += `📊 Resumo Restaurado:\n`;
                msg += `- Agendamentos: ${result.stats.agendamentos || 0}\n`;
                msg += `- Professores: ${result.stats.professores || 0}\n`;
                msg += `- Turmas: ${result.stats.turmas || 0}\n`;
            }
            alert(msg);
            window.location.reload();
        } else {
            showToast(result.message || 'Erro ao restaurar.', 'error');
        }
    } catch (error) {
        console.error('Erro na restauração:', error);
        showToast('Erro interno ao restaurar backup.', 'error');
    }

    event.target.value = ''; // Limpar input
}

// --- GitHub / Nuvem Config ---

function openGithubModal(type) {
    const modalId = type === 'project' ? 'githubProjectModal' : 'githubBackupModal';
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.style.display = 'block';
        fetch('/api/config/github')
            .then(r => r.json())
            .then(data => {
                if (type === 'backup') {
                    if (data.repo) document.getElementById('ghRepoUrl').value = data.repo;
                    if (data.user) document.getElementById('ghUser').value = data.user;
                } else if (type === 'project') {
                    if (data.repo_proj) document.getElementById('ghRepoUrlProj').value = data.repo_proj;
                }
            })
            .catch(err => console.log("Erro ao buscar configurações: ", err));
    }
}


async function testGithubConnection(type) {
    const isProj = type === 'project';
    const btnId = isProj ? 'btnTestProj' : 'btnTestBackup';
    const btn = document.getElementById(btnId);

    const data = { action: 'test' };
    if (isProj) {
        data.repo_proj = document.getElementById('ghRepoUrlProj').value;
        data.token_proj = document.getElementById('ghTokenProj').value;
    } else {
        data.repo = document.getElementById('ghRepoUrl').value;
        data.user = document.getElementById('ghUser').value;
        data.token = document.getElementById('ghToken').value;
    }

    if (btn) {
        btn.disabled = true;
        btn.innerText = "Testando...";
    }

    try {
        const res = await fetch('/api/config/github', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        const respData = await res.json();
        alert(respData.message);
    } catch (e) {
        alert('Erro ao testar: ' + e);
    } finally {
        if (btn) {
            btn.disabled = false;
            btn.innerText = isProj ? "Testar Dev" : "Testar";
        }
    }
}

async function restoreFromGithub() {
    if (!confirm("Tem certeza que deseja restaurar o backup da nuvem? Isso substituirá os dados atuais.")) return;

    showToast('Baixando backup da nuvem... Isso pode demorar.', 'info');

    try {
        const res = await fetch('/api/restore/github', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({}) // Backend deve usar credenciais salvas
        });
        const result = await res.json();

        if (res.ok && result.success) {
            alert(`✅ Restauração da Nuvem Concluída!\n\nBackup usado: ${result.backup_file}\nData: ${result.stats?.backup_date || 'N/A'}`);
            window.location.reload();
        } else {
            console.error("Erro restore:", result);
            alert('❌ Erro na Restauração: ' + (result.message || "Falha desconhecida"));
        }
    } catch (e) {
        alert('Erro crítico: ' + e);
    }
}
// Função para alternar abas no Modal de Configurações
function openSettingsTab(tabName) {
    // 1. Remove classe 'active' de todos os botões e conteúdos
    document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
    document.querySelectorAll('.tab-content').forEach(content => content.classList.remove('active'));

    // 2. Adiciona 'active' no botão clicado e no conteúdo correspondente
    const selectedBtn = document.querySelector(`.tab-btn[onclick="openSettingsTab('${tabName}')"]`);
    const selectedContent = document.getElementById(`tab-${tabName}`);

    if (selectedBtn) selectedBtn.classList.add('active');
    if (selectedContent) selectedContent.classList.add('active');
}

async function openManagePasswordsModal() {
    openModal('managePasswordsModal');
    const tbody = document.getElementById('userPasswordsList');
    if (!tbody) return;

    tbody.innerHTML = '<tr><td colspan="4" style="text-align: center; padding: 20px;">Carregando usuários...</td></tr>';

    try {
        const res = await fetch('/api/admin/users');
        const users = await res.json();

        tbody.innerHTML = '';
        if (users.length === 0) {
            tbody.innerHTML = '<tr><td colspan="4" style="text-align: center; padding: 20px;">Nenhum usuário encontrado.</td></tr>';
            return;
        }

        // Ordenar por nome
        users.sort((a, b) => a.nome.localeCompare(b.nome));

        users.forEach(u => {
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td>${u.nome}</td>
                <td style="color: #94a3b8; font-family: monospace;">${u.username}</td>
                <td><span class="badge ${u.role}">${u.role.toUpperCase()}</span></td>
                <td style="text-align: right;">
                    <button class="btn-small danger" onclick="resetUserPassword('${u.username}')" style="background: rgba(239, 68, 68, 0.1); color: #ef4444; border: 1px solid rgba(239, 68, 68, 0.2); padding: 4px 8px; border-radius: 4px; cursor: pointer;">
                        Resetar Senha
                    </button>
                </td>
            `;
            tbody.appendChild(tr);
        });
    } catch (e) {
        tbody.innerHTML = '<tr><td colspan="4" style="text-align: center; color: #ef4444; padding: 20px;">Erro ao carregar usuários.</td></tr>';
    }
}

async function resetUserPassword(username) {
    if (!confirm(`Deseja realmente resetar a senha do usuário "${username}" para o padrão (@Senha123456)?`)) return;

    try {
        const res = await fetch('/api/admin/reset-password', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username })
        });
        const result = await res.json();

        if (result.success) {
            showToast(result.message, 'success');
        } else {
            showToast(result.message, 'error');
        }
    } catch (e) {
        showToast('Erro ao resetar senha: ' + e, 'error');
    }
}
async function loadAppVersion() {
    try {
        const res = await fetch('/api/version');
        const data = await res.json();
        const label = document.getElementById('vLocalLabel');
        if (label) label.innerText = `v${data.version}`;
    } catch (e) {
        console.error("Erro ao carregar versão:", e);
    }
}

async function syncPush() {
    if (!confirm("Isso irá incrementar o número da versão e enviar seu código ATUAL para o GitHub (excluindo a pasta de dados). Deseja prosseguir?")) return;

    const btn = event.currentTarget;
    const mac = btn.innerHTML;
    btn.disabled = true;
    btn.innerHTML = '<span class="loading-spinner"></span> Enviando...';

    try {
        const res = await fetch('/api/update/sync', { method: 'POST' });
        const data = await res.json();
        if (data.success) {
            showToast(data.message, 'success');
            loadAppVersion();
        } else {
            showToast(data.message, 'error');
        }
    } catch (e) {
        showToast('Erro crítico no push: ' + e, 'error');
    } finally {
        btn.disabled = false;
        btn.innerHTML = mac;
    }
}

async function checkUpdates() {
    const btn = event.currentTarget;
    const mac = btn.innerText;
    btn.disabled = true;
    btn.innerText = 'Verificando...';

    try {
        const res = await fetch('/api/update/check');
        const data = await res.json();

        const btnInstall = document.getElementById('btnInstallUpdate');

        if (data.success) {
            if (data.has_update) {
                showToast(`Nova versão disponível: v${data.remote_version}`, 'info');
                if (btnInstall) {
                    btnInstall.disabled = false;
                    btnInstall.innerText = `Instalar v${data.remote_version}`;
                    btnInstall.style.opacity = '1';
                    btnInstall.style.cursor = 'pointer';
                }
            } else {
                showToast('Seu sistema já está na versão mais recente.', 'success');
                if (btnInstall) {
                    btnInstall.disabled = true;
                    btnInstall.innerText = 'v' + data.local_version + ' (Atualizada)';
                    btnInstall.style.opacity = '0.5';
                    btnInstall.style.cursor = 'not-allowed';
                }
            }
        } else {
            showToast(data.message, 'error');
        }
    } catch (e) {
        showToast('Erro ao verificar atualizações: ' + e, 'error');
    } finally {
        btn.disabled = false;
        btn.innerText = mac;
    }
}

async function installUpdate() {
    if (!confirm("ATENÇÃO: A instalação irá substituir os arquivos do sistema e reiniciar o servidor. Seus dados na pasta 'data' serão preservados. Deseja iniciar?")) return;

    const btn = document.getElementById('btnInstallUpdate');
    const container = document.getElementById('updateProgressContainer');
    const bar = document.getElementById('updateProgressBar');

    if (btn) btn.disabled = true;
    if (container) container.style.display = 'block';

    let progress = 0;
    const interval = setInterval(() => {
        progress += 5;
        if (bar) bar.style.width = progress + '%';
        if (progress >= 95) clearInterval(interval);
    }, 200);

    try {
        const res = await fetch('/api/update/install', { method: 'POST' });
        const data = await res.json();

        if (data.success) {
            if (bar) bar.style.width = '100%';
            showToast('Arquivos baixados! Reiniciando servidor...', 'success');
            setTimeout(() => {
                window.location.reload();
            }, 3000);
        } else {
            showToast(data.message, 'error');
            if (container) container.style.display = 'none';
            if (btn) btn.disabled = false;
        }
    } catch (e) {
        showToast('Erro na instalação: ' + e, 'error');
        if (container) container.style.display = 'none';
        if (btn) btn.disabled = false;
    }
}

// Função para atualizar o link de geração de token dinamicamente
function updateGithubTokenLink(type) {
    const isProj = type === 'project';
    const repoInputId = isProj ? 'ghRepoUrlProj' : 'ghRepoUrl';
    const linkId = isProj ? 'ghTokenLinkProj' : 'ghTokenLinkBackup';

    const repoUrl = document.getElementById(repoInputId).value.trim();
    const linkElem = document.getElementById(linkId);

    if (!linkElem) return;

    // Tenta extrair usuário e repo da URL (ex: https://github.com/usuario/repo.git)
    // Suporta formatos HTTPS e SSH simples
    const regex = /github\.com[\/:]([^\/]+)\/([^\/\.]+)/;
    const match = repoUrl.match(regex);

    let targetUrl = 'https://github.com/settings/tokens/new?scopes=repo';
    let description = isProj ? 'Agenda CI/CD Project' : 'Agenda Backup System';

    if (match && match.length >= 3) {
        const user = match[1];
        const repo = match[2];
        description += ` (${user}/${repo})`;

        // Atualiza texto para dar feedback visual
        linkElem.innerText = `Gerar Token para ${user}/${repo}`;
        linkElem.style.opacity = '1';
    } else {
        linkElem.innerText = isProj ? 'Obter Token Root' : 'Obter Token do GitHub';
    }

    // Adiciona a descrição à URL
    targetUrl += `&description=${encodeURIComponent(description)}`;

    linkElem.href = targetUrl;
}

// --- Funções de Debug e Atualização (GitHub) ---

async function checkUpdates() {
    const btn = event.target || document.querySelector('button[onclick="checkUpdates()"]');
    const originalText = btn ? btn.innerText : 'Verificar Check';
    if (btn) {
        btn.disabled = true;
        btn.innerText = "Verificando...";
    }

    try {
        const res = await fetch('/api/update/check');
        const data = await res.json();

        if (data.success) {
            if (data.has_update) {
                showToast(`Nova versão disponível: ${data.remote_version}`, 'info');
                const btnInstall = document.getElementById('btnInstallUpdate');
                if (btnInstall) {
                    btnInstall.innerText = `Instalar ${data.remote_version}`;
                    btnInstall.disabled = false;
                    btnInstall.style.opacity = '1';
                    btnInstall.style.cursor = 'pointer';
                }
            } else {
                showToast('O sistema já está atualizado.', 'success');
            }
        } else {
            showToast(data.message || 'Erro ao verificar atualizações.', 'error');
        }
    } catch (e) {
        showToast('Erro de conexão ao verificar updates.', 'error');
        console.error(e);
    } finally {
        if (btn) {
            btn.innerText = originalText;
            btn.disabled = false;
        }
    }
}

async function installUpdate() {
    if (!confirm('O servidor será reiniciado após a atualização. Continuar?')) return;

    const btn = document.getElementById('btnInstallUpdate');
    if (btn) {
        btn.disabled = true;
        btn.innerText = "Instalando...";
    }

    try {
        const res = await fetch('/api/update/install', { method: 'POST' });
        const data = await res.json();

        if (data.success) {
            showToast('Atualização instalada! Reiniciando...', 'success');
            setTimeout(() => location.reload(), 5000);
        } else {
            showToast(data.message || 'Falha na instalação.', 'error');
            if (btn) {
                btn.disabled = false;
                btn.innerText = "Tentar Novamente";
            }
        }
    } catch (e) {
        showToast('Erro na requisição de instalação.', 'error');
        if (btn) btn.disabled = false;
    }
}

async function syncProject() {
    if (!confirm('Isso enviará as alterações locais para o repositório remoto (Push). Continuar?')) return;

    const btn = document.getElementById('btnSyncProject');
    if (btn) {
        btn.disabled = true;
        btn.innerText = "Sincronizando...";
    }

    showToast('Sincronizando com GitHub... (Pode demorar)', 'info');

    try {
        const res = await fetch('/api/update/sync', { method: 'POST' });
        const data = await res.json();

        if (data.success) {
            showToast('Sincronização concluída com sucesso!', 'success');
            alert("Sucesso:\n" + data.message);
        } else {
            showToast(`Erro na sincronização.`, 'error');
            alert("Erro:\n" + data.message);
        }
    } catch (e) {
        showToast('Erro de conexão ao sincronizar.', 'error');
    } finally {
        if (btn) {
            btn.disabled = false;
            btn.innerText = "Sincronizar Agora";
        }
    }
}

function hideSyncButton() {
    const btn = document.getElementById('btnSyncProject');
    if (btn) btn.style.display = 'none';
}

async function saveGithubConfig(type) {
    const isProject = type === 'project';
    const payload = { action: 'save' };

    if (isProject) {
        payload.repo_proj = document.getElementById('ghRepoUrlProj')?.value;
        payload.token_proj = document.getElementById('ghTokenProj')?.value;
    } else {
        payload.repo = document.getElementById('ghRepoUrl')?.value;
        payload.user = document.getElementById('ghUser')?.value;
        payload.token = document.getElementById('ghToken')?.value;
    }

    try {
        const res = await fetch('/api/config/github', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        const data = await res.json();
        if (data.success) {
            showToast('Configurações salvas com sucesso!', 'success');
            if (isProject) {
                // Mostra o botão de sincronizar se o salvamento foi um sucesso
                const btnSync = document.getElementById('btnSyncProject');
                if (btnSync) btnSync.style.display = 'block';
            } else {
                closeModal('githubBackupModal');
            }
        } else {
            showToast(data.message || 'Erro ao salvar.', 'error');
        }
    } catch (e) {
        showToast('Erro ao salvar configuração.', 'error');
    }
}

async function testGithubConnection(type) {
    const isProject = type === 'project';
    const payload = { action: 'test' };

    if (isProject) {
        payload.repo_proj = document.getElementById('ghRepoUrlProj')?.value;
        payload.token_proj = document.getElementById('ghTokenProj')?.value;
    } else {
        payload.repo = document.getElementById('ghRepoUrl')?.value;
        payload.user = document.getElementById('ghUser')?.value;
        payload.token = document.getElementById('ghToken')?.value;
    }

    showToast('Testando conexão...', 'info');

    try {
        const res = await fetch('/api/config/github', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        const data = await res.json();
        if (data.success) {
            alert("Resultado do Teste:\n" + data.message);
        } else {
            alert("Falha no Teste:\n" + data.message);
        }
    } catch (e) {
        alert("Erro ao testar conexão.");
    }
}
