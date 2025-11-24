from ttoken import TOKEN


class Simbolo:
    def __init__(self, nome, tipo, categoria, info_extras=None):
        self.nome = nome
        # Tipo agora é uma tupla: (TOKEN.INT, False) ou (TOKEN.INT, True) p/ array
        self.tipo = tipo
        self.categoria = categoria  # 'variavel', 'funcao', 'parametro', 'array'
        self.info_extras = info_extras if info_extras is not None else {}

    def __str__(self):
        return f"Simbolo({self.nome}, {self.tipo}, {self.categoria})"


class TabelaDeSimbolos:
    def __init__(self):
        self.escopos = [{}]

    def entrar_escopo(self):
        self.escopos.append({})

    def sair_escopo(self):
        if len(self.escopos) > 1:
            self.escopos.pop()

    def adicionar(self, simbolo):
        escopo_atual = self.escopos[-1]
        if simbolo.nome in escopo_atual:
            return False
        escopo_atual[simbolo.nome] = simbolo
        return True

    def buscar(self, nome):
        for escopo in reversed(self.escopos):
            if nome in escopo:
                return escopo[nome]
        return None


# --- REGRAS DE TIPOS E COMPATIBILIDADE (Idêntico ao Gustavo) ---

# Dicionário de regras binárias
# Chave: frozenset({(T1, Arr1), Operador, (T2, Arr2)}) -> Valor: (TRes, ArrRes)
regras_operacoes_binarias = {}


def _add_regra(t1, arr1, op, t2, arr2, t_res, arr_res):
    chave = frozenset({(t1, arr1), op, (t2, arr2)})
    regras_operacoes_binarias[chave] = (t_res, arr_res)


# 1. Aritmética (+, -, *, /)
ops_aritmeticos = [TOKEN.mais, TOKEN.menos, TOKEN.multiplica, TOKEN.divide]
for op in ops_aritmeticos:
    # Int op Int = Int
    _add_regra(TOKEN.INT, False, op, TOKEN.INT, False, TOKEN.INT, False)
    # Float op Float = Float
    _add_regra(TOKEN.FLOAT, False, op, TOKEN.FLOAT, False, TOKEN.FLOAT, False)
    # Int op Float = Float
    _add_regra(TOKEN.INT, False, op, TOKEN.FLOAT, False, TOKEN.FLOAT, False)
    # Char op Char = Int
    _add_regra(TOKEN.CHAR, False, op, TOKEN.CHAR, False, TOKEN.INT, False)
    # Char op Int = Int
    _add_regra(TOKEN.CHAR, False, op, TOKEN.INT, False, TOKEN.INT, False)
    # Char op Float = Float
    _add_regra(TOKEN.CHAR, False, op, TOKEN.FLOAT, False, TOKEN.FLOAT, False)

# 2. Módulo (%) - Apenas Inteiros
_add_regra(TOKEN.INT, False, TOKEN.mod, TOKEN.INT, False, TOKEN.INT, False)
_add_regra(TOKEN.CHAR, False, TOKEN.mod, TOKEN.CHAR, False, TOKEN.INT, False)
_add_regra(TOKEN.INT, False, TOKEN.mod, TOKEN.CHAR, False, TOKEN.INT, False)

# 3. Relacionais e Lógicos - Retornam sempre INT
ops_logicos_rel = [TOKEN.opRel, TOKEN.AND, TOKEN.OR]
tipos_simples = [TOKEN.INT, TOKEN.FLOAT, TOKEN.CHAR]

for op in ops_logicos_rel:
    for t1 in tipos_simples:
        for t2 in tipos_simples:
            _add_regra(t1, False, op, t2, False, TOKEN.INT, False)


# --- FUNÇÕES AUXILIARES EXPOSTAS ---

def checar_operacao_binaria(t1, op, t2):
    """
    Verifica compatibilidade binária usando o dicionário.
    t1 e t2 são tuplas: (TOKEN, Boolean)
    """
    chave = frozenset({t1, op, t2})
    return regras_operacoes_binarias.get(chave, None)


def checar_operacao_unaria(op, t1):
    """
    Verifica operações unárias (-, !, +).
    """
    token_tipo, is_array = t1
    if is_array: return None  # Não faz sentido operar array direto

    if op == TOKEN.NOT:
        # ! só faz sentido com inteiros/booleanos, mas C aceita float (0.0 é false)
        return (TOKEN.INT, False)

    if op in [TOKEN.mais, TOKEN.menos]:
        if token_tipo in [TOKEN.INT, TOKEN.FLOAT, TOKEN.CHAR]:
            return t1  # Mantém o tipo

    return None


def checar_atribuicao(tipo_var, tipo_expr):
    """
    tipo_var e tipo_expr são tuplas (TOKEN, bool)
    """
    t_v, arr_v = tipo_var
    t_e, arr_e = tipo_expr

    # Regra crucial: Não se atribui a um array (v = ...)
    if arr_v: return False

    if t_v == t_e: return True

    # Coerções
    if t_v == TOKEN.FLOAT and t_e in [TOKEN.INT, TOKEN.CHAR]: return True
    if t_v == TOKEN.INT and t_e == TOKEN.CHAR: return True

    return False