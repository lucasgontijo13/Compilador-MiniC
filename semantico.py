# semantico.py
# Analisador Sintático e Semântico para a linguagem Mini-C.

import sys
from lexico import Lexico
from ttoken import TOKEN
from tabela_de_simbolos import TabelaDeSimbolos, Simbolo
from tipo import Tipo, token_para_tipo, compatibilidade_aritmetica, checar_compatibilidade_atribuicao, \
    checar_compatibilidade_relacional_logica


class Semantico:
    def __init__(self, nome_arquivo):
        self.lexico = Lexico(nome_arquivo)
        self.token_lido = None
        self.tabela = TabelaDeSimbolos()
        self.loop_level = 0
        self.funcao_atual = None

    def analisa(self):
        self.token_lido = self.lexico.prox_token()
        try:
            self.Program()
            self.consome(TOKEN.eof)
            print('\nAnálise sintática e semântica concluída com sucesso.')
        except Exception as e:
            print(f'\n[ANÁLISE INTERROMPIDA] {e}')

    def consome(self, token_esperado):
        if self.token_lido == token_esperado:
            self.token_lido = self.lexico.prox_token()
        else:
            lexema = self.lexico.lexema_atual
            linha = self.lexico.token_linha
            col = self.lexico.token_coluna
            msg_recebida = f"'{lexema}' ({TOKEN.msg(self.token_lido)})"
            msg_esperada = f"'{TOKEN.msg(token_esperado)}'"
            raise Exception(
                f'Erro Sintático na Linha {linha}, Coluna {col}: Esperado {msg_esperada}, mas foi recebido {msg_recebida}.')

    def erro_semantico(self, msg):
        linha = self.lexico.token_linha
        col = self.lexico.token_coluna
        raise Exception(f"Erro Semântico na Linha {linha}, Coluna {col}: {msg}")

    # --- REGRAS GRAMATICAIS COM AÇÕES SEMÂNTICAS ---

    def Program(self):
        while self.token_lido in [TOKEN.INT, TOKEN.FLOAT, TOKEN.CHAR]:
            self.Function()

    def Function(self):
        tipo_retorno = self.Type()
        nome_funcao = self.lexico.lexema_atual
        self.consome(TOKEN.ident)

        simbolo_funcao = Simbolo(nome_funcao, tipo_retorno, 'funcao', info_extras={'params': []})
        if not self.tabela.adicionar(simbolo_funcao):
            self.erro_semantico(f"Função '{nome_funcao}' já declarada.")
        self.funcao_atual = simbolo_funcao

        self.tabela.entrar_escopo()
        self.consome(TOKEN.abrePar)
        simbolo_funcao.info_extras['params'] = self.ArgList()
        self.consome(TOKEN.fechaPar)
        self.CompoundStmt()
        self.tabela.sair_escopo()
        self.funcao_atual = None

    def ArgList(self):
        params = []
        if self.token_lido in [TOKEN.INT, TOKEN.FLOAT, TOKEN.CHAR]:
            params.append(self.Arg())
            while self.token_lido == TOKEN.virg:
                self.consome(TOKEN.virg)
                params.append(self.Arg())
        return params

    def Arg(self):
        tipo_arg = self.Type()
        nome_arg = self.lexico.lexema_atual
        self.consome(TOKEN.ident)

        simbolo_arg = Simbolo(nome_arg, tipo_arg, 'parametro')
        if not self.tabela.adicionar(simbolo_arg):
            self.erro_semantico(f"Parâmetro '{nome_arg}' já declarado.")

        # Lida com array como argumento: int v[]
        if self.token_lido == TOKEN.abreColch:
            self.consome(TOKEN.abreColch)
            self.consome(TOKEN.fechaColch)
            simbolo_arg.categoria = 'array'
            simbolo_arg.tipo = Tipo.ARRAY
            simbolo_arg.info_extras['base_type'] = tipo_arg

        return simbolo_arg.tipo

    def CompoundStmt(self):
        self.consome(TOKEN.abreChave)
        self.StmtList()
        self.consome(TOKEN.fechaChave)

    def StmtList(self):
        first_stmt = [TOKEN.FOR, TOKEN.WHILE, TOKEN.IF, TOKEN.abreChave, TOKEN.BREAK, TOKEN.CONTINUE, TOKEN.RETURN,
                      TOKEN.ptoVirg, TOKEN.ident, TOKEN.valorInt, TOKEN.valorFloat, TOKEN.valorChar, TOKEN.abrePar,
                      TOKEN.INT, TOKEN.FLOAT, TOKEN.CHAR]

        # Entra em um novo escopo se não for o escopo da função
        is_function_body = (self.funcao_atual is not None and len(self.tabela.escopos) == 2)
        if not is_function_body:
            self.tabela.entrar_escopo()

        while self.token_lido in first_stmt:
            self.Stmt()

        if not is_function_body:
            self.tabela.sair_escopo()

    def Stmt(self):
        token = self.token_lido
        if token == TOKEN.FOR:
            self.ForStmt()
        elif token == TOKEN.WHILE:
            self.WhileStmt()
        elif token == TOKEN.IF:
            self.IfStmt()
        elif token == TOKEN.abreChave:
            self.CompoundStmt()
        elif token == TOKEN.BREAK:
            if self.loop_level == 0: self.erro_semantico("'break' fora de um laço.")
            self.consome(TOKEN.BREAK);
            self.consome(TOKEN.ptoVirg)
        elif token == TOKEN.CONTINUE:
            if self.loop_level == 0: self.erro_semantico("'continue' fora de um laço.")
            self.consome(TOKEN.CONTINUE);
            self.consome(TOKEN.ptoVirg)
        elif token == TOKEN.RETURN:
            self.consome(TOKEN.RETURN)
            if self.funcao_atual is None: self.erro_semantico("'return' fora de uma função.")

            tipo_expr = self.Expr()
            tipo_esperado = self.funcao_atual.tipo

            if not checar_compatibilidade_atribuicao(tipo_esperado, tipo_expr):
                self.erro_semantico(
                    f"Tipo de retorno incompatível. Esperado '{tipo_esperado.value}', recebido '{tipo_expr.value}'.")

            self.consome(TOKEN.ptoVirg)
        elif token in [TOKEN.INT, TOKEN.FLOAT, TOKEN.CHAR]:
            self.Declaration()
        elif token == TOKEN.ptoVirg:
            self.consome(TOKEN.ptoVirg)
        else:
            self.Expr(); self.consome(TOKEN.ptoVirg)

    def ForStmt(self):
        self.consome(TOKEN.FOR);
        self.consome(TOKEN.abrePar)
        self.Expr();
        self.consome(TOKEN.ptoVirg)
        self.Expr();
        self.consome(TOKEN.ptoVirg)
        self.Expr();
        self.consome(TOKEN.fechaPar)
        self.loop_level += 1
        self.Stmt()
        self.loop_level -= 1

    def WhileStmt(self):
        self.consome(TOKEN.WHILE);
        self.consome(TOKEN.abrePar)
        self.Expr();
        self.consome(TOKEN.fechaPar)
        self.loop_level += 1
        self.Stmt()
        self.loop_level -= 1

    def IfStmt(self):
        self.consome(TOKEN.IF);
        self.consome(TOKEN.abrePar)
        self.Expr();
        self.consome(TOKEN.fechaPar)
        self.Stmt()
        if self.token_lido == TOKEN.ELSE:
            self.consome(TOKEN.ELSE);
            self.Stmt()

    def Declaration(self):
        tipo = self.Type()
        self.IdentList(tipo)
        self.consome(TOKEN.ptoVirg)

    def Type(self):
        tipo = token_para_tipo(self.token_lido)
        if tipo == Tipo.ERRO:
            self.erro_semantico("Tipo (int, float, char) esperado.")
        self.consome(self.token_lido)
        return tipo

    def IdentList(self, tipo):
        self.IdentDeclar(tipo)
        while self.token_lido == TOKEN.virg:
            self.consome(TOKEN.virg)
            self.IdentDeclar(tipo)

    def IdentDeclar(self, tipo):
        nome = self.lexico.lexema_atual
        self.consome(TOKEN.ident)
        categoria = 'variavel'
        info = {}

        # Declaração de array: int v[10];
        if self.token_lido == TOKEN.abreColch:
            categoria = 'array'
            info = {'base_type': tipo}
            tipo = Tipo.ARRAY  # O tipo principal do símbolo é ARRAY
            self.consome(TOKEN.abreColch)
            if self.token_lido != TOKEN.valorInt:
                self.erro_semantico("Tamanho do array deve ser um inteiro.")
            self.consome(TOKEN.valorInt)
            self.consome(TOKEN.fechaColch)

        simbolo = Simbolo(nome, tipo, categoria, info_extras=info)
        if not self.tabela.adicionar(simbolo):
            self.erro_semantico(f"Variável '{nome}' já declarada neste escopo.")

    # --- ANÁLISE DE EXPRESSÃO COM CHECAGEM DE TIPO ---

    def Expr(self):
        tipo_esq = self.Log()
        if self.token_lido == TOKEN.atrib:
            self.consome(TOKEN.atrib)
            tipo_dir = self.Expr()
            if not checar_compatibilidade_atribuicao(tipo_esq, tipo_dir):
                self.erro_semantico(
                    f"Atribuição incompatível. Não é possível atribuir '{tipo_dir.value}' a uma variável do tipo '{tipo_esq.value}'.")
            return tipo_esq
        return tipo_esq

    def Log(self):
        tipo_esq = self.Rel()
        while self.token_lido in [TOKEN.AND, TOKEN.OR]:
            op = self.token_lido
            self.consome(op)
            tipo_dir = self.Rel()
            tipo_res = checar_compatibilidade_relacional_logica(tipo_esq, tipo_dir)
            if tipo_res == Tipo.ERRO:
                self.erro_semantico(
                    f"Operador lógico '{TOKEN.msg(op)}' não pode ser aplicado aos tipos '{tipo_esq.value}' e '{tipo_dir.value}'.")
            tipo_esq = tipo_res
        return tipo_esq

    def Rel(self):
        tipo_esq = self.Soma()
        if self.token_lido == TOKEN.opRel:
            op = self.token_lido
            self.consome(op)
            tipo_dir = self.Soma()
            tipo_res = checar_compatibilidade_relacional_logica(tipo_esq, tipo_dir)
            if tipo_res == Tipo.ERRO:
                self.erro_semantico(
                    f"Operador relacional '{TOKEN.msg(op)}' não pode ser aplicado aos tipos '{tipo_esq.value}' e '{tipo_dir.value}'.")
            return tipo_res
        return tipo_esq

    def Soma(self):
        tipo_esq = self.Mult()
        while self.token_lido in [TOKEN.mais, TOKEN.menos]:
            op = self.token_lido
            self.consome(op)
            tipo_dir = self.Mult()
            try:
                tipo_res = compatibilidade_aritmetica[tipo_esq][tipo_dir]
                tipo_esq = tipo_res
            except KeyError:
                self.erro_semantico(
                    f"Operador aritmético '{TOKEN.msg(op)}' não pode ser aplicado aos tipos '{tipo_esq.value}' e '{tipo_dir.value}'.")
        return tipo_esq

    def Mult(self):
        tipo_esq = self.Uno()
        while self.token_lido in [TOKEN.multiplica, TOKEN.divide, TOKEN.mod]:
            op = self.token_lido
            self.consome(op)
            tipo_dir = self.Uno()
            try:
                tipo_res = compatibilidade_aritmetica[tipo_esq][tipo_dir]
                tipo_esq = tipo_res
            except KeyError:
                self.erro_semantico(
                    f"Operador aritmético '{TOKEN.msg(op)}' não pode ser aplicado aos tipos '{tipo_esq.value}' e '{tipo_dir.value}'.")
        return tipo_esq

    def Uno(self):
        if self.token_lido in [TOKEN.mais, TOKEN.menos]:
            self.consome(self.token_lido)
            return self.Uno()
        return self.Folha()

    def Folha(self):
        token = self.token_lido
        if token == TOKEN.abrePar:
            self.consome(TOKEN.abrePar)
            tipo = self.Expr()
            self.consome(TOKEN.fechaPar)
            return tipo
        elif token == TOKEN.ident:
            return self.Identifier()
        elif token == TOKEN.valorInt:
            self.consome(token)
            return Tipo.INT
        elif token == TOKEN.valorFloat:
            self.consome(token)
            return Tipo.FLOAT
        elif token == TOKEN.valorChar:
            self.consome(token)
            return Tipo.CHAR
        else:
            self.erro_semantico(f"Expressão inesperada começando com '{self.lexico.lexema_atual}'.")

    def Identifier(self):
        nome = self.lexico.lexema_atual
        simbolo = self.tabela.buscar(nome)
        if simbolo is None:
            self.erro_semantico(f"Identificador '{nome}' não declarado.")

        self.consome(TOKEN.ident)

        # Acesso a array: v[i]
        if self.token_lido == TOKEN.abreColch:
            if simbolo.categoria != 'array':
                self.erro_semantico(f"'{nome}' não é um array e não pode ser indexado.")
            self.consome(TOKEN.abreColch)
            tipo_indice = self.Expr()
            if tipo_indice != Tipo.INT:
                self.erro_semantico("Índice do array deve ser um inteiro.")
            self.consome(TOKEN.fechaColch)
            return simbolo.info_extras['base_type']  # O tipo do acesso é o tipo base do array

        # Chamada de função: f(a, b)
        if self.token_lido == TOKEN.abrePar:
            if simbolo.categoria != 'funcao':
                self.erro_semantico(f"'{nome}' não é uma função e não pode ser chamada.")
            self.consome(TOKEN.abrePar)
            # Checagem de parâmetros
            params_passados = self.Params()
            params_esperados = simbolo.info_extras['params']
            if len(params_passados) != len(params_esperados):
                self.erro_semantico(
                    f"Função '{nome}' chamada com número incorreto de argumentos. Esperado {len(params_esperados)}, recebido {len(params_passados)}.")

            for i, (tipo_passado, tipo_esperado) in enumerate(zip(params_passados, params_esperados)):
                if not checar_compatibilidade_atribuicao(tipo_esperado, tipo_passado):
                    self.erro_semantico(
                        f"Argumento {i + 1} da função '{nome}' incompatível. Esperado '{tipo_esperado.value}', recebido '{tipo_passado.value}'.")

            self.consome(TOKEN.fechaPar)
            return simbolo.tipo  # O tipo da expressão é o tipo de retorno da função

        return simbolo.tipo

    def Params(self):
        tipos_params = []
        first_expr = [TOKEN.ident, TOKEN.valorInt, TOKEN.valorFloat, TOKEN.valorChar, TOKEN.abrePar]
        if self.token_lido in first_expr:
            tipos_params.append(self.Expr())
            while self.token_lido == TOKEN.virg:
                self.consome(TOKEN.virg)
                tipos_params.append(self.Expr())
        return tipos_params


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("\nUso: python semantico.py <arquivo_de_entrada>\n")
        sys.exit(1)

    analisador = Semantico(sys.argv[1])
    analisador.analisa()