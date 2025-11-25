# tabela_de_simbolos.py

from ttoken import TOKEN


class Simbolo:
    def __init__(self, nome, tipo, categoria, info_extras=None):
        self.nome = nome
        self.tipo = tipo
        self.categoria = categoria  # 'variavel', 'funcao', 'parametro', 'array'
        self.info_extras = info_extras if info_extras is not None else {}

    def __str__(self):
        return f"Simbolo({self.nome}, {self.tipo}, {self.categoria})"


class TabelaDeSimbolos:
    def __init__(self):
        self.escopos = [{}]
        # Carrega as funções com os nomes exatos do arquivo bolha.txt
        self._inicializar_stdlib()

    def _inicializar_stdlib(self):
        """
        Insere as funções nativas compatíveis com o formato 'putstr', 'getint', etc.
        """

        # --- INPUT (Entrada) ---

        # int getint()
        self.adicionar(Simbolo('getint', (TOKEN.INT, False), 'funcao', {'params': []}))

        # float getfloat() (Adicionei por precaução)
        self.adicionar(Simbolo('getfloat', (TOKEN.FLOAT, False), 'funcao', {'params': []}))

        # char getchar() (Adicionei por precaução)
        self.adicionar(Simbolo('getchar', (TOKEN.CHAR, False), 'funcao', {'params': []}))

        # --- OUTPUT (Saída) ---

        # int putint(int x)
        self.adicionar(Simbolo('putint', (TOKEN.INT, False), 'funcao',
                               {'params': [(TOKEN.INT, False)]}))

        # int putfloat(float x)
        self.adicionar(Simbolo('putfloat', (TOKEN.INT, False), 'funcao',
                               {'params': [(TOKEN.FLOAT, False)]}))

        # int putchar(char c)
        self.adicionar(Simbolo('putchar', (TOKEN.INT, False), 'funcao',
                               {'params': [(TOKEN.CHAR, False)]}))

        # int putstr(char s[])
        self.adicionar(Simbolo('putstr', (TOKEN.INT, False), 'funcao',
                               {'params': [(TOKEN.CHAR, True)]}))

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


# --- Mantenha o restante do arquivo (regras de tipos) exatamente igual ---
regras_operacoes_binarias = {}


def _add_regra(t1, arr1, op, t2, arr2, t_res, arr_res):
    chave = frozenset({(t1, arr1), op, (t2, arr2)})
    regras_operacoes_binarias[chave] = (t_res, arr_res)


# 1. Aritmética
ops_aritmeticos = [TOKEN.mais, TOKEN.menos, TOKEN.multiplica, TOKEN.divide]
for op in ops_aritmeticos:
    _add_regra(TOKEN.INT, False, op, TOKEN.INT, False, TOKEN.INT, False)
    _add_regra(TOKEN.FLOAT, False, op, TOKEN.FLOAT, False, TOKEN.FLOAT, False)
    _add_regra(TOKEN.INT, False, op, TOKEN.FLOAT, False, TOKEN.FLOAT, False)
    _add_regra(TOKEN.CHAR, False, op, TOKEN.CHAR, False, TOKEN.INT, False)
    _add_regra(TOKEN.CHAR, False, op, TOKEN.INT, False, TOKEN.INT, False)
    _add_regra(TOKEN.CHAR, False, op, TOKEN.FLOAT, False, TOKEN.FLOAT, False)

# 2. Módulo (%)
_add_regra(TOKEN.INT, False, TOKEN.mod, TOKEN.INT, False, TOKEN.INT, False)
_add_regra(TOKEN.CHAR, False, TOKEN.mod, TOKEN.CHAR, False, TOKEN.INT, False)
_add_regra(TOKEN.INT, False, TOKEN.mod, TOKEN.CHAR, False, TOKEN.INT, False)

# 3. Relacionais e Lógicos
ops_logicos_rel = [TOKEN.opRel, TOKEN.AND, TOKEN.OR]
tipos_simples = [TOKEN.INT, TOKEN.FLOAT, TOKEN.CHAR]

for op in ops_logicos_rel:
    for t1 in tipos_simples:
        for t2 in tipos_simples:
            _add_regra(t1, False, op, t2, False, TOKEN.INT, False)


def checar_operacao_binaria(t1, op, t2):
    chave = frozenset({t1, op, t2})
    return regras_operacoes_binarias.get(chave, None)


def checar_operacao_unaria(op, t1):
    token_tipo, is_array = t1
    if is_array: return None
    if op == TOKEN.NOT:
        return (TOKEN.INT, False)
    if op in [TOKEN.mais, TOKEN.menos]:
        if token_tipo in [TOKEN.INT, TOKEN.FLOAT, TOKEN.CHAR]:
            return t1
    return None


def checar_atribuicao(tipo_var, tipo_expr):
    t_v, arr_v = tipo_var
    t_e, arr_e = tipo_expr


    if arr_v != arr_e:
        return False

    if arr_v and arr_e:

        return t_v == t_e


    if t_v == t_e: return True
    if t_v == TOKEN.FLOAT and t_e in [TOKEN.INT, TOKEN.CHAR]: return True
    if t_v == TOKEN.INT and t_e == TOKEN.CHAR: return True

    return False