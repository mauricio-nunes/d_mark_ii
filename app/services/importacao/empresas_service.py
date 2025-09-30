import requests
import os
import tempfile
import zipfile
from tqdm import tqdm
import csv
from ...core.utils import normalize_cnpj,parse_date
from ...db.repositories.empresas_repo import EmpresasRepo as empresas_repo
from ...db.connection import get_conn
import sys


class ValidationError(Exception): ...

class EmpresasService:
    def __init__(self):
        self.conn = get_conn()
        self.empresas_repo = empresas_repo(self.conn)
    

    def download_fundos_cvm(self):
        
        url = f"https://dados.cvm.gov.br/dados/FI/CAD/DADOS/registro_fundo_classe.zip"
        
        # Create temp directory for download
        temp_dir = tempfile.mkdtemp()
        zip_path = os.path.join(temp_dir, f"registro_fundo_classe.zip")
        csv_path = os.path.join(temp_dir, f"registro_fundo.csv")
        
        try:
        # Download file
            response = requests.get(url, stream=True)
            response.raise_for_status()
        
            total_size = int(response.headers.get('content-length', 0))
            with open(zip_path, 'wb') as f:
                with tqdm(total=total_size, unit='B', unit_scale=True, desc="Baixando") as pbar:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                            pbar.update(len(chunk))
        
            # Extract CSV from ZIP
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                # Look for the expected CSV file
                expected_csv = f"registro_fundo.csv"
                if expected_csv not in zip_ref.namelist():
                    raise Exception(f"Arquivo {expected_csv} não encontrado no ZIP")
            
                zip_ref.extract(expected_csv, temp_dir)
        
            return csv_path
        
        except requests.RequestException as e:
            raise Exception(f"Erro ao baixar arquivo da CVM: {e}")
        except zipfile.BadZipFile:
            raise Exception("Arquivo ZIP corrompido")
        except Exception as e:
            raise Exception(f"Erro no processamento: {e}")
        
    def download_cias_abertas_cvm(self):
        
        url = "https://dados.cvm.gov.br/dados/CIA_ABERTA/CAD/DADOS/cad_cia_aberta.csv"
        
         # Create temp directory for download
        temp_dir = tempfile.mkdtemp()
        csv_path = os.path.join(temp_dir, f"cad_cia_aberta.csv")
        
        try:
        # Download file
            response = requests.get(url, stream=True)
            response.raise_for_status()
        
            total_size = int(response.headers.get('content-length', 0))
            with open(csv_path, 'wb') as f:
                with tqdm(total=total_size, unit='B', unit_scale=True, desc="Baixando") as pbar:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                            pbar.update(len(chunk))
        
        
            return csv_path
        
        except requests.RequestException as e:
            raise Exception(f"Erro ao baixar arquivo da CVM: {e}")
        except zipfile.BadZipFile:
            raise Exception("Arquivo ZIP corrompido")
        except Exception as e:
            raise Exception(f"Erro no processamento: {e}")
    

    def importar(self):
        # Download and extract file
        csv_cias_abertas = self.download_cias_abertas_cvm()
        csv_fundos = self.download_fundos_cvm()
        
        max_int = sys.maxsize
        while True:
            try:
                csv.field_size_limit(max_int)
                break
            except OverflowError:
                max_int = int(sys.maxsize / 10)
        
        try:
            
            # Count total rows for progress bar
            with open(csv_cias_abertas, 'r', encoding='latin1') as f:
                total_cias_abertas = sum(1 for _ in csv.DictReader(f, delimiter=';', quoting=csv.QUOTE_NONE, escapechar="\\")) - 1  # Subtract header
                
            with open(csv_fundos, 'r', encoding='latin1') as f:
                total_fundos = sum(1 for _ in csv.DictReader(f, delimiter=';', quoting=csv.QUOTE_NONE, escapechar="\\")) - 1  # Subtract header
                
                
            # Download and extract file
            # csv_cias_abertas = self.download_cias_abertas_cvm()
            # csv_fundos = self.download_fundos_cvm()
            
            i_e,  ig_e, err_e = self._cias_abertas(csv_cias_abertas,total_cias_abertas)
            i_f,  ig_f, err_f = self._fundos(csv_fundos,total_fundos)
            
            self.empresas_repo.conn.commit()
            self.empresas_repo.conn.close()
            
            return i_e + i_f, ig_e + ig_f, err_e + err_f
        
        finally:
            # Cleanup temp files
            try:
                if os.path.exists(csv_cias_abertas):
                    os.remove(csv_cias_abertas)
                if os.path.exists(os.path.dirname(csv_cias_abertas)):
                    os.rmdir(os.path.dirname(csv_cias_abertas))
                
                if os.path.exists(csv_fundos):
                    os.remove(csv_fundos)
                if os.path.exists(os.path.dirname(csv_fundos)):
                    os.rmdir(os.path.dirname(csv_fundos))
            except:
                pass  # Ignore cleanup errors
                    
    def _cias_abertas(self, csv_cias_abertas,total_linhas) -> tuple[int, int, int, int]:

        
        inserido, atualizado, ignorado, erros = 0, 0, 0, 0

            # Process CSV file
        with open(csv_cias_abertas, 'r', encoding='latin1') as f:
            reader = csv.DictReader(f, delimiter=';', quoting=csv.QUOTE_NONE, escapechar="\\")
                
            with tqdm(total=total_linhas, desc="Processando empresas", unit="empresas") as pbar:
                for row in reader:
                    try:
                        #FILTROS
                        if row.get("TP_MERC", "").strip() != "BOLSA":  # Skip non-listed companies
                            ignorado += 1
                            pbar.update(1)
                            continue
                            
                        
                        #CNPJ
                        cnpj = normalize_cnpj(row.get("CNPJ_CIA", ""))
                        if not cnpj:
                             erros += 1
                             pbar.update(1)
                             continue
                        
                        #RAZAO SOCIAL
                        razao_social = row.get("DENOM_SOCIAL", "").strip()
                        if not razao_social:
                            erros += 1
                            pbar.update(1)
                            continue
                        
                        # SETOR ATIVIDADE
                        setor_atividade = row.get("SETOR_ATIV", "").strip() or None
                        if setor_atividade == "":
                            setor_atividade = None
                        
                        #TIPO EMPRESA
                        tipo_empresa = "CiaAberta"
                        
                        # CODIGO CVM
                        codigo_cvm = row.get("CD_CVM", "").strip() or None
                        if codigo_cvm == "":
                            codigo_cvm = None
                        else:
                            codigo_cvm = int(codigo_cvm)

                        
                        # SITUACAO EMISSOR
                        situacao_emissor = row.get("SIT_EMISSOR", "").strip() or None
                        if situacao_emissor == "":
                            situacao_emissor = None
                        
                        # CONTROLE ACIONARIO
                        controle_acionario = row.get("CONTROLE_ACIONARIO", "").strip() or None
                        if controle_acionario == "":
                            controle_acionario = None
                        
                        
                        #DATA CONSTITUICAO
                        data_constituicao = row.get("DT_CONST", "").strip() or None
                        if data_constituicao == "":
                            data_constituicao = None
                        else:
                            data_constituicao = parse_date(data_constituicao)  # Valida formato
                        
                        #ATIVO
                        situacao = row.get("SIT", "").strip() or None
                        ativo = 1 if situacao == "ATIVO" else 0
                        
                      
                       
                            
                        # Upsert company
                        was_inserted = self.empresas_repo.upsert_por_cnpj(
                            cnpj=cnpj,
                            razao_social=razao_social,
                            setor_atividade=setor_atividade,
                            tipo_empresa=tipo_empresa,
                            codigo_cvm=codigo_cvm,
                            situacao_emissor=situacao_emissor,
                            controle_acionario=controle_acionario,
                            data_constituicao=data_constituicao,
                            ativo=ativo
                        )

                        if was_inserted > 1:
                            inserido += 1

                    except Exception as e:
                            erros += 1
                        
                    pbar.update(1)
            
        return inserido, ignorado, erros
    
    def _fundos(self, csv_fundos,total_linhas) -> tuple[int, int, int, int]:

        inserido, atualizado, ignorado, erros = 0, 0, 0, 0
            # Process CSV file
        with open(csv_fundos, 'r', encoding='latin1') as f:
            reader = csv.DictReader(f, delimiter=';', quoting=csv.QUOTE_NONE, escapechar="\\")
                
            with tqdm(total=total_linhas, desc="Processando fundos", unit="fundos") as pbar:
                for row in reader:
                    try:
                        
                        #FILTROS
                        if row.get("Tipo_Fundo", "").strip() != "FII":  # Skip all other funds
                            ignorado += 1
                            pbar.update(1)  
                            continue

                        # CNPJ
                        cnpj = normalize_cnpj(row.get("CNPJ_Fundo", "").strip())
                        if not cnpj:
                             erros += 1
                             pbar.update(1)
                             continue
                         
                        # RAZAO SOCIAL                            
                        razao_social = row.get("Denominacao_Social", "").strip()
                        if not razao_social:
                            erros += 1
                            pbar.update(1)
                            continue
                        
                        #SETOR ATIVIDADE
                        setor_atividade = None  # Não disponível no CSV de fundos
                        
                        #TIPO EMPRESA
                        tipo_empresa = "Fundo"
                        
                        #CODIGO CVM
                        codigo_cvm = row.get("Codigo_CVM", "").strip() or None
                        if codigo_cvm == "":
                            codigo_cvm = None
                        else:
                            codigo_cvm = int(codigo_cvm)
                        
                        #SITUACAO EMISSOR
                        situacao_emissor = row.get("Situacao", "").strip() or None
                        
                        #CONTROLE ACIONARIO
                        controle_acionario = None  # Não aplicável para fundos
                        
                        #DATA CONSTITUICAO
                        data_constituicao = row.get("Data_Constituicao", "").strip() or None
                        if data_constituicao == "":
                            data_constituicao = None
                        else:
                            data_constituicao = parse_date(data_constituicao)  # Valida formato
                            
                            
                        # Set ativo based on situacao
                        ativo = 0 if situacao_emissor == "Cancelado" else 1
                            
                        # Upsert company
                        was_inserted = self.empresas_repo.upsert_por_cnpj(
                            cnpj=cnpj,
                            razao_social=razao_social,
                            setor_atividade=setor_atividade,
                            tipo_empresa=tipo_empresa,
                            codigo_cvm=codigo_cvm,
                            situacao_emissor=situacao_emissor,
                            controle_acionario=controle_acionario,
                            data_constituicao=data_constituicao,
                            ativo=ativo,
                        )

                        if was_inserted > 1:
                            inserido += 1

                    except Exception as e:
                            erros += 1
                        
                    pbar.update(1)
            
        return inserido, ignorado, erros
            
       