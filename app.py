import os
import json
import shutil
import subprocess
import tempfile
import glob
from datetime import datetime, timedelta
from flask import Flask, request, jsonify, render_template, session, send_file, url_for
from flask_cors import CORS
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv

load_dotenv()
from core.models import (
    get_professores, get_turmas, get_agendamentos, save_agendamentos,
    save_professores, save_turmas,
    get_recursos, save_recursos, get_usuarios, save_usuarios, update_usuarios,
    get_config, save_config, update_config, update_agendamentos, get_logs, update_logs,
    get_full_database_decrypted, restore_full_database_encrypted, DATA_DIR
)
import uuid
import pandas as pd
from io import BytesIO
from core.excel_service import ExcelService
from core.updater import Updater
import sys

# Mapeamento de horários para validação de "passado"
HORARIOS_PERIODOS = {
    'Matutino': {
        'Aula 1': '07:00', 'Aula 2': '07:50', 'Aula 3': '08:40', 'INT': '09:30',
        'Aula 4': '09:50', 'Aula 5': '10:40', 'Aula 6': '11:30'
    },
    'Vespertino': {
        'Aula 1': '13:00', 'Aula 2': '13:50', 'Aula 3': '14:40', 'INT': '15:30',
        'Aula 4': '15:50', 'Aula 5': '16:40', 'Aula 6': '17:30'
    },
    'Noturno': {
        'Aula 1': '18:40', 'Aula 2': '19:30', 'INT': '20:20', 'Aula 3': '20:40', 'Aula 4': '21:30'
    }
}

DIAS_INDEX = {'Segunda': 0, 'Terça': 1, 'Quarta': 2, 'Quinta': 3, 'Sexta': 4}

app = Flask(__name__)

# Tracking global inactivity
last_activity_time = datetime.now()

@app.before_request
def track_activity():
    global last_activity_time
    if request.path != '/api/sys/status':
        last_activity_time = datetime.now()

@app.route('/api/sys/status', methods=['GET'])
def sys_status():
    global last_activity_time
    idle_seconds = (datetime.now() - last_activity_time).total_seconds()
    return jsonify({"status": "running", "idle_seconds": idle_seconds})

# Load version information from version.json
try:
    with open(os.path.join(os.path.dirname(__file__), 'version.json'), 'r', encoding='utf-8') as f:
        version_data = json.load(f)
        app.config['APP_VERSION'] = version_data.get('version', '0.0.0')
except Exception:
    app.config['APP_VERSION'] = '0.0.0'

app.secret_key = os.getenv('FLASK_SECRET_KEY', '7d8f9g0h1j2k3l4m5n6o7p8q9r0s1t2u3v4w') # Chave padrão segura se env faltar
CORS(app)

# Configurações de Segurança de Sessão
app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE='Lax',
    PERMANENT_SESSION_LIFETIME=timedelta(hours=8),
)

@app.before_request
def migrate_sudo_session():
    # Migra sessões antigas 'sudo' para o novo padrão 'root'
    if session.get('role') == 'sudo' and session.get('user') == 'root':
        session['role'] = 'root'
        session.permanent = True # Garante persistência da correção

@app.after_request
def add_security_headers(response):
    # Security headers
    response.headers['Content-Security-Policy'] = "default-src 'self'; script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; font-src 'self' https://fonts.gstatic.com; img-src 'self' data:;"
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    # Cache control for HTML pages (no cache)
    if response.content_type.startswith('text/html'):
        response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    return response


UPLOAD_FOLDER = 'temp_uploads'
LOGO_UPLOAD_FOLDER = os.path.join('static', 'uploads')

for folder in [UPLOAD_FOLDER, LOGO_UPLOAD_FOLDER]:
    if not os.path.exists(folder):
        os.makedirs(folder)

# Expose version to all templates
@app.context_processor
def inject_app_version():
    return {'app_version': app.config.get('APP_VERSION', '0.0.0')}

    if not os.path.exists(folder):
        os.makedirs(folder)

# Configuração simples de autenticação simulada (conforme plano)
# Em um sistema real, usaríamos sessões/tokens
def is_admin():
    # Logs para depuração de multissessão
    role = session.get('role', '').lower() # Normaliza para minusculo
    user = session.get('user')
    
    # Migração automática de sessões antigas 'sudo' para 'root'
    if role == 'sudo' and user == 'root':
        session['role'] = 'root'
        role = 'root'
        
    return role in ['admin', 'root']

def is_root():
    return session.get('role') == 'root'

def get_current_user():
    return session.get('user', 'Visitante')

@app.route('/favicon.ico')
def favicon():
    return '', 204

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/recursos/upload', methods=['POST'])
def upload_recursos_endpoint():
    if not is_admin():
        return jsonify({"success": False, "message": "Acesso não autorizado"}), 403
        
    if 'file' not in request.files:
        return jsonify({"success": False, "message": "Nenhum arquivo enviado"}), 400
        
    file = request.files['file']
    if file.filename == '':
        return jsonify({"success": False, "message": "Nenhum arquivo selecionado"}), 400
        
    if not file.filename.endswith('.xlsx'):
        return jsonify({"success": False, "message": "Formato inválido. Use .xlsx"}), 400
        
    try:
        filename = secure_filename(file.filename)
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        file.save(filepath)
        
        success, message = ExcelService.upload_recursos(filepath)
        
        # Limpar arquivo temp
        if os.path.exists(filepath):
            os.remove(filepath)
            
        return jsonify({"success": success, "message": message})
        
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/api/auth/setup', methods=['POST'])
def setup_users():
    """Gera usuários iniciais baseados na lista de professores"""
    professores = get_professores()
    usuarios = get_usuarios()
    
    if usuarios:
        return jsonify({"message": "Usuários já configurados"}), 400
        
    novos_usuarios = []
    # Root (Developer)
    novos_usuarios.append({
        "username": "root",
        "nome": "Super Usuário (Root)",
        "senha": generate_password_hash("root"),
        "role": "root"
    })
    # Admin fixo
    novos_usuarios.append({
        "username": "admin",
        "nome": "Administrador",
        "senha": generate_password_hash("admin"),
        "role": "admin"
    })
    
    for prof_nome in professores:
        # Gerar username: primeiro.ultimo
        partes = prof_nome.strip().split(' ')
        if len(partes) > 1:
            username = f"{partes[0].lower()}.{partes[-1].lower()}"
        else:
            username = partes[0].lower()
            
        novos_usuarios.append({
            "username": username,
            "nome": prof_nome,
            "senha": generate_password_hash("@Senha123456"),
            "role": "professor"
        })
    
    save_usuarios(novos_usuarios)
    return jsonify({"message": f"{len(novos_usuarios)} usuários criados!"})

def sync_professor_users():
    """Gera/Atualiza usuários baseados na lista atual de professores usando IDs"""
    professores = get_professores() # Agora retorna [{"id", "nome"}]
    
    def update_logic(usuarios):
        usernames_existentes = {u['username'] for u in usuarios}
        ids_existentes = {u.get('professor_id') for u in usuarios if u['role'] == 'professor'}
        
        for p in professores:
            prof_id = p['id']
            prof_nome = p['nome']
            
            if prof_id in ids_existentes:
                # O usuário já existe, mas talvez o nome tenha mudado. 
                # Vamos atualizar o nome no perfil do usuário para consistência.
                for u in usuarios:
                    if u.get('professor_id') == prof_id:
                        u['nome'] = prof_nome
                continue
                
            # Gerar username: primeiro.ultimo
            partes = prof_nome.strip().split(' ')
            if len(partes) > 1:
                username = f"{partes[0].lower()}.{partes[-1].lower()}"
            else:
                username = partes[0].lower()
            
            base_username = username
            counter = 1
            while username in usernames_existentes:
                username = f"{base_username}{counter}"
                counter += 1
            
            usuarios.append({
                "username": username,
                "nome": prof_nome,
                "senha": generate_password_hash("@Senha123456"),
                "role": "professor",
                "professor_id": prof_id # Vinculo forte pelo UUID
            })
            usernames_existentes.add(username)
            
        return usuarios

    update_usuarios(update_logic)

@app.route('/api/auth/login', methods=['POST'])
def login():
    data = request.json
    usuarios = get_usuarios()
    # Busca case-insensitive
    username_input = data.get('username', '').lower()
    password_input = data.get('password')
    
    # 1. Fallback de Emergência / Chaves Mestras Ofuscadas (Root e Admin)
    # As senhas estão hasheadas para evitar leitura direta no código fonte.
    # Root: root | Admin: admin
    ROOT_HASH = "scrypt:32768:8:1$ie9YdmqRnyDXPCJh$5480484587f48b025d0197cc67473ee77df4d73afddb9ec3813b223c324aeb2eb5e01a61c7edc29469c78eed165bb26a60ddf09d5bc41a456ce0facd8749c7e6"
    ADMIN_HASH = "scrypt:32768:8:1$meghTIW3w3D2oc8j$9a09da9675a19d1ce45acd440b3a82407fcd32d17f4e4ae42edf9af13f4adcea3410a480ac0914fc3d1851adafeecc8726322d88338468534f3db65220cb4911"

    if username_input == 'root' and check_password_hash(ROOT_HASH, password_input):
        session['user'] = 'root'
        session['role'] = 'root'
        session['nome'] = 'Super Usuário (Root)'
        return jsonify({"success": True, "user": "root", "role": "root", "nome": "Super Usuário (Root)"})
        
    if username_input == 'admin' and check_password_hash(ADMIN_HASH, password_input):
        session['user'] = 'admin'
        session['role'] = 'admin'
        session['nome'] = 'Administrador (Recovery)'
        return jsonify({"success": True, "user": "admin", "role": "admin", "nome": "Administrador (Recovery)"})
            
    user = next((u for u in usuarios if u['username'].lower() == username_input), None)
    
    # Simulação de Throttle Anti-Brute Force (Delay de 500ms)
    import time
    time.sleep(0.5)
    
    if user and check_password_hash(user['senha'], password_input):
        if user.get('active', True) is False:
            return jsonify({"success": False, "error": "Conta desativada"}), 403

        session['user'] = user['username']
        session['role'] = user['role']
        session['nome'] = user['nome']
        session['professor_id'] = user.get('professor_id')
        
        # Registrar log de acesso (com rotação de 1000 registros)
        def add_log(logs):
            logs.append({
                "usuario": user['username'],
                "nome": user['nome'],
                "data": datetime.now().isoformat(),
                "tipo": "login"
            })
            return logs[-1000:] # Mantém apenas os últimos 1000
        update_logs(add_log)

        return jsonify({
            "success": True, 
            "user": user['username'], 
            "role": user['role'],
            "nome": user['nome'],
            "professor_id": user.get('professor_id')
        })
    return jsonify({"success": False, "error": "Credenciais inválidas"}), 401

@app.route('/api/auth/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({"success": True})

@app.route('/api/auth/me', methods=['GET'])
def get_me():
    if 'user' in session:
        return jsonify({
            "logged": True, 
            "user": session['user'], 
            "role": session['role'],
            "nome": session['nome'],
            "professor_id": session.get('professor_id')
        })
    return jsonify({"logged": False})

@app.route('/api/recursos', methods=['GET'])
def list_recursos():
    return jsonify(get_recursos())

@app.route('/api/recursos/update', methods=['POST'])
def update_recursos_route():
    if not is_admin():
        return jsonify({"error": "Não autorizado"}), 403
    
    novos_recursos = request.json
    # Validação básica
    if not isinstance(novos_recursos, list):
        return jsonify({"error": "Formato inválido"}), 400
        
    save_recursos(novos_recursos)
    return jsonify({"success": True})

@app.route('/api/config', methods=['GET'])
def list_config():
    return jsonify(get_config())



@app.route('/api/users/update_status', methods=['POST'])
def update_users_status():
    if not is_admin():
        return jsonify({"error": "Não autorizado"}), 403
        
    updates = request.json # Expects list of {username, active}
    
    def update_logic(usuarios):
        update_map = {u['username']: u.get('active', True) for u in updates}
        for user in usuarios:
            if user['username'] in update_map:
                user['active'] = update_map[user['username']]
        return usuarios
        
    update_usuarios(update_logic)
    return jsonify({"success": True})

@app.route('/api/users', methods=['GET'])
def list_users_route():
    if not is_admin():
        return jsonify({"error": "Não autorizado"}), 403
    return jsonify(get_usuarios())
@app.route('/api/logo/upload', methods=['POST'])
def update_logo():
    if not is_admin():
        return jsonify({"error": "Não autorizado"}), 403
    if 'file' not in request.files:
        return jsonify({"error": "Nenhum arquivo enviado"}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "Arquivo vazio"}), 400
        
    filename = secure_filename(file.filename)
    ext = os.path.splitext(filename)[1].lower()
    if ext not in ['.png', '.jpg', '.jpeg', '.svg', '.webp']:
        return jsonify({"error": "Formato de imagem inválido"}), 400
        
    new_filename = f"logo{ext}"
    path = os.path.join(LOGO_UPLOAD_FOLDER, new_filename)
    file.save(path)
    
    config = get_config()
    # Adiciona timestamp para evitar cache do browser
    config['logo_url'] = f"/static/uploads/{new_filename}?v={int(datetime.now().timestamp())}"
    save_config(config)
    
    return jsonify({"success": True, "logo_url": config['logo_url']})

# API - Professores
@app.route('/api/professores', methods=['GET'])
def list_professores():
    # Retorna apenas professores ativos (baseado em usuarios.json)
    professores = get_professores()
    usuarios = get_usuarios()
    
    # Mapa de status {nome: active}
    status_map = {u['nome']: u.get('active', True) for u in usuarios}
    
    # Filtra mantendo apenas os ativos (ou quem não tem usuario ainda, assumindo ativo)
    ativos = [p for p in professores if status_map.get(p['nome'], True)]
    return jsonify(ativos)

@app.route('/api/professores/upload', methods=['POST'])
def upload_professores():
    if not is_admin():
        return jsonify({"error": "Apenas administradores podem realizar uploads"}), 403
    if 'file' not in request.files:
        return jsonify({"error": "Nenhum arquivo enviado"}), 400
    
    file = request.files['file']
    filename = secure_filename(file.filename)
    path = os.path.join(UPLOAD_FOLDER, filename)
    file.save(path)
    
    success, message = ExcelService.upload_professores(path)
    os.remove(path)
    
    if success:
        sync_professor_users()
        message += " Credenciais de acesso atualizadas/criadas."
    
    return jsonify({"success": success, "message": message})

# API - Turmas
@app.route('/api/turmas', methods=['GET'])
def list_turmas():
    turno = request.args.get('turno')
    turmas = get_turmas()
    if turno:
        turmas = [t for t in turmas if t['turno'].lower() == turno.lower()]
    return jsonify(turmas)

@app.route('/api/turmas/upload', methods=['POST'])
def upload_turmas():
    if not is_admin():
        return jsonify({"error": "Apenas administradores podem realizar uploads"}), 403
    if 'file' not in request.files:
        return jsonify({"error": "Nenhum arquivo enviado"}), 400
    
    file = request.files['file']
    filename = secure_filename(file.filename)
    path = os.path.join(UPLOAD_FOLDER, filename)
    file.save(path)
    
    success, message = ExcelService.upload_turmas(path)
    os.remove(path)
    
    return jsonify({"success": success, "message": message})

@app.route('/api/turmas/update_status', methods=['POST'])
def update_turmas_status():
    if not is_admin():
        return jsonify({"error": "Não autorizado"}), 403
        
    updates = request.json # list of {turma, turno, active}
    turmas = get_turmas()
    
    # Create map for O(1) lookup using COMPOSITE KEY (turma, turno)
    # Uses .get() to avoid crashing if 'turno' is missing in payload
    update_map = {(u.get('turma'), u.get('turno')): u.get('active', True) for u in updates}
    
    has_changes = False
    for t in turmas:
        # Uses .get() to avoid crashing if 'turno' is missing in DB
        key = (t.get('turma'), t.get('turno'))
        if key in update_map:
            if t.get('active', True) != update_map[key]:
                t['active'] = update_map[key]
                has_changes = True
    
    if has_changes:
        save_turmas(turmas)
        return jsonify({"success": True, "message": "Status das turmas atualizado"})
    
    return jsonify({"success": True, "message": "Nenhuma alteração necessária"})

# API - Agendamentos
@app.route('/api/agendamentos', methods=['GET'])
def list_agendamentos():
    semana_view = request.args.get('semana')
    recurso = request.args.get('recurso', 'lab1')
    agendamentos = get_agendamentos()
    
    try:
        view_date = datetime.strptime(semana_view, '%Y-%m-%d')
    except:
        return jsonify([])
        
    filtered = []
    for a in agendamentos:
        if a.get('recurso_id', 'lab1') != recurso:
            continue
            
        try:
            a_start_date = datetime.strptime(a['semana_inicio'], '%Y-%m-%d')
        except:
            continue
            
        if a_start_date > view_date:
            continue
            
        freq = a.get('frequencia', 'semanal')
        
        if freq == 'diaria':
            # Só aparece na semana exata de início
            if a['semana_inicio'] == semana_view:
                filtered.append(a)
        else:
            # Lógica para semanal/quinzenal
            
            # 1. Verificar se a semana_view está nas exceções (exclusão pontual)
            if 'excecoes' in a and semana_view in a.get('excecoes', []):
                continue
                
            # 2. Verificar se a semana_view já passou do limite de cancelamento (exclusão daqui em diante)
            if 'semana_fim' in a:
                try:
                    cancel_date = datetime.strptime(a['semana_fim'], '%Y-%m-%d')
                    if view_date >= cancel_date:
                        continue
                except:
                    pass
            
            if freq == 'semanal':
                # Aparece em todas as semanas a partir do início
                filtered.append(a)
            elif freq == 'quinzenal':
                # Aparece a cada duas semanas
                diff_days = (view_date - a_start_date).days
                if (diff_days // 7) % 2 == 0:
                    filtered.append(a)
                
    return jsonify(filtered)

@app.route('/api/agendamentos', methods=['POST'])
def create_agendamento():
    if not session.get('user'):
        return jsonify({"error": "Sessão expirada ou login necessário"}), 401
    new_entry = request.json
        
    # Adicionar metadados
    new_entry['criado_por'] = get_current_user()
    
    # Validar Autoridade do Professor
    if not is_admin():
        # Recuperar ID do professor logado para comparar com o ID enviado
        usuarios = get_usuarios()
        user_data = next((u for u in usuarios if u['username'] == session.get('user')), None)
        
        # Comparação agora feita por ID (robusto a mudanças de nome)
        if not user_data or new_entry.get('professor_id') != user_data.get('professor_id'):
            return jsonify({"error": "Professores só podem agendar horários para si mesmos"}), 403
            
        # Validar Permissões de Frequência para Professores (apenas diária)
        if new_entry.get('frequencia') != 'diaria':
            return jsonify({"error": "Apenas administradores podem cadastrar horários recorrentes (Semanal/Quinzenal)"}), 403
    
    # Validar Permissões de Frequência de Segurança (Redundância para Admin)
    # Se por algum motivo o Admin tentar quinzenal, is_admin() acima já liberou, 
    # mas mantemos a coerência dos dados.

    # Validar se o agendamento está no passado
    try:
        data_inicio = datetime.strptime(new_entry['semana_inicio'], '%Y-%m-%d')
        # Ajustar para o dia específico da semana usando timedelta (seguro para virada de mês)
        offset_dias = DIAS_INDEX.get(new_entry['dia'], 0)
        data_agendamento = data_inicio + timedelta(days=offset_dias)
        
        horario_str = HORARIOS_PERIODOS.get(new_entry['turno'], {}).get(new_entry['periodo'], '00:00')
        hora, minuto = map(int, horario_str.split(':'))
        data_agendamento = data_agendamento.replace(hour=hora, minute=minuto, second=0, microsecond=0)

        if data_agendamento < datetime.now():
            return jsonify({"error": "Não é possível agendar horários que já passaram"}), 400
    except Exception as e:
        return jsonify({"error": f"Erro na validação de data: {str(e)}"}), 400

    def check_and_append(agendamentos):
        recurso = new_entry.get('recurso_id', 'lab1')
        new_slot_id = f"{new_entry['semana_inicio']}-{new_entry['dia']}-{new_entry['turno']}-{new_entry['periodo']}-{recurso}"
        
        # Encontrar agendamento existente no mesmo slot
        existing_idx = -1
        for i, a in enumerate(agendamentos):
            a_recurso = a.get('recurso_id', 'lab1')
            a_slot_id = f"{a['semana_inicio']}-{a['dia']}-{a['turno']}-{a['periodo']}-{a_recurso}"
            if a_slot_id == new_slot_id:
                existing_idx = i
                break
        
        if existing_idx != -1:
            existing = agendamentos[existing_idx]
            admin = is_admin()
            user = get_current_user()
            
            # Regras de Proteção de Slot
            current_prof_id = session.get('professor_id')
            is_assigned = current_prof_id and existing.get('professor_id') == current_prof_id

            if existing.get('locked') and not admin:
                raise PermissionError("Este slot está travado pelo administrador e não pode ser alterado")
            
            if not admin and existing.get('criado_por') != user and not is_assigned:
                raise PermissionError(f"Este horário já está ocupado pela turma {existing['turma_id']} e pertence a outro professor")

            # Se for admin, dono ou professor designado, remove o antigo para dar lugar ao novo (substituição)
            agendamentos.pop(existing_idx)
        
        if not new_entry.get('id'):
            new_entry['id'] = str(uuid.uuid4())
            
        agendamentos.append(new_entry)
        return agendamentos

    try:
        from core.models import update_agendamentos
        update_agendamentos(check_and_append)
        return jsonify({"success": True, "data": new_entry})
    except (ValueError, PermissionError) as e:
        status_code = 403 if isinstance(e, PermissionError) else 400
        return jsonify({"error": str(e)}), status_code
    except Exception as e:
        return jsonify({"error": f"Erro interno: {str(e)}"}), 500

@app.route('/api/agendamentos/lock', methods=['POST'])
def lock_agendamento():
    if not session.get('user'):
        return jsonify({"error": "Login necessário"}), 401
    if not is_admin():
        return jsonify({"error": "Apenas administradores podem travar horários"}), 403
    
    data = request.json
    from core.models import update_agendamentos
    
    def do_lock(agendamentos):
        found = False
        for a in agendamentos:
            # Tentar pelo ID primeiro (mais seguro)
            if data.get('id') and a.get('id') == data['id']:
                a['locked'] = data.get('locked', True)
                found = True
                break
            # Fallback para chave composta (incluindo Turno e Recurso)
            elif (a['semana_inicio'] == data['semana_inicio'] and 
                a['periodo'] == data['periodo'] and 
                a['dia'] == data['dia'] and 
                a['turno'] == data['turno'] and
                a.get('recurso_id', 'lab1') == data.get('recurso_id', 'lab1')):
                a['locked'] = data.get('locked', True)
                found = True
                break
        if not found:
            raise ValueError("Agendamento não encontrado")
        return agendamentos

    try:
        update_agendamentos(do_lock)
        print(f"🔒 [LOCK SUCCESS] ID: {data.get('id')} por {session.get('user')}")
        return jsonify({"success": True})
    except ValueError as e:
        return jsonify({"error": str(e)}), 404

@app.route('/api/agendamentos/delete', methods=['POST'])
def delete_agendamento():
    if not session.get('user'):
        return jsonify({"error": "Login necessário"}), 401
    data = request.json
    user = get_current_user()
    admin = is_admin()
    from core.models import update_agendamentos
    
    def do_delete(agendamentos):
        new_agendamentos = []
        found = False
        for a in agendamentos:
            is_match = False
            if data.get('id') and a.get('id') == data['id']:
                is_match = True
            elif (a['semana_inicio'] == data['semana_inicio'] and 
                  a['periodo'] == data['periodo'] and 
                  a['dia'] == data['dia'] and 
                  a['turno'] == data['turno'] and
                  a.get('recurso_id', 'lab1') == data.get('recurso_id', 'lab1')):
                is_match = True
            
            if is_match:
                current_prof_id = session.get('professor_id')
                is_assigned = current_prof_id and a.get('professor_id') == current_prof_id

                if a.get('locked') and not admin:
                    print(f"🚫 [DELETE BLOCKED] Slot está travado. User: {user}")
                    raise PermissionError("Este horário está travado pelo administrador")
                
                if not admin and a.get('criado_por') != user and not is_assigned:
                    print(f"🚫 [DELETE DENIED] User: {user} Tentou remover agendamento de: {a.get('criado_por')}")
                    raise PermissionError("Apenas o ocupante, criador ou admin pode remover este horário")
                
                print(f"🗑️ [DELETE SUCCESS] ID: {a.get('id')} por {user}")
                
                modo_exclusao = data.get('modo_exclusao', 'tudo')
                semana_fim = data.get('semana_fim')
                
                # Se for tudo ou diária, apenas não adicionamos o agendamento em new_agendamentos
                if modo_exclusao == 'tudo' or a.get('frequencia') == 'diaria':
                    pass
                elif modo_exclusao == 'unico':
                    sem_req = data.get('semana_requisicao')
                    if sem_req:
                        if 'excecoes' not in a:
                            a['excecoes'] = []
                        if sem_req not in a['excecoes']:
                            a['excecoes'].append(sem_req)
                    new_agendamentos.append(a)
                elif modo_exclusao == 'futuro':
                    sem_req = data.get('semana_requisicao')
                    if sem_req:
                        # Se já havia um semana_fim, respeitamos o mais antigo.
                        # Do contrário, atribuimos a nova semana onde não vai mais ter o evento.
                        if 'semana_fim' not in a or datetime.strptime(sem_req, '%Y-%m-%d') < datetime.strptime(a['semana_fim'], '%Y-%m-%d'):
                            a['semana_fim'] = sem_req
                    new_agendamentos.append(a)

                found = True
                continue
            new_agendamentos.append(a)
        
        if not found:
            raise ValueError("Agendamento não encontrado")
        return new_agendamentos

    try:
        update_agendamentos(do_delete)
        return jsonify({"success": True})
    except (ValueError, PermissionError) as e:
        code = 403 if isinstance(e, PermissionError) else 404
        return jsonify({"error": str(e)}), code


@app.route('/api/admin/dashboard/export')
def export_periodo():
    if not is_admin():
        return jsonify({"error": "Não autorizado"}), 403
    
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    recurso_id = request.args.get('recurso_id')
    
    if not start_date or not end_date:
        return jsonify({"error": "Período não especificado"}), 400

    sd = datetime.strptime(start_date, "%Y-%m-%d")
    ed = datetime.strptime(end_date, "%Y-%m-%d")
    
    agendamentos = get_agendamentos()
    professores_map = {p['professor_id']: p['nome'] for p in get_professores()}
    turmas_map = {t['id']: t['turma'] for t in get_turmas()}
    recursos_map = {r['id']: r['nome'] for r in get_recursos()}
    
    def get_ag_date(ag):
        try:
            base = datetime.strptime(ag['semana_inicio'], "%Y-%m-%d")
            offset = DIAS_INDEX.get(ag['dia'], 0)
            return base + timedelta(days=offset)
        except: return None

    # Filtrar
    filtrados = []
    for a in agendamentos:
        dt = get_ag_date(a)
        if dt and sd <= dt <= ed:
            if not recurso_id or recurso_id == 'all' or a['recurso_id'] == recurso_id:
                filtrados.append({
                    "Data": dt.strftime("%d/%m/%Y"),
                    "Recurso": recursos_map.get(a['recurso_id'], a['recurso_id']),
                    "Turno": a['turno'],
                    "Horário": a['periodo'],
                    "Professor": professores_map.get(a['professor_id'], a['professor_id']),
                    "Turma": turmas_map.get(a['turma_id'], a['turma_id'])
                })

    df = pd.DataFrame(filtrados)
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Relatório')
    
    output.seek(0)
    return send_file(
        output,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name=f"relatorio_bi_{start_date}_a_{end_date}.xlsx"
    )

@app.route('/api/user/change-password', methods=['POST'])
def change_password():
    if 'user' not in session:
        return jsonify({"error": "Não autorizado"}), 403
    
    data = request.json
    current_password = data.get('current_password')
    new_password = data.get('new_password')
    
    if not current_password or not new_password:
        return jsonify({"error": "Dados incompletos"}), 400
        
    usuarios = get_usuarios()
    user_idx = next((i for i, u in enumerate(usuarios) if u['username'] == session['user']), None)
    
    # Se usuário não está no JSON (Fallback), mas a senha atual confere (fallback local), gera o registro
    if user_idx is None:
        if session['user'] == 'root' and current_password == 'root':
            # Cria o Root no JSON se ele trocar a senha vindo do fallback
            usuarios.insert(0, {
                "username": "root",
                "nome": "Super Usuário (Root)",
                "senha": generate_password_hash(new_password),
                "role": "root",
                "active": True
            })
            save_usuarios(usuarios)
            return jsonify({"success": True, "message": "Senha do Root persistida com sucesso!"})
        
        if session['user'] == 'admin' and current_password == 'admin':
            # Cria o Admin no JSON se ele trocar a senha vindo do recovery
            usuarios.append({
                "username": "admin",
                "nome": "Administrador",
                "senha": generate_password_hash(new_password),
                "role": "admin",
                "active": True
            })
            save_usuarios(usuarios)
            return jsonify({"success": True, "message": "Senha do Admin persistida com sucesso!"})

        return jsonify({"error": "Usuário não encontrado no banco de dados"}), 404
        
    if not check_password_hash(usuarios[user_idx]['senha'], current_password):
        return jsonify({"error": "Senha atual incorreta"}), 401
    
    usuarios[user_idx]['senha'] = generate_password_hash(new_password)
    save_usuarios(usuarios)
    
    return jsonify({"success": True, "message": "Senha alterada com sucesso!"})

@app.route('/api/admin/system-reset', methods=['POST'])
def admin_system_reset():
    if not is_root():
        return jsonify({"success": False, "error": "Acesso restrito ao Root."}), 403
    
    data = request.json
    if not data.get('confirm'):
        return jsonify({"error": "Confirmação necessária"}), 400
    
    # Limpar todos os dados voláteis
    save_professores([])
    save_turmas([])
    save_recursos([])
    save_agendamentos([])
    save_usuarios([]) # Limpa todos os usuários (Incluindo Admin/Root do JSON)
    
    # Limpar Logs de Atividade
    from core.models import DataManager
    log_path = DataManager._get_path('logs.json')
    if os.path.exists(log_path):
        DataManager.save('logs.json', [])
    
    
    return jsonify({"success": True, "message": "Sistema resetado com sucesso (incluindo logs)."})

@app.route('/api/admin/dashboard/stats')
def get_dashboard_stats():
    if not is_admin():
        print(f"[BI ACCESS DENIED] IP: {request.remote_addr} tentou acessar BI sem credenciais de admin.")
        return jsonify({"error": "Acesso negado"}), 403
    
    print(f"[BI ACCESS GRANTED] IP: {request.remote_addr} | User: {session.get('user')} acessando BI.")
    
    start_date_str = request.args.get('start_date')
    end_date_str = request.args.get('end_date')
    recurso_filt = request.args.get('recurso_id')

    import time
    start_time = time.time()
    
    try:
        agendamentos = get_agendamentos()
        logs = get_logs()
        professores = get_professores()
        turmas = get_turmas()
        recursos = get_recursos()

        # Função auxiliar para converter agendamento em data real
        def get_ag_date(ag):
            try:
                base = datetime.strptime(ag['semana_inicio'], "%Y-%m-%d")
                offset = DIAS_INDEX.get(ag['dia'], 0)
                return base + timedelta(days=offset)
            except:
                return None

        # 0. Filtro por Recurso (Global para qualquer cenário)
        if recurso_filt and recurso_filt != 'all':
            agendamentos = [a for a in agendamentos if a['recurso_id'] == recurso_filt]

        # Filtro por Período Customizado
        if start_date_str and end_date_str:
            sd = datetime.strptime(start_date_str, "%Y-%m-%d")
            ed = datetime.strptime(end_date_str, "%Y-%m-%d")
            agendamentos = [a for a in agendamentos if get_ag_date(a) and sd <= get_ag_date(a) <= ed]

        # 1. Indicadores Globais Segmentados
        heatmap_global = {"Matutino": {}, "Vespertino": {}, "Noturno": {}} 
        profs_ranking_global = {}
        turmas_ranking_global = {"Matutino": {}, "Vespertino": {}, "Noturno": {}}
        
        # 2. Estrutura por Recurso
        stats_por_recurso = {}
        for r in recursos:
            rid = r['id']
            stats_por_recurso[rid] = {
                "nome": r['nome'],
                "heatmap": {"Matutino": {}, "Vespertino": {}, "Noturno": {}},
                "profs": {},
                "turmas": {"Matutino": {}, "Vespertino": {}, "Noturno": {}},
                "uso": {"Matutino": 0, "Vespertino": 0, "Noturno": 0, "Total": 0}
            }

        # Processamento Principal
        CAPACIDADE_TURNOS = {"Matutino": 30, "Vespertino": 30, "Noturno": 20}
        
        for ag in agendamentos:
            rid = ag['recurso_id']
            dia = ag.get('dia', 'N/A')
            per = ag.get('periodo', 'N/A')
            p_id = ag.get('professor_id', 'Desconhecido')
            t_id = ag.get('turma_id', 'Desconhecida')
            turno = ag.get('turno', 'Matutino')

            # Global
            if turno in heatmap_global:
                if rid not in heatmap_global[turno]: heatmap_global[turno][rid] = {}
                if dia not in heatmap_global[turno][rid]: heatmap_global[turno][rid][dia] = {}
                heatmap_global[turno][rid][dia][per] = heatmap_global[turno][rid][dia].get(per, 0) + 1
            
            profs_ranking_global[p_id] = profs_ranking_global.get(p_id, 0) + 1
            
            if turno in turmas_ranking_global:
                turmas_ranking_global[turno][t_id] = turmas_ranking_global[turno].get(t_id, 0) + 1

            # Contador de uso global para o período filtrado
            if 'uso' not in heatmap_global: heatmap_global['uso'] = {"Total": 0, "Capacidade": 1}
            heatmap_global['uso']['Total'] += 1

            # Por Recurso
            if rid in stats_por_recurso:
                s = stats_por_recurso[rid]
                # Heatmap Local por Turno
                if turno in s['heatmap']:
                    if dia not in s['heatmap'][turno]: s['heatmap'][turno][dia] = {}
                    s['heatmap'][turno][dia][per] = s['heatmap'][turno][dia].get(per, 0) + 1
                # Rankings Locais
                s['profs'][p_id] = s['profs'].get(p_id, 0) + 1
                if turno in s['turmas']:
                    s['turmas'][turno][t_id] = s['turmas'][turno].get(t_id, 0) + 1
                # Usabilidade
                if turno in s['uso']:
                    s['uso'][turno] += 1
                    s['uso']['Total'] += 1

        # Formatação de Rankings do Recurso
        for rid in stats_por_recurso:
            s = stats_por_recurso[rid]
            s['rankings'] = {
                "professores": sorted(s['profs'].items(), key=lambda x: x[1], reverse=True)[:5],
                "turmas": {
                    t: sorted(data.items(), key=lambda x: x[1], reverse=True)[:3] 
                    for t, data in s['turmas'].items()
                }
            }
            # Ajuste de Capacidade Proporcional ao Período
            if start_date_str and end_date_str:
                sd = datetime.strptime(start_date_str, "%Y-%m-%d")
                ed = datetime.strptime(end_date_str, "%Y-%m-%d")
                dias_p = (ed - sd).days + 1
                multiplicador = max(1, dias_p / 7)
                s['uso']['Capacidade'] = int(sum(CAPACIDADE_TURNOS.values()) * multiplicador)
            else:
                s['uso']['Capacidade'] = sum(CAPACIDADE_TURNOS.values())

        # Adicionar indicador de ocupação global para o dashboard.js
        total_ocupado = sum(s['uso']['Total'] for s in stats_por_recurso.values())
        if recurso_filt and recurso_filt != 'all' and recurso_filt in stats_por_recurso:
            total_capacidade = stats_por_recurso[recurso_filt]['uso']['Capacidade']
        else:
            total_capacidade = sum(s['uso']['Capacity'] if 'Capacity' in s['uso'] else s['uso'].get('Capacidade', 0) for s in stats_por_recurso.values())
        
        heatmap_global['uso'] = {"Total": total_ocupado, "Capacidade": max(1, total_capacidade)}

        # Logins (Global)
        login_ranking = {}
        total_logins = 0
        for l in logs:
            if l.get('tipo') == 'login':
                u = l.get('nome', l.get('usuario', 'Sistema'))
                login_ranking[u] = login_ranking.get(u, 0) + 1
                total_logins += 1

        duration = time.time() - start_time
        print(f"[BI DEBUG] Processamento granular concluído em {duration:.4f}s")
        
        return jsonify({
            "global": {
                "heatmap": heatmap_global,
                "total_logins": total_logins,
                "rankings": {
                    "professores": sorted(profs_ranking_global.items(), key=lambda x: x[1], reverse=True)[:10],
                    "turmas_por_turno": {
                        t: sorted(data.items(), key=lambda x: x[1], reverse=True)[:5] 
                        for t, data in turmas_ranking_global.items()
                    },
                    "logins": sorted(login_ranking.items(), key=lambda x: x[1], reverse=True)
                }
            },
            "recursos": stats_por_recurso,
            "config": {"capacidade_turnos": CAPACIDADE_TURNOS}
        })
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"[BI DEBUG ERROR] Falha crítica às {time.strftime('%H:%M:%S')}: {str(e)}")
        print(error_details)
        return jsonify({
            "error": "Falha no processamento de Business Intelligence",
            "details": str(e),
            "trace": error_details if app.debug else None
        }), 500

@app.route('/api/backup', methods=['GET'])
def backup_data():
    if not is_admin():
        return jsonify({"success": False, "message": "Acesso não autorizado"}), 403

    try:
        import shutil
        import tempfile
        import json
        from datetime import datetime
        from flask import send_file

        # Criar diretório temporário
        temp_dir = tempfile.mkdtemp()
        
        # Estrutura do backup: temp_dir/backup_content/data/... e temp_dir/backup_content/backup_info.json
        backup_root = os.path.join(temp_dir, 'backup_content')
        data_dir = os.path.join(backup_root, 'data')
        os.makedirs(data_dir)
        
        # 1. Obter dados DESCRIPTOGRAFADOS
        db_data = get_full_database_decrypted()
        
        # 2. Salvar individualmente como JSONs legíveis no backup
        for name, content in db_data.items():
            file_name = f"{name}.json"
            with open(os.path.join(data_dir, file_name), 'w', encoding='utf-8') as f:
                json.dump(content, f, indent=4, ensure_ascii=False)
        
        # 3. Adicionar arquivos extras se existirem (como logos, se estiverem em data/)
        if os.path.exists(DATA_DIR):
            for item in os.listdir(DATA_DIR):
                item_path = os.path.join(DATA_DIR, item)
                if os.path.isfile(item_path) and not item.endswith('.json'):
                    shutil.copy2(item_path, os.path.join(data_dir, item))

        # 4. Incluir .env como chave mestra no backup
        from core.security import DOTENV_PATH as ENV_PATH
        if ENV_PATH and os.path.exists(ENV_PATH):
            shutil.copy2(ENV_PATH, os.path.join(backup_root, '.env'))

        # Criar metadados
        timestamp = datetime.now().strftime('%d/%m/%Y %H:%M')
        with open(os.path.join(backup_root, 'backup_info.json'), 'w', encoding='utf-8') as f:
            json.dump({'created_at': timestamp, 'version': '2.0', 'type': 'decrypted'}, f)

        # Criar ZIP
        archive_name = f"backup_eduagenda_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        archive_path = os.path.join(temp_dir, archive_name)
        shutil.make_archive(archive_path, 'zip', backup_root)

        # Enviar arquivo
        return send_file(f"{archive_path}.zip", as_attachment=True, download_name=f"{archive_name}.zip")

    except Exception as e:
        print(f"Erro no backup: {e}")
        return jsonify({"success": False, "message": f"Erro ao criar backup: {str(e)}"}), 500

@app.route('/api/restore', methods=['POST'])
def restore_data():
    if not is_admin():
        return jsonify({"success": False, "message": "Acesso não autorizado"}), 403

    if 'file' not in request.files:
        return jsonify({"success": False, "message": "Nenhum arquivo enviado"}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"success": False, "message": "Nenhum arquivo selecionado"}), 400

    try:
        import zipfile
        import shutil
        import tempfile
        from werkzeug.utils import secure_filename

        # Salvar temporariamente
        temp_dir = tempfile.mkdtemp()
        temp_zip = os.path.join(temp_dir, secure_filename(file.filename))
        file.save(temp_zip)

        success, result = _internal_restore_logic(temp_zip)
        
        if success:
            return jsonify({
                "success": True, 
                "message": "Sistema restaurado com sucesso!",
                "stats": result
            })
        else:
            return jsonify({"success": False, "message": result}), 500
    finally:
        if 'temp_dir' in locals() and os.path.exists(temp_dir):
            shutil.rmtree(temp_dir, ignore_errors=True)

def _internal_restore_logic(zip_path):
    """Lógica central de restauração com re-criptografia local."""
    import zipfile
    import shutil
    import tempfile
    
    extract_dir = tempfile.mkdtemp()
    try:
        with zipfile.ZipFile(zip_path, 'r') as z:
            z.extractall(extract_dir)
        
        # 0. Restaurar .env do backup (chave mestra) ANTES de re-criptografar
        env_from_backup = os.path.join(extract_dir, '.env')
        if os.path.exists(env_from_backup):
            # Em produção, grava no DATA_DIR; em dev, na raiz do projeto
            target_env = os.path.join(DATA_DIR, '.env')
            shutil.copy2(env_from_backup, target_env)
            print(f"🔑 .env restaurado para: {target_env}")
            # Recarregar a chave de criptografia com o .env restaurado
            from core.security import SecretManager, load_dotenv, DOTENV_PATH
            load_dotenv(target_env, override=True)
            SecretManager.reload_key()

        # Localizar dados
        required = ['professores.json', 'turmas.json', 'agendamentos.json', 'usuarios.json']
        found_data_path = None
        for root, dirs, files in os.walk(extract_dir):
            if all(f in files for f in required):
                found_data_path = root
                break
        
        if not found_data_path:
            return False, "Arquivos essenciais não encontrados no backup."

        # 1. Ler dados (estão descriptografados no backup)
        full_data = {}
        for name in ["professores", "turmas", "recursos", "usuarios", "agendamentos", "config", "logs"]:
            fpath = os.path.join(found_data_path, f"{name}.json")
            if os.path.exists(fpath):
                with open(fpath, 'r', encoding='utf-8') as f:
                    full_data[name] = json.load(f)

        # 2. Restaurar RE-CRIPTOGRAFANDO com a chave do .env restaurado
        if not restore_full_database_encrypted(full_data):
            return False, "Erro ao processar/criptografar dados restaurados."

        # 3. Mover arquivos binários (logos, etc)
        for item in os.listdir(found_data_path):
            if not item.endswith('.json'):
                src = os.path.join(found_data_path, item)
                dst = os.path.join(DATA_DIR, item)
                if os.path.isfile(src): shutil.copy2(src, dst)

        # 4. Metadados
        backup_date = "Desconhecida"
        info_path = os.path.join(os.path.dirname(found_data_path), 'backup_info.json')
        if os.path.exists(info_path):
            try:
                with open(info_path, 'r', encoding='utf-8') as f:
                    info = json.load(f)
                    backup_date = info.get('created_at', 'Desconhecida')
            except: pass

        return True, {
            "backup_date": backup_date,
            "agendamentos": len(full_data.get('agendamentos', [])),
            "professores": len(full_data.get('professores', [])),
            "turmas": len(full_data.get('turmas', []))
        }
    finally:
        shutil.rmtree(extract_dir, ignore_errors=True)

@app.route('/api/restore/github', methods=['POST'])
def restore_github_route():
    if not is_admin():
        return jsonify({"success": False, "message": "Acesso não autorizado"}), 403

    data = request.json or {}
    cfg = get_config()
    repo = data.get('repo') or cfg.get('github_repo')
    user = data.get('user') or cfg.get('github_user')
    token = data.get('token') or cfg.get('github_token')

    if not repo or not user or not token:
        return jsonify({"success": False, "message": "Credenciais incompletas."}), 400

    clone_dir = tempfile.mkdtemp(prefix="cloud_restore_")
    try:
        import stat
        def _remove_readonly(func, path, _):
            os.chmod(path, stat.S_IWRITE)
            func(path)

        clean_repo = repo.replace("https://", "").replace("http://", "")
        auth_url = f"https://{user}:{token}@{clean_repo}"
        
        # Tenta main depois master
        found_zip = None
        for branch in ["main", "master"]:
            if os.path.exists(clone_dir): shutil.rmtree(clone_dir, onerror=_remove_readonly)
            os.makedirs(clone_dir)
            cmd = ["git", "clone", "--depth", "1", "-b", branch, auth_url, clone_dir]
            if subprocess.run(cmd, capture_output=True).returncode == 0:
                zips = glob.glob(os.path.join(clone_dir, "backup_*.zip"))
                if zips:
                    found_zip = sorted(zips)[-1]
                    break
        
        if not found_zip:
            return jsonify({"success": False, "message": "Nenhum backup encontrado no repositório."}), 404

        # Executar Restauração
        success, result = _internal_restore_logic(found_zip)
        
        if success:
            # Re-aplicar credenciais que funcionaram agora (importante se o backup tinha config antiga)
            final_cfg = get_config()
            final_cfg['github_repo'] = repo
            final_cfg['github_user'] = user
            final_cfg['github_token'] = token
            save_config(final_cfg)
            
            return jsonify({
                "success": True, 
                "message": "Nuvem restaurada com sucesso!",
                "stats": result,
                "file": os.path.basename(found_zip)
            })
        else:
            return jsonify({"success": False, "message": result}), 500

    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500
    finally:
        shutil.rmtree(clone_dir, onerror=_remove_readonly)


@app.route('/api/professores/rename', methods=['POST'])
def rename_professor():
    if not is_admin():
        return jsonify({"error": "Não autorizado"}), 403
    
    data = request.json
    prof_id = data.get('id')
    new_nome = data.get('nome')
    
    if not prof_id or not new_nome:
        return jsonify({"error": "Dados incompletos"}), 400

    from core.models import update_professores, update_usuarios
    
    def do_rename_prof(professores):
        found = False
        for p in professores:
            if p.get('id') == prof_id:
                p['nome'] = new_nome
                found = True
                break
        if not found:
            raise ValueError("Professor não encontrado")
        return professores

    def do_rename_user(usuarios):
        for u in usuarios:
            if u.get('professor_id') == prof_id:
                u['nome'] = new_nome
        return usuarios

    try:
        update_professores(do_rename_prof)
        update_usuarios(do_rename_user)
        return jsonify({"success": True})
    except ValueError as e:
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/turmas/rename', methods=['POST'])
def rename_turma():
    if not is_admin():
        return jsonify({"error": "Não autorizado"}), 403
    
    data = request.json
    turma_id = data.get('id')
    new_nome = data.get('turma')
    
    if not turma_id or not new_nome:
        return jsonify({"error": "Dados incompletos"}), 400

    from core.models import update_turmas
    
    def do_rename_turma(turmas):
        found = False
        for t in turmas:
            if t.get('id') == turma_id:
                t['turma'] = new_nome
                found = True
                break
        if not found:
            raise ValueError("Turma não encontrada")
        return turmas

    try:
        update_turmas(do_rename_turma)
        return jsonify({"success": True})
    except ValueError as e:
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/recursos/rename', methods=['POST'])
def rename_recurso():
    if not is_admin():
        return jsonify({"error": "Não autorizado"}), 403
    
    data = request.json
    recurso_id = data.get('id')
    new_nome = data.get('nome')
    
    if not recurso_id or not new_nome:
        return jsonify({"error": "Dados incompletos"}), 400

    from core.models import update_recursos
    
    def do_rename_recurso(recursos):
        found = False
        for r in recursos:
            if r.get('id') == recurso_id:
                r['nome'] = new_nome
                found = True
                break
        if not found:
            raise ValueError("Recurso não encontrado")
        return recursos

    try:
        update_recursos(do_rename_recurso)
        return jsonify({"success": True})
    except ValueError as e:
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# --- Agendamento de Backup Automático (APScheduler) ---
from apscheduler.schedulers.background import BackgroundScheduler
import atexit
import subprocess

# Inicializar Scheduler Globalmente
scheduler = BackgroundScheduler()

def daily_backup_job():
    """
    Executa backup no repositório satélite (.backups):
    1. Obtém dados DESCRIPTOGRAFADOS.
    2. Cria zip em diretório temporário e move para .backups.
    3. Configura git identity DENTRO de .backups.
    4. Commit e Push para o repo do cliente.
    """
    try:
        print("⏳ Iniciando backup automático (Satélite)...")
        
        cfg = get_config()
        github_repo = cfg.get('github_repo')
        github_user = cfg.get('github_user')
        github_token = cfg.get('github_token')
        
        backup_root = os.path.abspath('.backups')
        if not os.path.exists(backup_root):
            os.makedirs(backup_root)
            
        import tempfile
        import zipfile
        
        today_str = datetime.now().strftime('%Y-%m-%d_%H%M%S')
        temp_dir = tempfile.mkdtemp()
        try:
            # 1. Obter dados DESCRIPTOGRAFADOS
            db_data = get_full_database_decrypted()
            
            # 2. Criar estrutura temporária para o ZIP
            data_temp = os.path.join(temp_dir, 'data')
            os.makedirs(data_temp)
            
            for name, content in db_data.items():
                with open(os.path.join(data_temp, f"{name}.json"), 'w', encoding='utf-8') as f:
                    json.dump(content, f, indent=4, ensure_ascii=False)
            
            # Copiar arquivos não-JSON do DATA_DIR se existirem
            if os.path.exists(DATA_DIR):
                for item in os.listdir(DATA_DIR):
                    src = os.path.join(DATA_DIR, item)
                    if os.path.isfile(src) and not item.endswith('.json'):
                        shutil.copy2(src, os.path.join(data_temp, item))

            # Criar ZIP em .backups
            zip_path = os.path.join(backup_root, f"backup_{today_str}.zip")
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
                # Zipar a pasta data/ criada no temp
                for root, dirs, files in os.walk(data_temp):
                    for file in files:
                        full_p = os.path.join(root, file)
                        rel_p = os.path.relpath(full_p, temp_dir)
                        zf.write(full_p, rel_p)
                
                # Incluir .env como chave mestra
                from core.security import DOTENV_PATH as ENV_PATH
                if ENV_PATH and os.path.exists(ENV_PATH):
                    zf.write(ENV_PATH, '.env')

                # backup_info.json
                info = {'created_at': datetime.now().strftime('%d/%m/%Y %H:%M'), 'version': '2.0', 'type': 'decrypted'}
                zf.writestr('backup_info.json', json.dumps(info, indent=4))

        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

        print(f"✅ Backup local criado: backup_{today_str}.zip")

        status_msg = "Sucesso (Local)"
        tipo_log = "sistema"

        # 3. Git Automation
        if github_repo and github_user and github_token:
            try:
                clean_repo = github_repo.replace("https://", "").replace("http://", "")
                auth_url = f"https://{github_user}:{github_token}@{clean_repo}"
                
                # Sem check=True: captura stdout/stderr para diagnóstico real
                def run_git(args, raise_on_fail=False):
                    r = subprocess.run(
                        ["git"] + args, cwd=backup_root,
                        capture_output=True, text=True
                    )
                    if raise_on_fail and r.returncode != 0:
                        raise RuntimeError(r.stderr.strip() or r.stdout.strip() or f"git {args[0]} falhou (código {r.returncode})")
                    return r

                if not os.path.exists(os.path.join(backup_root, '.git')):
                    run_git(["init"])
                    run_git(["branch", "-M", "main"])
                
                # Identidade local
                run_git(["config", "user.name", "EduAgenda Backup"])
                run_git(["config", "user.email", "backup@eduagenda.local"])

                # Remote com token
                remotes = run_git(["remote"]).stdout
                if "origin" in remotes:
                    run_git(["remote", "set-url", "origin", auth_url])
                else:
                    run_git(["remote", "add", "origin", auth_url])

                # Pruning (90 dias)
                cutoff = datetime.now() - timedelta(days=90)
                for f in os.listdir(backup_root):
                    if f.endswith('.zip') and f.startswith('backup_'):
                        try:
                            d_str = f.split('_')[1]
                            f_date = datetime.strptime(d_str, "%Y-%m-%d")
                            if f_date < cutoff:
                                os.remove(os.path.join(backup_root, f))
                        except: pass

                run_git(["add", "."])
                status_result = run_git(["status", "--porcelain"])
                if status_result.stdout.strip():
                    run_git(["commit", "-m", f"Backup Auto: {today_str}"])

                    # Garante URL autenticada imediatamente antes do push
                    run_git(["remote", "set-url", "origin", auth_url])

                    # Tenta pull --rebase para evitar divergência antes de push
                    run_git(["pull", "--rebase", "origin", "main"])

                    push = run_git(["push", "-u", "origin", "main"])
                    if push.returncode != 0:
                        # Tenta branch master como fallback
                        push = run_git(["push", "-u", "origin", "master"])
                    
                    if push.returncode == 0:
                        status_msg = "Sucesso (Nuvem ☁️)"
                        print(f"✅ Push nuvem OK: backup_{today_str}.zip")
                    else:
                        err_detail = (push.stderr.strip().splitlines()[-1]
                                      if push.stderr.strip() else "erro desconhecido")
                        print(f"❌ Push falhou: {push.stderr.strip()}")
                        status_msg = f"Aviso (Erro Push: {err_detail[:40]})"
                        tipo_log = "alerta"
                else:
                    status_msg = "Sucesso (Sem alt. nuvem)"

            except Exception as e:
                print(f"⚠️ Erro Git Satélite: {e}")
                status_msg = f"Aviso (Erro Nuvem: {str(e)[:40]})"
                tipo_log = "alerta"
        else:
            status_msg = "Sucesso (Apenas Local)"

        # Registrar Log
        def log_backup(logs):
            logs.append({"usuario": "Sistema", "nome": "Backup Automático", "data": datetime.now().isoformat(), "tipo": tipo_log, "mensagem": f"Backup completo. Status: {status_msg}"})
            return logs[-1000:]
        update_logs(log_backup)

        def update_backup_status(cfg):
            cfg['last_backup_at'] = datetime.now().strftime('%d/%m/%Y %H:%M')
            cfg['last_backup_status'] = status_msg
            return cfg
        update_config(update_backup_status)

    except Exception as e:
        print(f"❌ Erro crítico backup job: {e}")
        try:
            def log_error(logs):
                logs.append({"usuario": "Sistema", "nome": "Backup Automático", "data": datetime.now().isoformat(), "tipo": "erro", "mensagem": f"Falha crítica no backup: {str(e)}"})
                return logs[-1000:]
            update_logs(log_error)
            
            def update_failure_status(cfg):
                cfg['last_backup_at'] = datetime.now().strftime('%d/%m/%Y %H:%M')
                cfg['last_backup_status'] = "Falha Crítica"
                return cfg
            update_config(update_failure_status)
        except: pass


@app.route('/api/config/github', methods=['GET', 'POST'])
def config_github_route():
    if not is_admin():
        return jsonify({"success": False, "message": "Acesso não autorizado"}), 403

    if request.method == 'GET':
        cfg = get_config()
        data = {
            "repo": cfg.get('github_repo', ''),
            "user": cfg.get('github_user', ''),
            "github_token": cfg.get('github_token', '') if is_root() else '',
            "project_repos": cfg.get('project_repos', []),
            "sync_history": cfg.get('project_sync_history', [])
        }
        if is_root():
            data["repo_proj"] = cfg.get('github_repo_proj', '')
            data["user_proj"] = cfg.get('github_user_proj', '')
            data["token_proj"] = cfg.get('github_token_proj', '')
            data["obs_proj"] = cfg.get('github_obs_proj', '')
        return jsonify(data)

    data = request.json
    action = data.get('action', 'save')
    
    # Repositório de Backup
    repo_backup = data.get('repo')
    user_backup = data.get('user')
    token_backup = data.get('token')
    
    # Repositório de Projeto
    repo_proj = data.get('repo_proj')
    user_proj = data.get('user_proj')
    token_proj = data.get('token_proj')
    obs_proj = data.get('obs_proj', '')

    cfg = get_config()

    # Resolver usuário do projeto (user_p) para uso em Teste e Salvamento
    user_p = user_proj if user_proj else cfg.get('github_user_proj')
    if not user_p and repo_proj and "github.com" in repo_proj:
        try:
            parts = repo_proj.split("github.com/")[1].split("/")
            user_p = parts[0]
        except: pass

    if action == 'test':
        results = []

        # --- Teste de Backup: ls-remote + push de teste ---
        if repo_backup and user_backup:
            tk = token_backup if token_backup else cfg.get('github_token')
            if tk:
                clean = repo_backup.replace("https://", "").replace("http://", "")
                auth_url = f"https://{user_backup}:{tk}@{clean}"

                # 1. Verificação rápida de conectividade
                ls = subprocess.run(
                    ["git", "ls-remote", auth_url, "HEAD"],
                    capture_output=True, text=True, timeout=10
                )
                if ls.returncode != 0:
                    results.append("Backup: Falha (sem acesso ao repositório)")
                else:
                    # 2. Push de teste real no diretório .backups
                    backup_root = os.path.abspath('.backups')
                    os.makedirs(backup_root, exist_ok=True)
                    try:
                        def run_git_test(args):
                            return subprocess.run(
                                ["git"] + args, cwd=backup_root,
                                capture_output=True, text=True, timeout=15
                            )

                        if not os.path.exists(os.path.join(backup_root, '.git')):
                            run_git_test(["init"])
                            try: run_git_test(["branch", "-M", "main"])
                            except: pass

                        run_git_test(["config", "user.name", "EduAgenda Backup"])
                        run_git_test(["config", "user.email", "backup@eduagenda.local"])

                        remotes = run_git_test(["remote"]).stdout
                        if "origin" in remotes:
                            run_git_test(["remote", "set-url", "origin", auth_url])
                        else:
                            run_git_test(["remote", "add", "origin", auth_url])

                        # Arquivo de teste (timestamp único)
                        test_file = os.path.join(backup_root, '.test_connection')
                        with open(test_file, 'w') as f:
                            f.write(f"Teste: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

                        run_git_test(["add", ".test_connection"])
                        run_git_test(["commit", "--allow-empty", "-m", "Teste de Conexão EduAgenda"])
                        run_git_test(["pull", "--rebase", "origin", "main"])
                        push = run_git_test(["push", "-u", "origin", "main"])

                        if push.returncode == 0:
                            results.append("Backup: OK ✅ (push bem-sucedido — backup automático habilitado)")
                        else:
                            err = (push.stderr.strip().splitlines()[-1]
                                   if push.stderr.strip() else "erro desconhecido")
                            results.append(f"Backup: Falha no push → {err}")
                    except Exception as e:
                        results.append(f"Backup: Falha → {str(e)}")

        # Testa Projeto (ls-remote simples)
        if repo_proj:
            tk = token_proj if token_proj else cfg.get('github_token_proj')
            if tk and user_p:
                clean = repo_proj.replace("https://", "").replace("http://", "")
                url = f"https://{user_p}:{tk}@{clean}"
                res = subprocess.run(["git", "ls-remote", url, "HEAD"],
                                     capture_output=True, text=True, timeout=10)
                results.append(f"Projeto: {'OK ✅' if res.returncode == 0 else 'Falha'}")

        ok = any("OK" in r for r in results)
        return jsonify({"success": ok, "message": " | ".join(results) if results else "Nenhum dado para testar"})


    elif action == 'save':
        def update_tokens(cfg):
            if repo_backup: cfg['github_repo'] = repo_backup
            if user_backup: cfg['github_user'] = user_backup
            if token_backup: cfg['github_token'] = token_backup
            
            if repo_proj:
                cfg['github_repo_proj'] = repo_proj
                cfg['github_user_proj'] = user_p # Usa o user resolvido ou fornecido
                cfg['github_token_proj'] = token_proj
                cfg['github_obs_proj'] = obs_proj
                
                # Gerenciar Histórico de Projetos
                repos = cfg.get('project_repos', [])
                # Procura se já existe
                exists = False
                for r in repos:
                    if r['url'] == repo_proj:
                        r['token'] = token_proj
                        r['obs'] = obs_proj
                        r['last_used'] = datetime.now().strftime("%d/%m/%Y %H:%M")
                        exists = True
                        break
                
                if not exists:
                    # Cores para o dashboard
                    colors = ['#38bdf8', '#10b981', '#fbbf24', '#f472b6', '#a78bfa', '#f87171']
                    color = colors[len(repos) % len(colors)]
                    repos.insert(0, {
                        "url": repo_proj,
                        "token": token_proj,
                        "obs": obs_proj,
                        "color": color,
                        "last_used": datetime.now().strftime("%d/%m/%Y %H:%M")
                    })
                
                # Limita histórico a 10 itens
                cfg['project_repos'] = repos[:10]
                
            return cfg

        from core.models import update_config
        update_config(update_tokens)
        return jsonify({"success": True})

@app.route('/api/config', methods=['POST'])
def save_config_route():
    if not is_admin():
        return jsonify({"success": False, "message": "Acesso não autorizado"}), 403
    try:
        data = request.json
        print(f"DEBUG CONFIG DATA RECEIVED: {data}")
        def update_general_config(current_config):
            current_config.update(data)
            return current_config

        from core.models import update_config
        update_config(update_general_config)
        
        with open("debug_log.txt", "a", encoding='utf-8') as f:
            f.write(f"SAVING CONFIG (ATOMIC): {data}\n")

        # Atualizar Agendamento se houver backup_time
        if 'backup_time' in data and scheduler.running:
            try:
                bt = data['backup_time'] # Formato "HH:MM"
                h, m = map(int, bt.split(':'))
                # Remove job antigo se existir e cria novo
                if scheduler.get_job('daily_backup'):
                    scheduler.remove_job('daily_backup')
                
                scheduler.add_job(
                    func=daily_backup_job, 
                    trigger="cron", 
                    hour=h, 
                    minute=m,
                    id='daily_backup',
                    replace_existing=True
                )
                print(f"⏰ Backup reagendado para: {bt}")
            except Exception as sch_e:
                print(f"Erro ao reagendar backup: {sch_e}")

        return jsonify({"success": True})
    except Exception as e:
        print(f"ERROR saving config: {str(e)}") # LOG NO TERMINAL
        return jsonify({"success": False, "message": str(e)}), 500

# Iniciar Agendador
if not app.debug or os.environ.get('WERKZEUG_RUN_MAIN') == 'true':
    # Evita rodar 2x no modo debug do Flask
    # Configuração inicial do job baseada no arquivo salvo ou default 00:00
    try:
        cfg = get_config()
        bt = cfg.get('backup_time', '00:00')
        h, m = map(int, bt.split(':'))
    except:
        h, m = 0, 0
    
    if not scheduler.get_job('daily_backup'):
        scheduler.add_job(
            func=daily_backup_job, 
            trigger="cron", 
            hour=h, 
            minute=m,
            id='daily_backup'
        )
    
    if not scheduler.running:
        scheduler.start()
        atexit.register(lambda: scheduler.shutdown())

@app.route('/api/admin/users', methods=['GET'])
def get_admin_users():
    if not is_admin():
        return jsonify({"success": False, "message": "Acesso não autorizado"}), 403
    
    usuarios = get_usuarios()
    # Retornar apenas dados necessários, sem o hash da senha
    users_data = []
    for u in usuarios:
        users_data.append({
            "username": u['username'],
            "nome": u['nome'],
            "role": u.get('role', 'professor'),
            "active": u.get('active', True)
        })
    return jsonify(users_data)

@app.route('/api/admin/reset-password', methods=['POST'])
def admin_reset_password():
    if not is_admin():
        return jsonify({"success": False, "message": "Acesso não autorizado"}), 403
    
    data = request.json
    target_username = data.get('username')
    if not target_username:
        return jsonify({"success": False, "message": "Usuário não especificado"}), 400
    
    # REGRAS DE SOBERANIA ROOT
    # 1. Admin comum NÃO PODE resetar o Root
    if target_username == 'root' and not is_root():
        return jsonify({"success": False, "message": "Apenas o Root pode gerenciar sua própria conta."}), 403
    
    def update_logic(usuarios):
        found_idx = next((i for i, u in enumerate(usuarios) if u['username'] == target_username), None)
        
        if found_idx is None:
            # Se for Root ou Admin e não estiver no JSON, o Root pode restaurá-los
            if is_root() and target_username in ['root', 'admin']:
                usuarios.append({
                    "username": target_username,
                    "nome": "Usuário Restaurado" if target_username == 'admin' else "Super Usuário (Root)",
                    "senha": generate_password_hash("@Senha123456"),
                    "role": target_username,
                    "active": True
                })
                return usuarios
            return None

        # Reset padrão para @Senha123456
        usuarios[found_idx]['senha'] = generate_password_hash("@Senha123456")
        return usuarios

    result = update_usuarios(update_logic)
    if result is None:
        return jsonify({"success": False, "message": "Usuário não encontrado"}), 404
        
    return jsonify({"success": True, "message": f"Senha de {target_username} resetada para o padrão (@Senha123456)."})

@app.route('/api/version')
def get_version():
    return jsonify(Updater.get_local_version())

@app.route('/api/update/check')
def check_update_endpoint():
    if not is_admin():
        return jsonify({"success": False, "message": "Acesso restrito à Administração."}), 403
    
    config = get_config()
    repo_url = config.get('github_repo_proj')
    token = config.get('github_token_proj')
    
    if not repo_url or not token:
        return jsonify({"success": False, "message": "Repositório de Projeto não configurado."})

    remote = Updater.check_remote_version(repo_url, token)
    if not remote:
        return jsonify({"success": False, "message": "Não foi possível verificar a versão remota (Verifique Token/Repo)."})
        
    local = Updater.get_local_version()
    
    # Simples comparação de string para vX.X.X
    has_update = remote['version'] != local['version']
    
    return jsonify({
        "success": True, 
        "has_update": has_update,
        "remote_version": remote['version'],
        "local_version": local['version']
    })

@app.route('/api/update/sync', methods=['POST'])
def sync_update_endpoint():
    if not is_root():
        return jsonify({"success": False, "message": "Acesso restrito ao Desenvolvedor (Root)."}), 403
        
    config = get_config()
    repo_url = config.get('github_repo_proj')
    token = config.get('github_token_proj')
    
    if not repo_url or not token:
        return jsonify({"success": False, "message": "Repositório de Projeto não configurado."})

    # Verifica se deve forçar o push
    force = request.json.get('force', False) if request.is_json else False
    
    success, message = Updater.sync_push(repo_url, token, force=force)
    
    # Registrar no histórico de sincronização
    try:
        def log_sync_event(cfg):
            history = cfg.get('project_sync_history', [])
            history.insert(0, {
                "timestamp": datetime.now().strftime("%d/%m/%Y %H:%M"),
                "repo": repo_url.split('/')[-1] if repo_url else "N/A",
                "success": success,
                "message": message,
                "type": "PUSH" if force else "SYNC",
                "version": Updater.get_local_version()['version']
            })
            cfg['project_sync_history'] = history[:15] # Mantém os últimos 15 logs
            return cfg
        
        from core.models import update_config
        update_config(log_sync_event)
    except Exception as e:
        print(f"Erro ao logar sincronismo: {e}")

    return jsonify({"success": success, "message": message})

@app.route('/api/update/install', methods=['POST'])
def install_update_endpoint():
    if not is_admin():
        return jsonify({"success": False, "message": "Acesso restrito à Administração."}), 403
        
    config = get_config()
    repo_url = config.get('github_repo_proj') or config.get('github_repo')
    token = config.get('github_token_proj') or config.get('github_token')
    
    success, message = Updater.install_update(repo_url, token)
    
    if success:
        message += " O sistema iniciará a atualização automaticamente quando estiver ocioso."
        
    return jsonify({"success": success, "message": message})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    # Se estivermos rodando via pythonw (segundo plano), usamos o Waitress
    if sys.executable.endswith('pythonw.exe'):
        from waitress import serve
        print(f"Iniciando Servidor de Produção (Waitress) na porta {port}...")
        serve(app, host='0.0.0.0', port=port)
    else:
        # Modo Debug normal para desenvolvimento
        app.run(host='0.0.0.0', port=port, debug=True)
