import pandas as pd
from .models import save_professores, save_turmas, get_professores, get_turmas

class ExcelService:
    @staticmethod
    def upload_professores(file_path):
        try:
            df = pd.read_excel(file_path)
            # Normalizar nomes de colunas para facilitar detecção
            df.columns = [str(c).strip().lower() for c in df.columns]
            
            # Detecção inteligente da coluna de nomes
            target_col = None
            for p in ['professores', 'professor', 'nome', 'docente']:
                if p in df.columns:
                    target_col = p
                    break
            
            if not target_col:
                target_col = df.columns[0] # Fallback para a primeira coluna
            
            novos_professores = df[target_col].dropna().apply(lambda x: str(x).strip()).unique().tolist()
            
            def merge_unique(existentes):
                todos = list(set(existentes + novos_professores))
                todos.sort()
                return todos
            
            from .models import update_professores
            update_professores(merge_unique)
            return True, f"{len(novos_professores)} professores processados."
        except Exception as e:
            return False, f"Erro ao processar professores: {str(e)}"

    @staticmethod
    def upload_turmas(file_path):
        try:
            df = pd.read_excel(file_path)
            # Normalizar colunas
            df.columns = [str(c).strip().lower() for c in df.columns]
            
            required = ['turma', 'turno']
            if not all(col in df.columns for col in required):
                return False, f"A planilha deve conter as colunas: {', '.join(required)}"
            
            # Limpar dados
            df['turma'] = df['turma'].astype(str).str.strip()
            df['turno'] = df['turno'].astype(str).str.strip().str.capitalize()
            
            novas_turmas = df[required].dropna().to_dict('records')
            
            def merge_turmas(existentes):
                ids_existentes = { (t['turma'], t['turno']) for t in existentes }
                para_adicionar = [t for t in novas_turmas if (t['turma'], t['turno']) not in ids_existentes]
                return existentes + para_adicionar
            
            from .models import update_turmas
            update_turmas(merge_turmas)
            return True, f"{len(novas_turmas)} turmas verificadas/adicionadas."
            return True, f"{len(novas_turmas)} turmas verificadas/adicionadas."
        except Exception as e:
            return False, f"Erro ao processar turmas: {str(e)}"

    @staticmethod
    def upload_recursos(file_path):
        try:
            df = pd.read_excel(file_path)
            df.columns = [str(c).strip().lower() for c in df.columns]
            
            # Validação de Colunas
            required = ['nome', 'tipo']
            if not all(col in df.columns for col in required):
                return False, f"A planilha deve conter as colunas: {', '.join(required)}"
            
            # Limpeza
            df['nome'] = df['nome'].astype(str).str.strip()
            df['tipo'] = df['tipo'].astype(str).str.strip().upper()
            
            novos_recursos = df[required].dropna().to_dict('records')
            
            # Validação BETA (Max 8 Recursos)
            from .models import get_recursos, save_recursos
            recursos_atuais = get_recursos()
            
            # Merge lógico (evitar duplicados por ID/Nome)
            # Como recursos não têm ID fixo na planilha, vamos criar IDs baseados no nome se não existirem
            # Mas primeiro, checar o limite total
            
            # ids existentes
            ids_existentes = {r['id'] for r in recursos_atuais}
            nomes_existentes = {r['nome'].lower() for r in recursos_atuais}
            
            adicionados = 0
            import uuid
            
            for r in novos_recursos:
                if r['nome'].lower() in nomes_existentes:
                    continue # Já existe
                
                # Checa limite antes de adicionar
                if len(recursos_atuais) >= 8:
                    return False, f"Limite da versão Beta atingido (Máx 8 Recursos). {adicionados} recursos foram adicionados antes da trava."
                
                novo_id = str(uuid.uuid4())[:8]
                recursos_atuais.append({
                    "id": novo_id,
                    "nome": r['nome'],
                    "tipo": r['tipo'],
                    "ativo": True
                })
                nomes_existentes.add(r['nome'].lower())
                adicionados += 1
            
            save_recursos(recursos_atuais)
            return True, f"{adicionados} recursos adicionados com sucesso."

        except Exception as e:
            return False, f"Erro ao processar recursos: {str(e)}"
