
const DashboardAdmin = {
    charts: {},
    pendingRenders: {},
    isLoading: false,

    async init() {
        console.log("[BI] Inicializando...");
        // Removido timeout rígido de 6s para evitar travamento em redes lentas
        const checkRole = setInterval(() => {
            if (window.currentRole === 'admin') {
                clearInterval(checkRole);
                this.setup();
            }
        }, 300);
    },

    slugify(text) {
        if (!text) return 'resource';
        return text.toString().toLowerCase()
            .normalize("NFD").replace(/[\u0300-\u036f]/g, "")
            .replace(/\s+/g, '-')
            .replace(/[^\w\-]+/g, '')
            .replace(/\-\-+/g, '-')
            .replace(/^-+/, '')
            .replace(/-+$/, '');
    },

    setup() {
        console.log("[BI] Setup administrativo ativo.");
        const btn = document.getElementById('btnOpenDashboard');
        if (btn) btn.style.display = 'block';

        const originalOpenModal = window.openModal;
        window.openModal = (id) => {
            if (id === 'dashboardModal') {
                console.log("[BI] Capturado abertura de modal.");
                this.loadData();
            }
            if (typeof originalOpenModal === 'function') originalOpenModal(id);
        };

        const tabsNav = document.getElementById('dashboardTabsNav');
        if (tabsNav) {
            tabsNav.onclick = (e) => {
                const btn = e.target.closest('.tab-btn');
                if (!btn) return;
                this.switchTab(btn.dataset.tab);
            };
        }
    },

    showEmptyState() {
        console.log("[BI] Sistema vazio detectado. Mostrando fallback.");
        const container = document.getElementById('tab-global');
        if (container) {
            container.innerHTML = `
                <div class="empty-dashboard-state" style="display: flex; flex-direction: column; align-items: center; justify-content: center; height: 50vh; text-align: center; color: #94a3b8;">
                    <div style="font-size: 5rem; margin-bottom: 25px; filter: drop-shadow(0 0 15px rgba(14, 165, 233, 0.2));">📊</div>
                    <h3 style="color: #fff; margin-bottom: 12px; font-size: 1.5rem;">Inteligência em Stand-by</h3>
                    <p style="max-width: 400px; line-height: 1.6; color: #64748b;">Nenhum agendamento foi processado ainda.<br>Os gráficos serão gerados automaticamente assim que o primeiro horário for travado na agenda.</p>
                </div>
            `;
        }
        // Limpar abas antigas
        const resContainer = document.getElementById('resourceTabsContainer');
        if (resContainer) resContainer.innerHTML = '';
        document.querySelectorAll('.tab-btn:not([data-tab="global"])').forEach(b => b.remove());
    },

    switchTab(tabId) {
        const slug = this.slugify(tabId);
        const targetId = (slug === 'global') ? 'tab-global' : `tab-${slug}`;

        document.querySelectorAll('.tab-btn').forEach(b => b.classList.toggle('active', b.dataset.tab === tabId));
        document.querySelectorAll('.tab-content').forEach(c => c.classList.toggle('active', c.id === targetId));

        if (tabId !== 'global' && this.pendingRenders[tabId]) {
            this.pendingRenders[tabId]();
            delete this.pendingRenders[tabId];
        }
        window.dispatchEvent(new Event('resize'));
    },

    async loadData() {
        if (this.isLoading) return;
        this.isLoading = true;

        const loader = document.getElementById('dashboardLoader');
        if (loader) {
            loader.style.display = 'flex';
            loader.style.opacity = '1';
            loader.innerHTML = `
                <div class="spinner" style="width: 50px; height: 50px; border: 4px solid rgba(56, 189, 248, 0.1); border-top: 4px solid #0ea5e9; border-radius: 50%; animation: spin 1s linear infinite;"></div>
                <span style="color: #94a3b8; margin-top: 15px; font-weight: 500;">Processando Inteligência...</span>
            `;
        }

        // Safety net: Timeout de 8 segundos para não travar a tela
        const safetyNet = setTimeout(() => {
            if (this.isLoading && loader) {
                console.warn("[BI] Timeout de carregamento atingido. Forçando encerramento.");
                this.isLoading = false;
                loader.style.display = 'none';
            }
        }, 8000);

        try {
            console.time("BI-Fetch");
            // Cache Busting: Força o navegador a buscar dados novos do servidor
            const uniqueRequest = Date.now() + Math.random().toString(36).substring(7);
            const res = await fetch('/api/admin/dashboard/stats?v=' + uniqueRequest);

            if (res.status === 403) {
                console.error("[BI] Acesso Negado pelo servidor. Sessão pode ter expirado.");
                alert("Sessão expirada. Por favor, faça login novamente.");
                window.location.reload();
                return;
            }

            const data = await res.json();
            console.timeEnd("BI-Fetch");

            if (data.error) throw new Error(data.error);

            const nav = document.getElementById('dashboardTabsNav');
            const container = document.getElementById('resourceTabsContainer');

            nav.querySelectorAll('.tab-btn:not([data-tab="global"]):not([data-tab="periodo"])').forEach(b => b.remove());
            container.innerHTML = '';
            this.pendingRenders = {};

            // Renderizar
            this.renderGlobal(data);

            if (data.recursos) {
                const pSelect = document.getElementById('periodoRecurso');
                if (pSelect) {
                    const currentVal = pSelect.value;
                    pSelect.innerHTML = '<option value="all">TODOS OS RECURSOS</option>';
                    Object.entries(data.recursos).forEach(([rid, rdata]) => {
                        this.createResourceTab(nav, container, rid, rdata);
                        pSelect.innerHTML += `<option value="${rid}">${rdata.nome.toUpperCase()}</option>`;
                    });
                    pSelect.value = currentVal || 'all';
                }
            }

            // Inicializar datas se necessário
            const pStart = document.getElementById('periodoStart');
            const pEnd = document.getElementById('periodoEnd');
            if (pStart && !pStart.value) {
                const now = new Date();
                const firstDay = new Date(now.getFullYear(), now.getMonth(), 1);
                pStart.value = firstDay.toISOString().split('T')[0];
                pEnd.value = now.toISOString().split('T')[0];
            }

            this.switchTab('global');
        } catch (e) {
            console.error("[BI] Erro Crítico:", e);
            if (loader) {
                loader.innerHTML = `<span style="color:#ef4444; padding:20px; text-align:center;">⚠️ Erro de Dados: ${e.message}</span>`;
            }
        } finally {
            clearTimeout(safetyNet);
            this.isLoading = false;
            if (loader) {
                setTimeout(() => {
                    loader.style.opacity = '0';
                    setTimeout(() => loader.style.display = 'none', 300);
                }, 200);
            }
        }
    },

    renderGlobal(data) {
        if (!data || !data.global) return;
        const { global } = data;

        let totalOcup = 0, totalCap = 0;
        let mat = 0, ves = 0, not = 0;
        Object.values(data.recursos || {}).forEach(r => {
            totalOcup += (r.uso?.Total || 0);
            totalCap += (r.uso?.Capacidade || 0);
            mat += (r.uso?.Matutino || 0);
            ves += (r.uso?.Vespertino || 0);
            not += (r.uso?.Noturno || 0);
        });

        // Se o sistema estiver sem agendamentos
        const tabGlobal = document.getElementById('tab-global');
        if (totalOcup === 0) {
            this.showEmptyState();
            return;
        } else {
            // Restaurar HTML base se estiver vindo do empty state
            if (tabGlobal && tabGlobal.querySelector('.empty-dashboard-state')) {
                // Em vez de recarregar a página, limpamos e forçamos o load original (idealmente o HTML estaria num template)
                // Para simplificar agora, se o usuário preencheu o sistema, ele reabre o modal.
                tabGlobal.innerHTML = `
                    <div class="dashboard-grid" style="display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 20px;">
                        <div class="dashboard-card" style="background:#1e293b; padding:25px; border-radius:12px; text-align: center;">
                            <h4 style="color:#94a3b8; font-size:0.8rem; text-transform:uppercase;">Ocupação Semanal</h4>
                            <div id="chartUsabilidadeRadial"></div>
                        </div>
                        <div class="dashboard-card" style="background:#1e293b; padding:25px; border-radius:12px; display:flex; flex-direction:column; align-items:center; justify-content:center;">
                            <h4 style="color:#94a3b8; font-size:0.8rem; text-transform:uppercase; text-align:center;">Líder Matutino</h4>
                            <h2 id="topTurmaMat" style="color:#38bdf8; margin:10px 0; font-size: 1.3rem; text-align:center;">---</h2>
                        </div>
                        <div class="dashboard-card" style="background:#1e293b; padding:25px; border-radius:12px; display:flex; flex-direction:column; align-items:center; justify-content:center;">
                            <h4 style="color:#94a3b8; font-size:0.8rem; text-transform:uppercase; text-align:center;">Líder Vespertino</h4>
                            <h2 id="topTurmaVesp" style="color:#fbbf24; margin:10px 0; font-size: 1.3rem; text-align:center;">---</h2>
                        </div>
                        <div class="dashboard-card" style="background:#1e293b; padding:25px; border-radius:12px; display:flex; flex-direction:column; align-items:center; justify-content:center;">
                            <h4 style="color:#94a3b8; font-size:0.8rem; text-transform:uppercase; text-align:center;">Líder Noturno</h4>
                            <h2 id="topTurmaNot" style="color:#f472b6; margin:10px 0; font-size: 1.3rem; text-align:center;">---</h2>
                        </div>
                        <div class="dashboard-card" style="background:#1e293b; padding:25px; border-radius:12px; display:flex; flex-direction:column; align-items:center; justify-content:center;">
                            <h4 style="color:#94a3b8; font-size:0.8rem; text-transform:uppercase; text-align:center;">Acessos Totais</h4>
                            <h2 id="totalAcessos" style="color:#10b981; margin:10px 0; font-size: 2.5rem; text-align:center;">---</h2>
                        </div>
                    </div>
                    <div class="dashboard-charts-area" style="display: grid; grid-template-columns: 1fr 1fr; gap: 25px; margin-top: 25px;">
                        <div class="dashboard-card" style="background:#1e293b; padding:25px; border-radius:12px; grid-column: span 2;">
                             <h4 style="color:#cbd5e1; border-left:4px solid #38bdf8; padding-left:10px;">Picos de Uso por Turno</h4>
                             <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 15px; margin-top:15px;">
                                <div><span style="color:#94a3b8; font-size:0.7rem; display:block; text-align:center;">Manhã</span><div id="chartHeatmapMat"></div></div>
                                <div><span style="color:#94a3b8; font-size:0.7rem; display:block; text-align:center;">Tarde</span><div id="chartHeatmapVesp"></div></div>
                                <div><span style="color:#94a3b8; font-size:0.7rem; display:block; text-align:center;">Noite</span><div id="chartHeatmapNot"></div></div>
                             </div>
                        </div>
                        <div class="dashboard-card" style="background:#1e293b; padding:25px; border-radius:12px;">
                            <h4 style="color:#cbd5e1; border-left:4px solid #a78bfa; padding-left:10px;">Engajamento de Professores</h4>
                            <div id="chartProfsRanking" style="min-height: 350px;"></div>
                        </div>
                        <div class="dashboard-card" style="background:#1e293b; padding:25px; border-radius:12px;">
                            <h4 style="color:#cbd5e1; border-left:4px solid #10b981; padding-left:10px;">Monitoramento de Acessos</h4>
                            <div id="chartLoginsRanking" style="min-height: 350px;"></div>
                        </div>
                        <div class="dashboard-card" style="background:#1e293b; padding:25px; border-radius:12px;">
                            <h4 style="color:#cbd5e1; border-left:4px solid #fbbf24; padding-left:10px;">Distribuição por Turno</h4>
                            <div id="chartTurnosDonut" style="min-height: 250px;"></div>
                        </div>
                        <div class="dashboard-card" style="background:#1e293b; padding:25px; border-radius:12px; grid-column: span 2;">
                            <h4 style="color:#cbd5e1; border-left:4px solid #f472b6; padding-left:10px;">Ranking Global de Turmas</h4>
                            <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 15px; margin-top:15px;">
                                <div><span style="color:#94a3b8; font-size:0.7rem; display:block; text-align:center;">Manhã</span><div id="chartTurmasRankingMat"></div></div>
                                <div><span style="color:#94a3b8; font-size:0.7rem; display:block; text-align:center;">Tarde</span><div id="chartTurmasRankingVesp"></div></div>
                                <div><span style="color:#94a3b8; font-size:0.7rem; display:block; text-align:center;">Noite</span><div id="chartTurmasRankingNot"></div></div>
                            </div>
                        </div>
                    </div>
                `;
            }
        }

        // Preencher Cards Segmentados
        const tp = global.rankings?.turmas_por_turno || {};
        const setTop = (id, list) => {
            const el = document.getElementById(id);
            if (el) el.innerText = (list && list.length) ? list[0][0].toUpperCase() : '---';
        };

        setTop('topTurmaMat', tp.Matutino);
        setTop('topTurmaVesp', tp.Vespertino);
        setTop('topTurmaNot', tp.Noturno);

        if (document.getElementById('totalAcessos')) {
            document.getElementById('totalAcessos').innerText = global.total_logins || 0;
        }

        const percent = totalCap > 0 ? Math.round((totalOcup / totalCap) * 100) : 0;
        this.createChart('chartUsabilidadeRadial', {
            chart: { type: 'radialBar', height: 250 },
            series: [percent],
            colors: ['#0ea5e9'],
            plotOptions: {
                radialBar: {
                    hollow: { size: '65%' },
                    dataLabels: {
                        name: { show: false },
                        value: { fontSize: '2rem', color: '#fff', offsetY: 10 }
                    }
                }
            }
        });

        this.renderHeatmap('chartHeatmapMat', global.heatmap.Matutino, true, 'Matutino');
        this.renderHeatmap('chartHeatmapVesp', global.heatmap.Vespertino, true, 'Vespertino');
        this.renderHeatmap('chartHeatmapNot', global.heatmap.Noturno, true, 'Noturno');

        // Rankings de Turmas por Turno
        this.renderRankings('chartTurmasRankingMat', tp.Matutino, '#f472b6');
        this.renderRankings('chartTurmasRankingVesp', tp.Vespertino, '#fbbf24');
        this.renderRankings('chartTurmasRankingNot', tp.Noturno, '#38bdf8');

        this.renderRankings('chartProfsRanking', global.rankings.professores, '#a78bfa');
        this.renderRankings('chartLoginsRanking', global.rankings.logins, '#34d399');

        this.createChart('chartTurnosDonut', {
            chart: { type: 'donut', height: 350 },
            series: [mat, ves, not],
            labels: ['Matutino', 'Vespertino', 'Noturno'],
            colors: ['#38bdf8', '#fbbf24', '#f472b6'],
            legend: { position: 'bottom', labels: { colors: '#94a3b8' } }
        });
    },

    createResourceTab(nav, container, rid, rdata) {
        const slug = this.slugify(rid);
        const btn = document.createElement('button');
        btn.className = 'tab-btn';
        btn.dataset.tab = rid;
        btn.innerText = rdata.nome;
        nav.appendChild(btn);

        const section = document.createElement('div');
        section.id = `tab-${slug}`;
        section.className = 'tab-content';
        section.innerHTML = `
            <div class="dashboard-grid" style="display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 20px;">
                <div class="dashboard-card" style="background:#1e293b; padding:25px; border-radius:12px; display:flex; flex-direction:column; align-items:center; justify-content:center; text-align: center;">
                    <h4 style="color:#94a3b8; font-size:0.8rem; text-transform:uppercase;">Ocupação Local</h4>
                    <div id="radial-${slug}" style="height: 200px;"></div>
                </div>
                <div class="dashboard-card" style="background:#1e293b; padding:25px; border-radius:12px; display:flex; flex-direction:column; align-items:center; justify-content:center; text-align: center;">
                    <h4 style="color:#94a3b8; font-size:0.8rem; text-transform:uppercase;">Destaque Local</h4>
                    <h2 style="color:#38bdf8; font-size:1.4rem; margin:15px 0;">${rdata.rankings?.professores?.[0]?.[0] || '---'}</h2>
                </div>
                <div class="dashboard-card" style="background:#1e293b; padding:25px; border-radius:12px; display:flex; flex-direction:column; align-items:center; justify-content:center; text-align: center;">
                    <h4 style="color:#94a3b8; font-size:0.8rem; text-transform:uppercase;">Aulas Reservadas</h4>
                    <h2 style="color:#fbbf24; font-size:2rem; margin:15px 0;">${rdata.uso?.Total || 0}</h2>
                </div>
            </div>
            <div class="dashboard-charts-area" style="display: grid; grid-template-columns: 1fr 1fr; gap: 25px; margin-top: 25px;">
                <div class="dashboard-card" style="background:#1e293b; padding:25px; border-radius:12px; grid-column: span 2;">
                    <h4 style="color:#cbd5e1; border-left:4px solid #38bdf8; padding-left:10px;">Calor por Turno: ${rdata.nome}</h4>
                    <div class="heatmap-container" style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 15px; margin-top:15px;">
                        <div><span style="color:#94a3b8; font-size:0.6rem; display:block; text-align:center;">Manhã</span><div id="heat-mat-${slug}"></div></div>
                        <div><span style="color:#94a3b8; font-size:0.6rem; display:block; text-align:center;">Tarde</span><div id="heat-vesp-${slug}"></div></div>
                        <div><span style="color:#94a3b8; font-size:0.6rem; display:block; text-align:center;">Noite</span><div id="heat-not-${slug}"></div></div>
                    </div>
                </div>
                <div class="dashboard-card" style="background:#1e293b; padding:25px; border-radius:12px; grid-column: span 2;">
                    <h4 style="color:#cbd5e1; border-left:4px solid #a78bfa; padding-left:10px;">Ranking Local (Engajamento de Professores)</h4>
                    <div id="ranking-${slug}" style="height: 350px;"></div>
                </div>
                <div class="dashboard-card" style="background:#1e293b; padding:25px; border-radius:12px; grid-column: span 2;">
                    <h4 style="color:#cbd5e1; border-left:4px solid #f472b6; padding-left:10px;">Ranking Local (Uso por Turma)</h4>
                    <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 15px; margin-top:15px;">
                        <div><span style="color:#94a3b8; font-size:0.6rem; display:block; text-align:center;">Manhã</span><div id="rank-tur-mat-${slug}"></div></div>
                        <div><span style="color:#94a3b8; font-size:0.6rem; display:block; text-align:center;">Tarde</span><div id="rank-tur-vesp-${slug}"></div></div>
                        <div><span style="color:#94a3b8; font-size:0.6rem; display:block; text-align:center;">Noite</span><div id="rank-tur-not-${slug}"></div></div>
                    </div>
                </div>
            </div>
        `;
        container.appendChild(section);

        this.pendingRenders[rid] = () => {
            const perc = (rdata.uso?.Capacidade > 0) ? Math.round((rdata.uso.Total / rdata.uso.Capacidade) * 100) : 0;
            this.createChart(`radial-${slug}`, {
                chart: { type: 'radialBar', height: 200 },
                series: [perc],
                colors: ['#0ea5e9'],
                plotOptions: {
                    radialBar: {
                        dataLabels: {
                            name: { show: false },
                            value: { fontSize: '1.2rem', color: '#fff', offsetY: 5 }
                        }
                    }
                }
            });

            this.renderHeatmap(`heat-mat-${slug}`, rdata.heatmap.Matutino, false, 'Matutino');
            this.renderHeatmap(`heat-vesp-${slug}`, rdata.heatmap.Vespertino, false, 'Vespertino');
            this.renderHeatmap(`heat-not-${slug}`, rdata.heatmap.Noturno, false, 'Noturno');

            this.renderRankings(`ranking-${slug}`, rdata.rankings?.professores, '#a78bfa');

            // Rankings Locais de Turmas
            this.renderRankings(`rank-tur-mat-${slug}`, rdata.rankings?.turmas?.Matutino, '#f472b6');
            this.renderRankings(`rank-tur-vesp-${slug}`, rdata.rankings?.turmas?.Vespertino, '#fbbf24');
            this.renderRankings(`rank-tur-not-${slug}`, rdata.rankings?.turmas?.Noturno, '#38bdf8');
        };
    },

    renderHeatmap(id, data, isGlobal, turno = 'Matutino') {
        const series = [];
        // Noite tem 4 aulas, Manhã/Tarde Têm 6
        const aulasCount = (turno === 'Noturno') ? 4 : 6;
        const aulas = [];
        for (let i = 1; i <= aulasCount; i++) aulas.push(`Aula ${i}`);
        if (turno !== 'Noturno') aulas.splice(3, 0, 'INT'); // Adicionar intervalo

        const dias = ['Segunda', 'Terça', 'Quarta', 'Quinta', 'Sexta'];

        aulas.reverse().forEach(per => {
            const row = { name: per, data: [] };
            dias.forEach(dia => {
                let val = 0;
                if (isGlobal) {
                    // data aqui é heatmap[turno] -> { recurso_id: { dia: { periodo: cont } } }
                    Object.values(data || {}).forEach(rHeat => { if (rHeat[dia]?.[per]) val += rHeat[dia][per]; });
                } else {
                    // data aqui é rdata.heatmap[turno] -> { dia: { periodo: cont } }
                    val = (data && data[dia]) ? (data[dia][per] || 0) : 0;
                }
                row.data.push({ x: dia, y: val });
            });
            series.push(row);
        });

        this.createChart(id, {
            chart: { type: 'heatmap', height: (turno === 'Noturno' ? 250 : 350), toolbar: { show: false } },
            series: series,
            dataLabels: {
                enabled: true,
                formatter: function (val) { return val === 0 ? '' : val; }, // Ocultar 0 para visual clean
                style: {
                    colors: ['#fff'],
                    fontFamily: 'Plus Jakarta Sans, sans-serif',
                    fontWeight: 600,
                    fontSize: '11px'
                }
            },
            stroke: {
                width: 3,
                colors: ['#0f172a'] // Espaçamento elegante entre "cards"
            },
            plotOptions: {
                heatmap: {
                    radius: 4, // Cantos arredondados modernos
                    shadeIntensity: 0.5,
                    colorScale: {
                        ranges: [
                            { from: 0, to: 0, color: '#1e293b', name: 'vazio' },
                            { from: 1, to: 9, color: '#fda4af', name: 'baixo' },     // Rose suave
                            { from: 10, to: 20, color: '#f43f5e', name: 'moderado' }, // Vibrant Rose
                            { from: 21, to: 1000, color: '#9f1239', name: 'intenso' }  // Bordô Imperial
                        ]
                    }
                }
            },
            xaxis: { position: 'bottom', labels: { style: { colors: '#94a3b8', fontFamily: 'Plus Jakarta Sans' } } },
            yaxis: { labels: { style: { colors: '#94a3b8', fontFamily: 'Plus Jakarta Sans' } } }
        });
    },

    renderRankings(id, list, color) {
        const series = (list && list.length) ? [{ name: 'Contagem', data: list.map(i => i[1]) }] : [{ name: 'Contagem', data: [] }];
        const cats = (list && list.length) ? list.map(i => i[0].toUpperCase()) : [];

        // Se a lista for vazia, o gráfico deve mostrar "Sem Dados" ou simplesmente ficar vazio em vez de não renderizar
        this.createChart(id, {
            chart: {
                type: 'bar',
                height: (list && list.length > 20) ? (list.length * 30) : 300,
                toolbar: { show: false }
            },
            noData: { text: 'Sem agendamentos no período', style: { color: '#94a3b8' } },
            series: series,
            colors: [color],
            plotOptions: { bar: { horizontal: true, borderRadius: 4, barHeight: '70%' } },
            xaxis: { categories: cats, labels: { style: { colors: '#94a3b8' } } },
            yaxis: { labels: { style: { colors: '#94a3b8' } } },
            dataLabels: { enabled: true, style: { colors: ['#fff'] } }
        });
    },

    async updatePeriodo() {
        const start = document.getElementById('periodoStart').value;
        const end = document.getElementById('periodoEnd').value;
        const recurso = document.getElementById('periodoRecurso').value;

        if (!start || !end) return alert("Selecione o intervalo de datas");

        const btn = document.querySelector('button[onclick="DashboardAdmin.updatePeriodo()"]');
        const originalText = btn.innerText;
        btn.disabled = true;
        btn.innerText = "Processando...";

        try {
            const res = await fetch(`/api/admin/dashboard/stats?start_date=${start}&end_date=${end}&recurso_id=${recurso}`);
            const data = await res.json();

            if (data.error) throw new Error(data.error);

            document.getElementById('periodoResults').style.display = 'block';

            // 1. Usabilidade Radial (Periodo)
            const globalUso = data.global.heatmap?.uso || { Total: 0, Capacidade: 1 };
            const perc = Math.round((globalUso.Total / (globalUso.Capacidade || 1)) * 100);
            this.createChart('chartPeriodoRadial', {
                chart: { type: 'radialBar', height: 200 },
                series: [perc],
                colors: ['#0ea5e9'],
                plotOptions: {
                    radialBar: {
                        dataLabels: {
                            name: { show: false },
                            value: { fontSize: '1.5rem', color: '#fff', offsetY: 5 }
                        }
                    }
                }
            });

            // 2. Donut Turnos (Periodo)
            const t = data.global.rankings.turmas_por_turno || {};
            const mat = (t.Matutino || []).reduce((a, b) => a + b[1], 0);
            const ves = (t.Vespertino || []).reduce((a, b) => a + b[1], 0);
            const not = (t.Noturno || []).reduce((a, b) => a + b[1], 0);

            this.createChart('chartPeriodoDonut', {
                chart: { type: 'donut', height: 200 },
                series: [mat, ves, not],
                labels: ['Manhã', 'Tarde', 'Noite'],
                colors: ['#38bdf8', '#fbbf24', '#f472b6'],
                legend: { show: false }
            });

            // 3. Rankings (Periodo)
            this.renderRankings('chartPeriodoProfs', data.global.rankings.professores, '#a78bfa');

            // Consolidar turmas
            const todasTurmas = {};
            ['Matutino', 'Vespertino', 'Noturno'].forEach(turno => {
                (data.global.rankings.turmas_por_turno[turno] || []).forEach(([turma, qtd]) => {
                    todasTurmas[turma] = (todasTurmas[turma] || 0) + qtd;
                });
            });
            const rankingTurmas = Object.entries(todasTurmas).sort((a, b) => b[1] - a[1]).slice(0, 10);
            this.renderRankings('chartPeriodoTurmas', rankingTurmas, '#f472b6');

            // 4. Heatmaps Custom (Periodo)
            this.renderHeatmap('heat-p-mat', data.global.heatmap.Matutino, true, 'Matutino');
            this.renderHeatmap('heat-p-vesp', data.global.heatmap.Vespertino, true, 'Vespertino');
            this.renderHeatmap('heat-p-not', data.global.heatmap.Noturno, true, 'Noturno');

            window.dispatchEvent(new Event('resize'));
        } catch (e) {
            console.error(e);
            alert("Erro ao filtrar período: " + e.message);
        } finally {
            btn.disabled = false;
            btn.innerText = originalText;
        }
    },

    async downloadPeriodo() {
        const start = document.getElementById('periodoStart').value;
        const end = document.getElementById('periodoEnd').value;
        const recurso = document.getElementById('periodoRecurso').value;
        if (!start || !end) return alert("Selecione o intervalo de datas");

        try {
            const res = await fetch(`/api/admin/dashboard/export?start_date=${start}&end_date=${end}&recurso_id=${recurso}`);
            if (!res.ok) throw new Error("Erro ao gerar planilha");

            const blob = await res.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `relatorio_bi_${start}_a_${end}.xlsx`;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);
        } catch (e) {
            alert("Erro ao baixar relatório: " + e.message);
        }
    },

    createChart(id, options) {
        const el = document.getElementById(id);
        if (!el) return null;
        if (this.charts[id]) { try { this.charts[id].destroy(); } catch (e) { } }
        try {
            const chart = new ApexCharts(el, {
                ...options,
                theme: { mode: 'dark' },
                chart: { ...options.chart, background: 'transparent' },
                fontFamily: 'Plus Jakarta Sans, sans-serif'
            });
            chart.render();
            this.charts[id] = chart;
            return chart;
        } catch (e) {
            console.error(`[BI] Erro no gráfico ${id}:`, e);
            return null;
        }
    }
};

document.addEventListener('DOMContentLoaded', () => DashboardAdmin.init());
