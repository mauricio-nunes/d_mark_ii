from typing import List, Tuple
import os
import re
import glob
from tqdm import tqdm
import calendar
from ...core.xlsx import read_xlsx_rows
from ...core.utils import normalize_b3_decimal,parse_date

from ...db.connection import get_conn
from ...db.repositories.importacao.posicoes_consolidadas_repo import PosicoesConsolidadasRepo as posicoes_consolidadas_repo
from ...db.repositories.importacao.proventos_repo import ProventosRepo as proventos_repo
from ...db.repositories.eventos_repo import EventosRepo as eventos_repo

class ValidationError(Exception): ...

class PosicaoConsolidadaService:
    
    def __init__(self):
        self.conn = get_conn()
        self.posicao_consolidada_repo = posicoes_consolidadas_repo(self.conn)
        self.provento_repo = proventos_repo(self.conn)
        self.eventos_repo = eventos_repo(self.conn)

    
    def procurar_arquivos_posicao(self, imports_dir: str = "imports") -> list[str]:
        """Encontra arquivos de posição consolidada da B3 na pasta imports"""
        
        pattern = os.path.join(imports_dir, "relatorio-consolidado-mensal-*.xlsx")
        files = glob.glob(pattern)
    
        # Filtrar apenas arquivos com padrão válido
        valid_files = []
        for file in files:
            basename = os.path.basename(file)
            # Padrão: relatorio-consolidado-mensal-YYYY-{mes}.xlsx
            match = re.match(r'^relatorio-consolidado-mensal-(\d{4})-(janeiro|fevereiro|marco|abril|maio|junho|julho|agosto|setembro|outubro|novembro|dezembro)\.xlsx$', basename.lower())
            if match:
                valid_files.append(file)
        
        # Ordenar por mtime (mais recente primeiro) e limitar a 10
        valid_files.sort(key=lambda x: os.path.getmtime(x), reverse=True)
        return valid_files[:10]

    def data_referencia_arquivo(self, filename: str) -> str:
        """Extrai a data de referência do nome do arquivo"""

        meses_map = {
            'janeiro': 1, 'fevereiro': 2, 'marco': 3, 'abril': 4,
            'maio': 5, 'junho': 6, 'julho': 7, 'agosto': 8,
            'setembro': 9, 'outubro': 10, 'novembro': 11, 'dezembro': 12
        }
        
        basename = os.path.basename(filename).lower()
        match = re.match(r'^relatorio-consolidado-mensal-(\d{4})-(janeiro|fevereiro|marco|abril|maio|junho|julho|agosto|setembro|outubro|novembro|dezembro)\.xlsx$', basename)
        
        if not match:
            raise ValidationError(f"Nome de arquivo inválido: {filename}")
        
        ano = int(match.group(1))
        mes_nome = match.group(2)
        mes = meses_map[mes_nome]
        
        # Último dia do mês (fevereiro sempre 28 conforme requisito)
        if mes == 2:
            ultimo_dia = 28
        else:
            ultimo_dia = calendar.monthrange(ano, mes)[1]
        
        return f"{ano:04d}-{mes:02d}-{ultimo_dia:02d}"

    def _read_posicao_file(self, path: str, sheet_target: str) -> List[dict]:
        
        if sheet_target == "Posição - Ações":
            expected_columns = [
                'Instituição', 'Conta', 'CNPJ da Empresa', 'Código de Negociação',
                'Quantidade Disponível', 'Quantidade Indisponível', 'Preço de Fechamento', 'Valor Atualizado'
            ]
        
        if sheet_target == "Posição - Fundos":
            expected_columns = [
                'Instituição', 'Conta', 'CNPJ do Fundo', 'Código de Negociação',
                'Quantidade Disponível', 'Quantidade Indisponível', 'Preço de Fechamento', 'Valor Atualizado'
            ]
            
        if sheet_target == "Posição - Tesouro Direto":
            expected_columns = [
                'Instituição', 'Produto', 'Quantidade Disponível', 'Quantidade Indisponível', 'Valor Atualizado', 
                'Valor líquido', 'Valor Aplicado', 'Valor bruto'	]
        
        if sheet_target =='Posição - Renda Fixa':
            expected_columns = ['Produto', 'Instituição', 'Emissor', 'Código', 'Indexador', 'Tipo de regime', 'Data de Emissão', 
                                'Vencimento', 'Quantidade', 'Quantidade Disponível', 'Quantidade Indisponível', 'Motivo', 
                                'Contraparte', 'Preço Atualizado MTM', 'Valor Atualizado MTM', 'Preço Atualizado CURVA', 'Valor Atualizado CURVA']

            
        if sheet_target == "Proventos Recebidos":
            expected_columns = [ 'Produto','Pagamento','Tipo de Evento','Instituição','Quantidade','Preço unitário','Valor líquido']
        
        rows = read_xlsx_rows(path, sheet_target)
        
        #Verificar cabeçalhos (primeira linha não vazia)
        if not rows:
            raise ValidationError("Aba '{sheet_target}' não contém dados")
        
        first_row = rows[0] if rows else {}
        missing_columns = [col for col in expected_columns if col not in first_row]
        
        if missing_columns:
            raise ValidationError(f"Colunas faltantes: {', '.join(missing_columns)}")
        
        return rows
            
    def importar_posicao(self, path: str, data_ref: str, sheet_names: list) -> Tuple[int, int, int]:
        """
        Importa posição consolidada da B3.
        Returns (inseridas, removidas, erros)
        """
        processed_data = []
        processed_data_proventos = []
        

        eventos_corretoras = self.eventos_repo.listar_eventos_por_tipo('corretora')
        eventos_tickers = self.eventos_repo.listar_eventos_por_tipo('ativo')
        corretoras = [{k: v for k, v in d.items() if k in ['nome', 'entidade_id']} for d in eventos_corretoras]
        tickers = [{k: v for k, v in d.items() if k in ['ticker_novo', 'entidade_id']} for d in eventos_tickers]
        

        # Process sheets and collect data
        for sheet in sheet_names:
            if sheet in ["Posição - Ações", "Posição - Fundos", "Posição - Tesouro Direto", "Posição - Renda Fixa"]:
                rows = self._read_posicao_file(path, sheet)
                tipo_ativo = sheet.split('-')[1].strip().lower()
                for row in rows:
                    produto = str(row.get('Produto', '')).strip()
                    if not produto or produto == 'None' :
                        continue
                    
                    

                    # Extract and normalize fields
                    data = {
                        'data_referencia': data_ref,
                        'produto': produto,
                        'instituicao': str(row.get('Instituição', '')).strip(),
                        'conta': str(row.get('Conta', '')).strip(),
                        'ativo_id': 0,
                        'corretora_id': 0,
                        'codigo_negociacao': str(row.get('Código de Negociação', '')).strip(),
                        'cnpj_empresa': str(row.get('CNPJ da Empresa', '')).strip(),
                        'codigo_isin': str(row.get('Código ISIN / Distribuição', '')).strip(),
                        'tipo_indexador': str(row.get('Tipo', '')).strip(),
                        'adm_escriturador_emissor': str(row.get('Escriturador', '')),
                        'quantidade': normalize_b3_decimal(row.get('Quantidade', 0)),
                        'quantidade_disponivel': normalize_b3_decimal(row.get('Quantidade Disponível', 0)),
                        'quantidade_indisponivel': normalize_b3_decimal(row.get('Quantidade Indisponível', 0)),
                        'motivo': str(row.get('Motivo', '')).strip(),
                        'preco_fechamento': normalize_b3_decimal(row.get('Preço de Fechamento', 0)),
                        'data_vencimento': parse_date(row.get('Vencimento', '').strip()),
                        'valor_aplicado': normalize_b3_decimal(row.get('Valor Aplicado', 0)),
                        'valor_liquido': normalize_b3_decimal(row.get('Valor líquido', 0)),
                        'valor_atualizado': normalize_b3_decimal(row.get('Valor Atualizado', 0)),
                        'tipo_ativo': tipo_ativo,
                        'tipo_regime': str(row.get('Tipo de Regime', '')).strip(),
                        'data_emissao': parse_date(row.get('Data de Emissão', '').strip()),
                        'contraparte': str(row.get('Contraparte', '')).strip(),
                        'preco_atualizado_mtm': normalize_b3_decimal(row.get('Preço Atualizado MTM', 0)),
                        'valor_atualizado_mtm': normalize_b3_decimal(row.get('Valor Atualizado MTM', 0)),
                    }

                    # Adjust fields for specific types
                    if tipo_ativo == 'fundos':
                        data['adm_escriturador_emissor'] = str(row.get('Administrador', ''))
                        data['cnpj_empresa'] = str(row.get('CNPJ do Fundo', '')).strip()
                    elif tipo_ativo == 'tesouro direto':
                        data['codigo_negociacao'] = produto.replace("Tesouro", "").strip()
                        data['codigo_isin'] = str(row.get('Código ISIN', '')).strip()
                        data['tipo_indexador'] = str(row.get('Indexador', ''))
                    elif tipo_ativo == 'renda fixa':
                        data['codigo_negociacao'] = produto.split()[0]
                        data['codigo_isin'] = str(row.get('Código', '')).strip()
                        data['tipo_indexador'] = str(row.get('Indexador', ''))
                        data['adm_escriturador_emissor'] = str(row.get('Emissor', ''))
                        data['preco_fechamento'] = normalize_b3_decimal(row.get('Preço Atualizado CURVA', 0))
                        data['valor_atualizado'] = row.get('Valor Atualizado CURVA', 0)
                        
                        
            
                     
                    ticker_id = next(
                                (d["entidade_id"] for d in tickers if d["ticker_novo"] == data['codigo_negociacao']),None)
                    if ticker_id is None :
                        raise ValidationError(f"Código de negociação {data['codigo_negociacao']} não encontrado em eventos do tipo 'ativo'.")
                    data['ativo_id'] = ticker_id
                    
                    corretora_id = next(
                                (d["entidade_id"] for d in corretoras if d["nome"].lower() == data['instituicao'].lower()),None)
                    if corretora_id is None :
                        raise ValidationError(f"Instituição {data['instituicao']} não encontrada em eventos do tipo 'corretora'.")
                    data['corretora_id'] = corretora_id
                    

                    processed_data.append(data)

            elif sheet == "Proventos Recebidos":
                rows = self._read_posicao_file(path, sheet)
                for row in rows:
                    produto = str(row.get('Produto', '')).strip()
                    if not produto or produto == 'None':
                        continue
                    
                    
                    
                    
                    data_proventos = {
                        'data_referencia': data_ref,
                        'ticker': produto.split('-')[0].strip().upper(),
                        'ativo_id': 0,
                        'corretora_id': 0,
                        'descricao': produto,
                        'data_pagamento': parse_date(str(row.get('Pagamento', '')).strip()),
                        'tipo_evento': str(row.get('Tipo de Evento', '')).strip(),
                        'instituicao': str(row.get('Instituição', '')).strip(),
                        'quantidade': str(row.get('Quantidade', 0)).replace('.', ''),
                        'preco_unitario': normalize_b3_decimal(row.get('Preço unitário', 0)),
                        'valor_total': normalize_b3_decimal(row.get('Valor líquido', 0)),
                        'observacoes': str(row.get('Observações', '')).strip()
                        
                    }
                    
                    ticker_id = next(
                                (d["entidade_id"] for d in tickers if d["ticker_novo"] == data_proventos['ticker']),None)
                    if ticker_id is None :
                        raise ValidationError(f"Código de negociação {data_proventos['ticker']} não encontrado em eventos do tipo 'ativo'.")
                    data_proventos['ativo_id'] = ticker_id
                    
                    corretora_id = next(
                                (d["entidade_id"] for d in corretoras if d["nome"].lower() == data_proventos['instituicao'].lower()),None)
                    if corretora_id is None :
                        raise ValidationError(f"Instituição {data_proventos['instituicao']} não encontrada em eventos do tipo 'corretora'.")
                    data_proventos['corretora_id'] = corretora_id
                    


                    processed_data_proventos.append(data_proventos)




        
        inseridas = 0
        erros = 0
        removidas_posicao = 0
        removidas_proventos = 0

        try:
            self.conn.execute("BEGIN TRANSACTION;")
            # Remove old data for the same competencia
            removidas_posicao = self.posicao_consolidada_repo.excluir_por_competencia(data_ref)
            removidas_proventos = self.provento_repo.excluir_por_competencia(data_ref)

            # Insert new consolidated positions
            for row_data in tqdm(processed_data, desc="Importando posições"):
                try:
                    self.posicao_consolidada_repo.criar(row_data)
                    inseridas += 1
                except Exception as e:
                    erros += 1
                    print(f"Erro ao processar linha: {e}")

            # Insert new proventos
            for row_data in tqdm(processed_data_proventos, desc="Importando Proventos"):
                try:
                    self.provento_repo.criar(row_data)
                    inseridas += 1
                except Exception as e:
                    erros += 1
                    print(f"Erro ao processar linha: {e}")

            self.conn.commit()
            
        except Exception as e:
            self.conn.rollback()
            raise ValidationError(f"Erro na importação: {e}")
        finally:
            # Mover arquivo para processed
            self._move_to_processed(path)
            self.conn.close()

        return inseridas, removidas_posicao + removidas_proventos, erros

    def _move_to_processed(self, file_path: str):
        """Move arquivo processado para imports/processed"""
        import shutil
        
        processed_dir = os.path.join(os.path.dirname(file_path), "processed")
        os.makedirs(processed_dir, exist_ok=True)
        
        filename = os.path.basename(file_path)
        destination = os.path.join(processed_dir, filename)
        
        # Resolver colisão de nome se necessário
        if os.path.exists(destination):
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            name, ext = os.path.splitext(filename)
            filename = f"{name}_{timestamp}{ext}"
            destination = os.path.join(processed_dir, filename)
        
        shutil.move(file_path, destination)

    def validar_competencia(self, data_referencia: str):
        records_posicao = self.posicao_consolidada_repo.existe_por_competencia(data_referencia)
        records_proventos = self.provento_repo.existe_por_competencia(data_referencia)
        if records_posicao or records_proventos:
            return True
        return False