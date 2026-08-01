"""
Pacote shared: entidades e utilitários compartilhados entre todas as
áreas do negócio da Dunder Mifflin (hoje: logística; no futuro: vendas,
qualidade, RH e contabilidade).

Este __init__.py reexporta as funções principais, para que outros
módulos possam importar diretamente de `src.shared`, sem precisar saber
em qual arquivo interno cada função está definida:

    from src.shared import montar_clientes, carrega_municipios

em vez de:

    from src.shared.entidades import montar_clientes
    from src.shared.municipios import carrega_municipios
"""

from src.shared.api_client import get_json, get_text, post_json
from src.shared.municipios import (
    carrega_municipios,
    carrega_lat_long,
    buscar_lat_long,
)
from src.shared.entidades import (
    montar_armazens,
    montar_produtos,
    montar_clientes,
    monta_funcionarios,
    montar_vendas,
)

__all__ = [
    "get_json",
    "get_text",
    "post_json",
    "carrega_municipios",
    "carrega_lat_long",
    "buscar_lat_long",
    "montar_armazens",
    "montar_produtos",
    "montar_clientes",
    "monta_funcionarios",
    "montar_vendas",
]