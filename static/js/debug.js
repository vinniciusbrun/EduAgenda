/**
 * Módulo de Debug - Monitoramento de Resolução e Otimização Laptop
 * Responsabilidade: Detectar resolução e oferecer otimização manual.
 */

const DebugResolution = {
    badge: null,
    isLaptopFixApplied: false,

    init() {
        this.badge = document.getElementById('debugResolution');
        if (!this.badge) return;

        window.addEventListener('resize', () => this.update());
        this.badge.ondblclick = () => this.hide();

        // Carrega estado anterior da otimização
        if (localStorage.getItem('laptopOptimized') === 'true') {
            this.applyLaptopFix(true);
        }

        this.update();
    },

    update() {
        this.badge = document.getElementById('debugResolution');
        if (!this.badge) return;

        const isAdmin = (window.currentRole === 'admin' || window.currentRole === 'root');
        const isHidden = sessionStorage.getItem('hideDebug') === 'true';

        const w = window.innerWidth;
        const h = window.innerHeight;
        let mode = 'DESKTOP';
        let shouldAutoOptimize = false;

        // Lógica de Detecção Automática (Laptops comuns)
        if (w <= 1280 && h <= 600) {
            mode = 'LAPTOP (Crítico 1280x585)';
            shouldAutoOptimize = true;
        } else if (w >= 1024 && w <= 1366) {
            mode = 'LAPTOP (HD Standard)';
            shouldAutoOptimize = true;
        } else if (w > 1366 && w <= 1536) {
            mode = 'LAPTOP (HD+ / FHD Scale)';
            shouldAutoOptimize = true;
        } else if (w > 1536 && w <= 1600) {
            mode = 'LAPTOP/SMALL MONITOR';
            shouldAutoOptimize = true;
        }

        // Automação: Aplica se detectado e não houver override manual de "desativação" nesta sessão
        const manualOverride = sessionStorage.getItem('laptopManualOverride') === 'off';
        if (shouldAutoOptimize && !this.isLaptopFixApplied && !manualOverride) {
            this.applyLaptopFix(true, false);
        }

        // Verificação de Configuração Global (definida em main.js ou padrão true)
        const configAllowed = (typeof window.debugModeAllowed !== 'undefined') ? window.debugModeAllowed : true;

        console.log(`[DebugResolution] Update: IsAdmin=${isAdmin}, Hide=${isHidden}, Allowed=${configAllowed}, Res=${w}x${h}`);

        if (isAdmin && !isHidden && configAllowed) {
            this.badge.style.display = 'block';
            try {
                this.badge.innerHTML = `<span>📏 RESOLUÇÃO:</span> ${w} x ${h} (${mode})`;

                const btn = document.createElement('button');
                if (this.isLaptopFixApplied) {
                    btn.innerText = "REVERTER LAYOUT";
                    btn.className = "btn-optimize-action revert";
                    btn.onclick = (e) => {
                        e.stopPropagation();
                        sessionStorage.setItem('laptopManualOverride', 'off');
                        this.applyLaptopFix(false, true);
                    };
                } else {
                    btn.innerText = "OTIMIZAR AGORA";
                    btn.className = "btn-optimize-action";
                    btn.onclick = (e) => {
                        e.stopPropagation();
                        sessionStorage.removeItem('laptopManualOverride');
                        this.applyLaptopFix(true, true);
                    };
                }
                this.badge.appendChild(btn);
            } catch (e) {
                console.error("[DebugResolution] Error updating innerHTML:", e);
                this.badge.innerText = "Erro Display";
            }
        } else {
            this.badge.style.display = 'none';
        }
    },

    applyLaptopFix(apply, isManual = false) {
        this.isLaptopFixApplied = apply;
        if (apply) {
            document.body.classList.add('laptop-optimized');
            localStorage.setItem('laptopOptimized', 'true');
            if (isManual && typeof window.showToast === 'function') {
                window.showToast("Layout Otimizado ativado manualmente", "success");
            }
        } else {
            document.body.classList.remove('laptop-optimized');
            localStorage.setItem('laptopOptimized', 'false');
            if (isManual && typeof window.showToast === 'function') {
                window.showToast("Layout original restaurado", "warning");
            }
        }
        if (isManual) this.update();
    },

    hide() {
        if (!this.badge) return;
        this.badge.style.display = 'none';
        sessionStorage.setItem('hideDebug', 'true');
        if (typeof window.showToast === 'function') {
            window.showToast("Debug ocultado nesta sessão", "warning");
        }
    }
};

window.DebugResolution = DebugResolution;

/**
 * DEBUG v8.27 - Análise Completa de Box-Model
 * Monitora mudanças e analisa TODOS os estilos relacionados ao posicionamento
 */
/**
 * DEBUG v8.28 - Análise Completa de Box-Model (Global + Abas Dinâmicas)
 * Monitora mudanças e analisa TODOS os estilos relacionados ao posicionamento
 */
function debugDynamicContentRealTime() {
    console.log('========== DEBUG BOX-MODEL COMPLETO (v8.28) ==========');
    console.log('🔍 Monitorando mudanças nos cards em tempo real (Global + Abas)...\n');

    // Função auxiliar de análise
    const analyzeElement = (element, label) => {
        if (!element) return;
        const newContent = element.innerText;

        console.log(`\n⚡ MUDANÇA DETECTADA - ${label}:`);
        console.log(`  ✏️ Novo conteúdo: "${newContent}"`);
        console.log(`  📏 Comprimento: ${newContent.length} caracteres`);

        // Analisar layout após conteúdo ser atualizado
        setTimeout(() => {
            const rect = element.getBoundingClientRect();
            const parent = element.parentElement.getBoundingClientRect();
            const computedStyle = window.getComputedStyle(element);
            const parentStyle = window.getComputedStyle(element.parentElement);

            console.log(`\n  📦 BOX-MODEL DO H2 (${label}):`);
            console.log(`    - margin-left: ${computedStyle.marginLeft}`);
            console.log(`    - margin-right: ${computedStyle.marginRight}`);
            console.log(`    - padding-left: ${computedStyle.paddingLeft}`);
            console.log(`    - padding-right: ${computedStyle.paddingRight}`);
            console.log(`    - display: ${computedStyle.display}`);
            console.log(`    - text-align: ${computedStyle.textAlign}`);
            console.log(`    - width: ${computedStyle.width}`);

            console.log(`\n  📦 BOX-MODEL DO PARENT (${label}):`);
            console.log(`    - display: ${parentStyle.display}`);
            console.log(`    - align-items: ${parentStyle.alignItems}`);
            console.log(`    - justify-content: ${parentStyle.justifyContent}`);
            console.log(`    - text-align: ${parentStyle.textAlign}`);
            console.log(`    - width: ${parentStyle.width}`);

            console.log(`\n  📐 DIMENSÕES E OFFSET (${label}):`);
            console.log(`    - Largura elemento: ${rect.width.toFixed(2)}px`);
            console.log(`    - Largura pai: ${parent.width.toFixed(2)}px`);
            console.log(`    - Offset X (do pai): ${(rect.left - parent.left).toFixed(2)}px`);

            // Análise visual de centralização
            const offsetX = rect.left - parent.left;
            const availableSpace = parent.width - rect.width; // Espaço que SOBRA
            const expectedOffset = availableSpace / 2;
            const difference = Math.abs(offsetX - expectedOffset);

            if (difference > 2) {
                console.log(`\n    🚨 PROBLEMA DE CENTRALIZAÇÃO DETECTADO!`);
                console.log(`       Offset atual: ${offsetX.toFixed(2)}px`);
                console.log(`       Offset esperado: ${expectedOffset.toFixed(2)}px`);
                console.log(`       Diferença: ${difference.toFixed(2)}px`);
            } else {
                console.log(`\n    ✅ Elemento está centralizado corretamente`);
            }
        }, 300); // Aguarda layout
    };

    // 1. Monitorar Abas Globais (Estáticas)
    const targets = ['topTurmaMat', 'topTurmaVesp', 'topTurmaNot', 'totalAcessos'];
    targets.forEach(id => {
        const element = document.getElementById(id);
        if (element) {
            const observer = new MutationObserver(() => analyzeElement(element, id));
            observer.observe(element, { childList: true, characterData: true, subtree: true });
        }
    });

    // 2. Monitorar Abas Dinâmicas (Recursos)
    // Observa o container de abas para quando novos conteúdos forem inseridos via JS
    const tabsContainer = document.getElementById('resourceTabsContainer');
    if (tabsContainer) {
        const tabObserver = new MutationObserver((mutations) => {
            mutations.forEach((mutation) => {
                mutation.addedNodes.forEach((node) => {
                    if (node.nodeType === 1 && node.classList.contains('tab-content')) {
                        // Nova aba adicionada! Vamos buscar os H2 de destaque dentro dela
                        const h2s = node.querySelectorAll('h2');
                        h2s.forEach((h2, index) => {
                            // Adiciona observer individual para cada H2 dinâmico
                            const innerObserver = new MutationObserver(() => analyzeElement(h2, `Dynamic-H2-${index}`));
                            innerObserver.observe(h2, { childList: true, characterData: true, subtree: true });

                            // Analisa estado inicial também
                            analyzeElement(h2, `Dynamic-H2-${index}-Init`);
                        });
                    }
                });
            });
        });
        tabObserver.observe(tabsContainer, { childList: true, subtree: true });
    }

    console.log('\n✅ Monitoramento ativo (v8.28)! Aguardando mudanças...');
    console.log('========== FIM SETUP DEBUG ==========\n');
}

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        DebugResolution.init();
        debugDynamicContentRealTime();
    });
} else {
    DebugResolution.init();
    debugDynamicContentRealTime();
}
