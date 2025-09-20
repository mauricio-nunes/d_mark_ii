import requests
import os
import tempfile
import zipfile
from tqdm import tqdm
import csv
from ...core.utils import normalize_cnpj
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
            
            i_e, a_e, ig_e, err_e = self._cias_abertas(csv_cias_abertas,total_cias_abertas)
            i_f, a_f, ig_f, err_f = self._fundos(csv_fundos,total_fundos)
            
            self.empresas_repo.conn.commit()
            self.empresas_repo.conn.close()
            
            return i_e + i_f, a_e + a_f, ig_e + ig_f, err_e + err_f
        
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
                            # Extract and normalize data
                        cnpj = normalize_cnpj(row.get("CNPJ_CIA", ""))
                        if not cnpj:
                             errors += 1
                             pbar.update(1)
                             continue
                            
                        razao_social = row.get("DENOM_SOCIAL", "").strip()
                        if not razao_social:
                            errors += 1
                            pbar.update(1)
                            continue
                            
                        setor_atividade = row.get("SETOR_ATIV", "").strip() or None
                        situacao = row.get("SIT", "").strip() or None
                            
                        # Set ativo based on situacao
                        ativo = 1 if situacao == "ATIVO" else 0
                            
                        # Upsert company
                        was_inserted = self.empresas_repo.upsert_por_cnpj(
                            cnpj=cnpj,
                            razao_social=razao_social,
                            setor_atividade=setor_atividade,
                            tipo_empresa="CiaAberta",
                            situacao=ativo,
                        )

                        if was_inserted == 1:
                            inserido += 1
                        elif was_inserted == 2:
                            atualizado += 1
                        else:
                            ignorado += 1

                    except Exception as e:
                            erros += 1
                        
                    pbar.update(1)
            
        return inserido, atualizado, ignorado, erros
    
    def _fundos(self, csv_fundos,total_linhas) -> tuple[int, int, int, int]:

        inserido, atualizado, ignorado, erros = 0, 0, 0, 0
            # Process CSV file
        with open(csv_fundos, 'r', encoding='latin1') as f:
            reader = csv.DictReader(f, delimiter=';', quoting=csv.QUOTE_NONE, escapechar="\\")
                
            with tqdm(total=total_linhas, desc="Processando fundos", unit="fundos") as pbar:
                for row in reader:
                    try:
                            
                            # Extract and normalize data
                        cnpj = normalize_cnpj(row.get("CNPJ_Fundo", "").strip())
                        if not cnpj:
                             errors += 1
                             pbar.update(1)
                             continue
                         
                        if cnpj == "35864448000138": 
                            a =1
                            
                        razao_social = row.get("Denominacao_Social", "").strip()
                        if not razao_social:
                            errors += 1
                            pbar.update(1)
                            continue
                            
                        
                        situacao = row.get("Situacao", "").strip() or None
                        
                        tipo_fundo = row.get("Tipo_Fundo", "").strip() or None
                            
                        # Set ativo based on situacao
                        ativo = 1 if situacao == "Em Funcionamento Normal" else 0
                            
                        # Upsert company
                        was_inserted = self.empresas_repo.upsert_por_cnpj(
                            cnpj=cnpj,
                            razao_social=razao_social,
                            setor_atividade=tipo_fundo,
                            tipo_empresa="Fundo",
                            situacao=ativo,
                        )

                        if was_inserted == 1:
                            inserido += 1
                        elif was_inserted == 2:
                            atualizado += 1
                        else:
                            ignorado += 1

                    except Exception as e:
                            erros += 1
                        
                    pbar.update(1)
            
        return inserido, atualizado, ignorado, erros
            
       