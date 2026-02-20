import pandas as pd
from .models import save_professores, save_turmas, get_professores, get_turmas

class ExcelService:
    @staticmethod
    def upload_professores(file_path):
        try:
            df = pd.read_excel(file_path, engine='openpyxl')
            df.columns = [str(c).strip().lower() for c in df.columns]
            
            target_col = None
            for p in ['professores', 'professor', 'nome', 'docente']:
                if p in df.columns:
                    target_col = p
                    break
            
            if not target_col:
                target_col = df.columns[0]
            
            nomes_novos = df[target_col].dropna().apply(lambda x: str(x).strip()).unique().tolist()
            
            import uuid
            def merge_unique(existentes):
                # existentes agora é a lista de objetos {"id": "...", "nome": "..."}
                nomes_atuais = {p['nome'].lower(): p for p in existentes}
                
                for nome in nomes_novos:
                    if nome.lower() not in nomes_atuais:
                        existentes.append({
                            "id": str(uuid.uuid4())[:8],
                            "nome": nome
                        })
                
                existentes.sort(key=lambda x: x['nome'])
                return existentes
            
            from .models import update_professores
            update_professores(merge_unique)
            return True, f"{len(nomes_novos)} professores processados."
        except Exception as e:
            return False, f"Erro ao processar professores: {str(e)}"

    @staticmethod
    def upload_turmas(file_path):
        try:
            df = pd.read_excel(file_path, engine='openpyxl')
            df.columns = [str(c).strip().lower() for c in df.columns]
            
            required = ['turma', 'turno']
            if not all(col in df.columns for col in required):
                return False, f"A planilha deve conter as colunas: {', '.join(required)}"
            
            df['turma'] = df['turma'].astype(str).str.strip()
            df['turno'] = df['turno'].astype(str).str.strip().str.capitalize()
            
            novas_turmas_raw = df[required].dropna().to_dict('records')
            
            import uuid
            def merge_turmas(existentes):
                # existentes agora é lista de {"id", "turma", "turno"}
                chaves_atuais = { (t['turma'].lower(), t['turno'].lower()): t for t in existentes }
                
                for nt in novas_turmas_raw:
                    chave = (nt['turma'].lower(), nt['turno'].lower())
                    if chave not in chaves_atuais:
                        existentes.append({
                            "id": str(uuid.uuid4())[:8],
                            "turma": nt['turma'],
                            "turno": nt['turno']
                        })
                return existentes
            
            from .models import update_turmas
            update_turmas(merge_turmas)
            return True, f"{len(novas_turmas_raw)} turmas verificadas/adicionadas."
        except Exception as e:
            return False, f"Erro ao processar turmas: {str(e)}"

    @staticmethod
    def upload_recursos(file_path):
        """
        Lê planilha de recursos e realiza o merge atômico com os atuais,
        respeitando o limite da versão Beta.
        """
        try:
            # 1. Carregar Dados do Excel
            df = pd.read_excel(file_path, engine='openpyxl')
            df.columns = [str(c).strip().lower() for c in df.columns]
            
            # Validação de Colunas
            required = ['nome', 'tipo']
            if not all(col in df.columns for col in required):
                return False, f"A planilha deve conter as colunas: {', '.join(required)}"
            
            # Limpeza e Preparação
            df['nome'] = df['nome'].astype(str).str.strip()
            df['tipo'] = df['tipo'].astype(str).str.strip().str.upper()
            novos_dados = df[required].dropna().to_dict('records')

            if not novos_dados:
                return False, "Nenhum recurso válido encontrado na planilha."

            from .models import get_recursos, save_recursos
            import uuid

            # 2. Operação Atômica de Merge
            # Nota: save_recursos agora usa DataManager.update internamente,
            # então precisamos carregar primeiro para validar regras de negócio
            # antes de disparar o update, ou fazer tudo dentro do callback.
            
            # Vamos usar uma abordagem de "preparação + salvamento atômico"
            recursos_atuais = get_recursos()
            nomes_existentes = {r['nome'].lower() for r in recursos_atuais}
            
            adicionados = 0
            recursos_para_adicionar = []

            for r in novos_dados:
                if r['nome'].lower() in nomes_existentes:
                    continue
                
                if (len(recursos_atuais) + adicionados) >= 8:
                    break
                
                novo_id = str(uuid.uuid4())[:8]
                recursos_para_adicionar.append({
                    "id": novo_id,
                    "nome": r['nome'],
                    "tipo": r['tipo'],
                    "ativo": True
                })
                adicionados += 1

            if adicionados > 0:
                # Atualiza a lista completa e salva atomicamente
                recursos_finais = recursos_atuais + recursos_para_adicionar
                save_recursos(recursos_finais)
                return True, f"{adicionados} recursos novos adicionados com sucesso."
            else:
                return True, "Nenhum recurso novo para adicionar (já existentes ou limite atingido)."

        except Exception as e:
            print(f"Erro em upload_recursos: {e}")
            import traceback
            traceback.print_exc()
            return False, f"Erro ao processar recursos: {str(e)}"
