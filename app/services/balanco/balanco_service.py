from ...db.repositories.balanco.balanco_repo import BalancoRepo
from ...db.repositories.empresas.empresa_repo import EmpresaRepo
from ...db.repositories.importacao.cia_aberta_fca_repo import CiaAbertaFcaRepo
from ...db.repositories.importacao.cia_aberta_itr_repo import CiaAbertaItrRepo
from ...core.xlsx import build_excel_balanco_dre_side_by_side

from typing import Tuple, Dict, List, Any
from ...core.utils import (
    normalize_cnpj,
    valid_cnpj,
    parse_date,
    parse_int,
    validate_url,
    get_utc_timestamp,
    parse_url,
    ValidationError,
)

class BalancoService:
    """Serviço de manipulação de indicadores financeiros."""

    def __init__(self):
        self.balanco_repo = BalancoRepo()
        self.empresa_repo = EmpresaRepo()
        self.fca_repo = CiaAbertaFcaRepo()
        self.itr_repo = CiaAbertaItrRepo()
    
    def _filtrar_contas_por_codigo(self, contas: List[Dict[str, Any]], codigo_conta: str) -> List[Dict[str, Any]]:
        return [conta for conta in contas if conta["codigo_conta"] == codigo_conta]
        
    def _calcular_indicadores(self, bpa: List[Dict[str, Any]], bpp: List[Dict[str, Any]], dre: List[Dict[str, Any]], cc: List[Dict[str, Any]], modo_analise: str) -> Dict[str, Any]:
        #Tratar os dados do  pegar os valores das contas necessárias '1','1.01','1.01.01','1.01.02'
        indicadores = []
        
        codigo_contas_bpa = ['1','1.01','1.01.01','1.01.02']
        for codigo in codigo_contas_bpa:
            contas_bpa = self._filtrar_contas_por_codigo(bpa, codigo)
            indicadores.extend(contas_bpa)

        codigo_contas_bpp = ['2','2.01','2.01.01']
        for codigo in codigo_contas_bpp:
            contas_bpp = self._filtrar_contas_por_codigo(bpp, codigo)
            indicadores.extend(contas_bpp)

        codigo_contas_dre = ['3.01','3.03','3.04.01','3.04.02','3.11']
        for codigo in codigo_contas_dre:
            contas_dre = self._filtrar_contas_por_codigo(dre, codigo)
            indicadores.extend(contas_dre)

        return indicadores

    def calcular_balanco_por_codigo(self, codigo: str, ano: int) -> Dict[str, Any]:
        
        empresa = self.empresa_repo.buscar_por_codigo(codigo)
        if empresa is None:
            raise ValidationError(f"Empresa com código {codigo} não encontrada")
        
        cnpj = empresa["cnpj"]
        tipo_dfp = "DF Individual" if empresa["tipo_dfp"] == "individual" else "DF Consolidado"
        # = "padrao" if empresa["modo_analise"] == None else empresa["modo_analise"]

        dres = self.balanco_repo.get_last_five_dres_by_cnpj(cnpj, tipo_dfp)
        dre_12m = self.balanco_repo.get_last_twelve_months_dres_by_cnpj(cnpj, tipo_dfp)
        
        bpps = self.balanco_repo.get_last_five_bpps_by_cnpj(cnpj, tipo_dfp)
        bpas = self.balanco_repo.get_last_five_bpas_by_cnpj(cnpj, tipo_dfp)
        last_bpa = self.balanco_repo.get_last_bpa_by_cnpj(cnpj, tipo_dfp)
        last_bpp = self.balanco_repo.get_last_bpp_by_cnpj(cnpj, tipo_dfp)
        
        build_excel_balanco_dre_side_by_side(
            dre_5y=dres,
            dre_12m=dre_12m,
            bpp_5y=bpps,
            bpa_5y=bpas,
            bpa=last_bpa,
            bpp=last_bpp,
            xlsx_path=f"balanco_dre_{codigo}_{ano}.xlsx",
            fill_missing_with_zero=True)
        
        
