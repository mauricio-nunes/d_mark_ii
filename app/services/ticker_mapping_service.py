from ..db.repositories import (ticker_mapping_repo)

def create_mapping(data: dict) -> int:
    """
    data: {ticker_antigo, ticker_novo, data_vigencia (YYYY-MM-DD)}
    """
    return ticker_mapping_repo.create(data)

def update_mapping(mid: int, data: dict) -> None:
    ticker_mapping_repo.update(mid, data)
    
def delete_mapping(mid: int) -> None:
    ticker_mapping_repo.delete(mid)

def list_mappings(offset: int = 0, limit: int = 100) -> list[dict]:
    return ticker_mapping_repo.list(offset, limit)

    