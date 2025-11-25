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
        self._inicializar_stdlib()

    def _inicializar_stdlib(self):
        # Input
        self.adicionar(Simbolo('getint', (TOKEN.INT, False), 'funcao', {'params': []}))
        self.adicionar(Simbolo('getfloat', (TOKEN.FLOAT, False), 'funcao', {'params': []}))
        self.adicionar(Simbolo('getchar', (TOKEN.CHAR, False), 'funcao', {'params': []}))
        # Output
        self.adicionar(Simbolo('putint', (TOKEN.INT, False), 'funcao', {'params': [(TOKEN.INT, False)]}))
        self.adicionar(Simbolo('putfloat', (TOKEN.INT, False), 'funcao', {'params': [(TOKEN.FLOAT, False)]}))
        self.adicionar(Simbolo('putchar', (TOKEN.INT, False), 'funcao', {'params': [(TOKEN.CHAR, False)]}))
        self.adicionar(Simbolo('putstr', (TOKEN.INT, False), 'funcao', {'params': [(TOKEN.CHAR, True)]}))

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


# --- REGRAS DE TIPOS (Lógica do Gustavo com Frozenset) ---

# Mapeamento de regras binárias: Chave=Set((t1,op,t2)), Valor=TipoResultado
regras_operacoes_binarias = {
    # Soma (+)
    frozenset({(TOKEN.INT, False), TOKEN.mais, (TOKEN.INT, False)}): (TOKEN.INT, False),
    frozenset({(TOKEN.FLOAT, False), TOKEN.mais, (TOKEN.FLOAT, False)}): (TOKEN.FLOAT, False),
    frozenset({(TOKEN.INT, False), TOKEN.mais, (TOKEN.FLOAT, False)}): (TOKEN.FLOAT, False),
    frozenset({(TOKEN.CHAR, False), TOKEN.mais, (TOKEN.CHAR, False)}): (TOKEN.INT, False),
    frozenset({(TOKEN.INT, False), TOKEN.mais, (TOKEN.CHAR, False)}): (TOKEN.INT, False),
    frozenset({(TOKEN.FLOAT, False), TOKEN.mais, (TOKEN.CHAR, False)}): (TOKEN.FLOAT, False),

    # Subtração (-)
    frozenset({(TOKEN.INT, False), TOKEN.menos, (TOKEN.INT, False)}): (TOKEN.INT, False),
    frozenset({(TOKEN.FLOAT, False), TOKEN.menos, (TOKEN.FLOAT, False)}): (TOKEN.FLOAT, False),
    frozenset({(TOKEN.INT, False), TOKEN.menos, (TOKEN.FLOAT, False)}): (TOKEN.FLOAT, False),
    frozenset({(TOKEN.CHAR, False), TOKEN.menos, (TOKEN.CHAR, False)}): (TOKEN.INT, False),

    # Multiplicação (*)
    frozenset({(TOKEN.INT, False), TOKEN.multiplica, (TOKEN.INT, False)}): (TOKEN.INT, False),
    frozenset({(TOKEN.FLOAT, False), TOKEN.multiplica, (TOKEN.FLOAT, False)}): (TOKEN.FLOAT, False),
    frozenset({(TOKEN.INT, False), TOKEN.multiplica, (TOKEN.FLOAT, False)}): (TOKEN.FLOAT, False),

    # Divisão (/)
    frozenset({(TOKEN.INT, False), TOKEN.divide, (TOKEN.INT, False)}): (TOKEN.INT, False),
    frozenset({(TOKEN.FLOAT, False), TOKEN.divide, (TOKEN.FLOAT, False)}): (TOKEN.FLOAT, False),
    frozenset({(TOKEN.INT, False), TOKEN.divide, (TOKEN.FLOAT, False)}): (TOKEN.FLOAT, False),

    # Relacionais (>, <, ==, !=) -> Sempre retornam INT (0 ou 1)
    frozenset({(TOKEN.INT, False), TOKEN.opRel, (TOKEN.INT, False)}): (TOKEN.INT, False),
    frozenset({(TOKEN.FLOAT, False), TOKEN.opRel, (TOKEN.FLOAT, False)}): (TOKEN.INT, False),
    frozenset({(TOKEN.INT, False), TOKEN.opRel, (TOKEN.FLOAT, False)}): (TOKEN.INT, False),
    frozenset({(TOKEN.CHAR, False), TOKEN.opRel, (TOKEN.CHAR, False)}): (TOKEN.INT, False),

    # Lógicos (&&, ||)
    frozenset({(TOKEN.INT, False), TOKEN.AND, (TOKEN.INT, False)}): (TOKEN.INT, False),
    frozenset({(TOKEN.INT, False), TOKEN.OR, (TOKEN.INT, False)}): (TOKEN.INT, False),
}

# Regras Unárias
regras_operacoes_unarias = {
    (TOKEN.menos, (TOKEN.INT, False)): (TOKEN.INT, False),
    (TOKEN.menos, (TOKEN.FLOAT, False)): (TOKEN.FLOAT, False),
    (TOKEN.NOT, (TOKEN.INT, False)): (TOKEN.INT, False),
}


def checar_operacao_binaria(t1, op, t2):
    # O set ignora a ordem, permitindo 10+float ou float+10
    chave = frozenset({t1, op, t2})
    return regras_operacoes_binarias.get(chave, None)


def checar_operacao_unaria(op, t1):
    chave = (op, t1)
    return regras_operacoes_unarias.get(chave, None)


def checar_atribuicao(tipo_var, tipo_expr):
    t_v, arr_v = tipo_var
    t_e, arr_e = tipo_expr

    # 1. Se são idênticos, aceita sempre.
    if tipo_var == tipo_expr:
        return True

    # 2. Lógica para Arrays (Resolvendo o putstr(0))
    if arr_v:
        # Se a variável é array e a expressão também, os tipos devem bater (Ex: char[] = char[])
        if arr_e: return t_v == t_e

        # EXCEÇÃO: Aceita Inteiro sendo passado para Array (Simula NULL ou Endereço de Memória)
        # Isso faz o putstr(0) funcionar.
        if t_e == TOKEN.INT: return True

        # Qualquer outra coisa (tipo float para array) é erro
        return False

    # 3. Lógica para Escalares (Resolvendo o putchar(65))
    # Se a variável NÃO é array
    # "Se a variável é int/float/char E a expressão é int/float/char -> ACEITA TUDO"

    tipos_basicos = [TOKEN.INT, TOKEN.FLOAT, TOKEN.CHAR]

    if t_v in tipos_basicos and t_e in tipos_basicos and not arr_e:
        return True

    return False