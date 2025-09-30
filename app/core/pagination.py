import os
from typing import Callable, List, Any, Optional
from colorama import Fore, Style
from tabulate import tabulate

PAGE_SIZE = int(os.getenv("DMARKI_PAGE_SIZE", "20"))

class Paginator:
    def __init__(self, total: int, page_size: int = PAGE_SIZE):
        self.total = total
        self.page_size = page_size
        self.pages = max(1, (total + page_size - 1) // page_size)
        self.page = 1

    def range(self):
        start = (self.page - 1) * self.page_size
        end = start + self.page_size
        return start, end

    def next(self):
        if self.page < self.pages: self.page += 1

    def prev(self):
        if self.page > 1: self.page -= 1

    def goto(self, p: int):
        if 1 <= p <= self.pages: self.page = p


def paginate(fetch_func: Callable[[int, int], List[Any]], 
             count_func: Callable[[], int],
             render_func: Callable[[Any, int], List[Any]], 
             headers: List[str], 
             title: str = "Listagem",
             items_per_page: int = PAGE_SIZE) -> Optional[Any]:
    """
    Sistema de paginação genérico para listagens
    
    Args:
        fetch_func: Função que busca dados (limit, offset) -> List[items]
        count_func: Função que conta total de items () -> int  
        render_func: Função que renderiza um item (item, index) -> List[values]
        headers: Cabeçalhos da tabela
        title: Título da listagem
        items_per_page: Items por página
    
    Returns:
        Item selecionado ou None se cancelou
    """
    from ..ui.widgets import title as show_title, divider
    from ..core.utils import clear_screen
    
    def _input(prompt: str) -> str:
        return input(Fore.WHITE + prompt + Style.RESET_ALL)
    
    total = count_func()
    
    if total == 0:
        clear_screen()
        show_title(title)
        print(f"{Fore.YELLOW}Nenhum registro encontrado.{Style.RESET_ALL}")
        return None
    
    paginator = Paginator(total, items_per_page)
    
    while True:
        clear_screen()
        show_title(title)
        
        # Buscar dados da página atual
        start, end = paginator.range()
        items = fetch_func(paginator.page_size, start)
        
        if not items:
            print(f"{Fore.YELLOW}Nenhum registro na página atual.{Style.RESET_ALL}")
            return None
        
        # Renderizar tabela
        table_data = []
        for i, item in enumerate(items):
            row = render_func(item, i)
            table_data.append(row)
        
        print(tabulate(table_data, headers=headers, tablefmt="fancy_grid"))
        print()
        
        # Informações de paginação
        print(f"Página {paginator.page} de {paginator.pages} | Total: {total:,} registros")
        print()
        divider()
        
        # Opções de navegação
        opcoes = []
        if paginator.page > 1:
            opcoes.append("A - Página anterior")
        if paginator.page < paginator.pages:
            opcoes.append("P - Próxima página")
        
        opcoes.extend([
            "ID - Selecionar por ID",
            "V - Voltar"
        ])
        
        for opcao in opcoes:
            print(opcao)
        print()
        
        escolha = _input("Escolha uma opção: ").strip().lower()
        
        if escolha == 'a' and paginator.page > 1:
            paginator.prev()
        elif escolha == 'p' and paginator.page < paginator.pages:
            paginator.next()
        elif escolha == 'v' or escolha == 'voltar':
            return None
        elif escolha.isdigit():
            # Seleção por ID
            id_selecionado = int(escolha)
            item_selecionado = next((item for item in items if item.get('id') == id_selecionado), None)
            
            if item_selecionado:
                return item_selecionado
            else:
                print(f"{Fore.RED}ID {id_selecionado} não encontrado na página atual.{Style.RESET_ALL}")
                input("Pressione Enter para continuar...")
        else:
            print(f"{Fore.RED}Opção inválida.{Style.RESET_ALL}")
            input("Pressione Enter para continuar...")
