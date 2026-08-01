"""
Pacote logistica: cálculo de distâncias reais e roteirização de entregas
da Dunder Mifflin — primeira etapa de negócio implementada no projeto.

Este __init__.py reexporta as funções principais, para que quem for usar
o pacote possa importar diretamente de `src.logistica`, sem precisar
saber em qual arquivo interno cada função está definida:

    from src.logistica import atribui_armazem, calcular_melhor_rota

em vez de:

    from src.logistica.roteirizacao import atribui_armazem, calcular_melhor_rota
"""

from src.logistica.distancias import calcula_distancias, calcula_distancias_clientes
from src.logistica.roteirizacao import atribui_armazem, calcular_melhor_rota

__all__ = [
    "calcula_distancias",
    "calcula_distancias_clientes",
    "atribui_armazem",
    "calcular_melhor_rota",
]
