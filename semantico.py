# semantico.py
from tabela_de_simbolos import TabelaDeSimbolos, Simbolo, \
    checar_operacao_binaria, checar_atribuicao, checar_operacao_unaria
from ttoken import TOKEN


class Semantico:
    def __init__(self):
        self.tabela = TabelaDeSimbolos()
        self.tipo_retorno_atual = None

        # Buffer onde guardaremos o código Python gerado
        self.codigo = []

        # Pilha de loops agora guarda o CÓDIGO DO INCREMENTO para resolver o bug do continue
        # Ex: {'tipo': 'for', 'incremento': 'i = i + 1'}
        self.pilha_loops = []

    def gera(self, nivel_indentacao, codigo_str):
        """ Escreve uma linha de código Python com a indentação correta """
        indent = "    " * nivel_indentacao  # 4 espaços por nível
        self.codigo.append(f"{indent}{codigo_str}")

    def obter_codigo_final(self):
        return "\n".join(self.codigo)

    # --- Controle de Escopo ---
    def entrar_escopo(self):
        self.tabela.entrar_escopo()

    def sair_escopo(self):
        self.tabela.sair_escopo()

    # --- Declarações ---
    def declarar_funcao(self, nome, tipo_retorno, params):
        lista_tipos_params = [p['tipo'] for p in params]
        simbolo = Simbolo(nome, tipo_retorno, 'funcao', {'params': lista_tipos_params})
        if not self.tabela.adicionar(simbolo):
            raise Exception(f"Erro Semântico: Função '{nome}' já declarada.")
        self.tipo_retorno_atual = tipo_retorno

    def declarar_parametro(self, nome, tipo):
        if not self.tabela.adicionar(Simbolo(nome, tipo, 'parametro')):
            raise Exception(f"Erro Semântico: Parâmetro '{nome}' duplicado.")

    def declarar_variavel(self, nome, tipo):
        categoria = 'array' if tipo[1] else 'variavel'
        if not self.tabela.adicionar(Simbolo(nome, tipo, categoria)):
            raise Exception(f"Erro Semântico: Variável '{nome}' já declarada.")

    # --- Validações ---
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
            raise Exception(f"Erro Semântico: Retorno inválido.")

    # --- Cálculos ---
    def calcular_binario(self, t1, op, t2):
        res = checar_operacao_binaria(t1, op, t2)
        if res is None: raise Exception(f"Erro Semântico: Operação inválida entre {t1} e {t2}.")
        return res

    def calcular_unario(self, op, t):
        res = checar_operacao_unaria(op, t)
        if res is None: raise Exception(f"Erro Semântico: Operação unária inválida em {t}.")
        return res

    # --- Controle de Fluxo (Adaptação para Python) ---
    def entrar_loop(self, tipo, codigo_incremento=None):
        """
        tipo: 'for' ou 'while'
        codigo_incremento: String com o código que deve rodar antes de um continue (só pro for)
        """
        self.pilha_loops.append({
            'tipo': tipo,
            'incremento': codigo_incremento
        })

    def sair_loop(self):
        if self.pilha_loops:
            self.pilha_loops.pop()

    def pegar_incremento_atual(self):
        """ Retorna o código de incremento do loop atual (se houver) """
        if self.pilha_loops:
            return self.pilha_loops[-1]['incremento']
        return None

    def verificar_dentro_loop(self, comando):
        if not self.pilha_loops:
            raise Exception(f"Erro Semântico: Comando '{comando}' fora de laço.")