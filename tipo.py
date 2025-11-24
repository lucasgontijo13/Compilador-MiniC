# tipo.py
from enum import Enum
from ttoken import TOKEN

class Tipo(Enum):
    INT = 'int'
    FLOAT = 'float'
    CHAR = 'char'
    VOID = 'void'
    ERRO = 'erro' # Tipo para representar um erro de tipo
    ARRAY = 'array'

def token_para_tipo(token_val):
    if token_val == TOKEN.INT: return Tipo.INT
    if token_val == TOKEN.FLOAT: return Tipo.FLOAT
    if token_val == TOKEN.CHAR: return Tipo.CHAR
    return Tipo.ERRO

# Matriz de compatibilidade para operadores aritméticos (+, -, *, /)
# [tipo1][tipo2] -> tipo_resultado
compatibilidade_aritmetica = {
    Tipo.INT: {
        Tipo.INT: Tipo.INT,
        Tipo.FLOAT: Tipo.FLOAT,
        Tipo.CHAR: Tipo.INT,
    },
    Tipo.FLOAT: {
        Tipo.INT: Tipo.FLOAT,
        Tipo.FLOAT: Tipo.FLOAT,
        Tipo.CHAR: Tipo.FLOAT,
    },
    Tipo.CHAR: {
        Tipo.INT: Tipo.INT,
        Tipo.FLOAT: Tipo.FLOAT,
        Tipo.CHAR: Tipo.INT,
    }
}

# Regras para operadores relacionais (==, !=, <, >, <=, >=) e lógicos (&&, ||)
# Sempre resultam em INT (0 ou 1)
def checar_compatibilidade_relacional_logica(tipo1, tipo2):
    tipos_numericos = [Tipo.INT, Tipo.FLOAT, Tipo.CHAR]
    if tipo1 in tipos_numericos and tipo2 in tipos_numericos:
        return Tipo.INT
    return Tipo.ERRO

# Regras para atribuição (variável = expressão)
# É permitido atribuir T2 a T1? (T1 = T2)
def checar_compatibilidade_atribuicao(tipo_var, tipo_expr):
    if tipo_var == tipo_expr:
        return True
    # Permite int -> float, char -> float, char -> int
    if tipo_var == Tipo.FLOAT and (tipo_expr == Tipo.INT or tipo_expr == Tipo.CHAR):
        return True
    if tipo_var == Tipo.INT and tipo_expr == Tipo.CHAR:
        return True
    return False