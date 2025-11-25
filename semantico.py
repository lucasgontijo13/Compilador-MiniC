# semantico.py
from tabela_de_simbolos import TabelaDeSimbolos, Simbolo, \
    checar_operacao_binaria, checar_atribuicao, checar_operacao_unaria
from ttoken import TOKEN


class Semantico:
    def __init__(self):
        # Note que NÃO recebemos mais 'nome_arquivo'. O Semantico não lê arquivo.
        self.tabela = TabelaDeSimbolos()
        self.tipo_retorno_atual = None
        self.dentro_de_loop = 0

    def entrar_escopo(self):
        self.tabela.entrar_escopo()

    def sair_escopo(self):
        self.tabela.sair_escopo()

    # --- Declarações ---

    def declarar_funcao(self, nome, tipo_retorno, params):
        # params é uma lista de dicionários: [{'nome': 'x', 'tipo': (TOKEN.INT, False)}, ...]

        # Converte para o formato que a Tabela espera (lista de tipos)
        lista_tipos_params = [p['tipo'] for p in params]

        simbolo = Simbolo(nome, tipo_retorno, 'funcao', {'params': lista_tipos_params})

        if not self.tabela.adicionar(simbolo):
            raise Exception(f"Erro Semântico: Função '{nome}' já declarada.")

        self.tipo_retorno_atual = tipo_retorno

    def declarar_parametro(self, nome, tipo):
        simbolo = Simbolo(nome, tipo, 'parametro')
        if not self.tabela.adicionar(simbolo):
            raise Exception(f"Erro Semântico: Parâmetro '{nome}' duplicado.")

    def declarar_variavel(self, nome, tipo):
        # Define se é array ou variável simples
        categoria = 'array' if tipo[1] else 'variavel'
        simbolo = Simbolo(nome, tipo, categoria)

        if not self.tabela.adicionar(simbolo):
            raise Exception(f"Erro Semântico: Variável '{nome}' já declarada neste escopo.")

    # --- Validações de Uso ---

    def verificar_existencia(self, nome):
        simbolo = self.tabela.buscar(nome)
        if not simbolo:
            raise Exception(f"Erro Semântico: Identificador '{nome}' não declarado.")
        return simbolo

    def verificar_atribuicao(self, tipo_var, tipo_expr):
        if not checar_atribuicao(tipo_var, tipo_expr):
            raise Exception(f"Erro Semântico: Atribuição incompatível. Tentou atribuir {tipo_expr} em {tipo_var}.")

    def verificar_return(self, tipo_expr):
        if self.tipo_retorno_atual is None:
            raise Exception("Erro Semântico: 'return' fora de função.")

        if not checar_atribuicao(self.tipo_retorno_atual, tipo_expr):
            raise Exception(f"Erro Semântico: Retorno inválido. Esperado {self.tipo_retorno_atual}, veio {tipo_expr}.")

    # --- Operações Matemáticas (Retornam o Tipo Resultante) ---

    def calcular_binario(self, t1, op, t2):
        res = checar_operacao_binaria(t1, op, t2)
        if res is None:
            raise Exception(f"Erro Semântico: Operação inválida entre {t1} e {t2}.")
        return res

    def calcular_unario(self, op, t):
        res = checar_operacao_unaria(op, t)
        if res is None:
            raise Exception(f"Erro Semântico: Operação unária inválida em {t}.")
        return res

    # --- Controle de Fluxo ---

    def entrar_loop(self):
        self.dentro_de_loop += 1

    def sair_loop(self):
        self.dentro_de_loop -= 1

    def verificar_break_continue(self):
        if self.dentro_de_loop == 0:
            raise Exception("Erro Semântico: Comando 'break' ou 'continue' fora de laço.")