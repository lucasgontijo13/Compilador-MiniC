import sys
from lexico import Lexico
from ttoken import TOKEN
# MUDANÇA: Tudo vem da tabela de símbolos agora
from tabela_de_simbolos import TabelaDeSimbolos, Simbolo, \
    checar_operacao_binaria, checar_atribuicao, checar_operacao_unaria


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
            print('\nAnálise semântica concluída com sucesso!')
        except Exception as e:
            print(f'\n[ERRO] {e}')
            sys.exit(1)

    def consome(self, token_esperado):
        if self.token_lido == token_esperado:
            self.token_lido = self.lexico.prox_token()
        else:
            # Captura dados para o erro
            lexema = self.lexico.lexema_atual
            linha = self.lexico.token_linha

            # Tenta recuperar a linha do código fonte (Contexto)
            txt_linha = ""
            try:
                linhas_codigo = self.lexico.buffer.splitlines()
                if 0 <= linha - 1 < len(linhas_codigo):
                    txt_linha = linhas_codigo[linha - 1].strip()
            except:
                txt_linha = "..."

            msg_esperada = TOKEN.msg(token_esperado)
            msg_recebida = TOKEN.msg(self.token_lido)

            # Formata a mensagem igual ao erro semântico
            mensagem_erro = (
                f"\n"
                f"🛑 ERRO SINTÁTICO (Linha {linha})\n"
                f"---------------------------------------------------\n"
                f"Descrição : Esperado '{msg_esperada}', mas encontrei '{msg_recebida}'.\n"
                f"Causador  : '{lexema}'\n"
                f"Contexto  : {txt_linha}\n"
                f"---------------------------------------------------"
            )

            raise Exception(mensagem_erro)

    def erro_semantico(self, msg):
        linha = self.lexico.token_linha
        lexema = self.lexico.lexema_atual

        # Tenta recuperar a linha original do código fonte para dar contexto
        txt_linha = ""
        try:
            linhas_codigo = self.lexico.buffer.splitlines()
            if 0 <= linha - 1 < len(linhas_codigo):
                txt_linha = linhas_codigo[linha - 1].strip()
        except:
            txt_linha = "..."

        # Formata uma mensagem de erro visualmente clara
        mensagem_erro = (
            f"\n"
            f"🛑 ERRO SEMÂNTICO (Linha {linha})\n"
            f"---------------------------------------------------\n"
            f"Descrição : {msg}\n"
            f"Causador  : '{lexema}' (Token: {TOKEN.msg(self.token_lido)})\n"
            f"Contexto  : {txt_linha}\n"
            f"---------------------------------------------------"
        )

        # Removemos o prefixo "Erro Semântico na Linha..." da Exception,
        # pois nossa mensagem formatada já contém tudo.
        raise Exception(mensagem_erro)

    # --- GRAMÁTICA ---

    def Program(self):
        while self.token_lido in [TOKEN.INT, TOKEN.FLOAT, TOKEN.CHAR]:
            self.Function()
        simbolo_main = self.tabela.buscar('main')
        if not simbolo_main:
            self.erro_semantico("A função principal 'main' não foi encontrada.")
        if simbolo_main.categoria != 'funcao':
            self.erro_semantico("O identificador 'main' deve ser uma função.")

    def Function(self):
        tipo_retorno = self.Type()
        nome_funcao = self.lexico.lexema_atual
        self.consome(TOKEN.ident)

        simbolo_func = Simbolo(nome_funcao, tipo_retorno, 'funcao', info_extras={'params': []})
        if not self.tabela.adicionar(simbolo_func):
            self.erro_semantico(f"Função '{nome_funcao}' já declarada.")

        self.funcao_atual = simbolo_func
        self.tabela.entrar_escopo()

        self.consome(TOKEN.abrePar)
        simbolo_func.info_extras['params'] = self.ArgList()
        self.consome(TOKEN.fechaPar)

        self.CompoundStmt(is_func_body=True)
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
        tipo_base_tuple = self.Type()
        token_base = tipo_base_tuple[0]

        nome = self.lexico.lexema_atual
        self.consome(TOKEN.ident)

        eh_array = False
        if self.token_lido == TOKEN.abreColch:
            self.consome(TOKEN.abreColch)
            self.consome(TOKEN.fechaColch)
            eh_array = True

        tipo_final = (token_base, eh_array)
        simbolo = Simbolo(nome, tipo_final, 'parametro')
        if not self.tabela.adicionar(simbolo):
            self.erro_semantico(f"Parâmetro '{nome}' duplicado.")

        return tipo_final

    def CompoundStmt(self, is_func_body=False):
        self.consome(TOKEN.abreChave)
        self.StmtList(is_func_body)
        self.consome(TOKEN.fechaChave)

    def StmtList(self, is_func_body=False):
        if not is_func_body:
            self.tabela.entrar_escopo()

        first = [TOKEN.FOR, TOKEN.WHILE, TOKEN.IF, TOKEN.abreChave, TOKEN.BREAK,
                 TOKEN.CONTINUE, TOKEN.RETURN, TOKEN.ptoVirg, TOKEN.INT, TOKEN.FLOAT, TOKEN.CHAR,
                 TOKEN.ident, TOKEN.valorInt, TOKEN.valorFloat, TOKEN.valorChar,
                 TOKEN.abrePar, TOKEN.mais, TOKEN.menos, TOKEN.NOT]

        while self.token_lido in first:
            self.Stmt()

        if not is_func_body:
            self.tabela.sair_escopo()

    def Stmt(self):
        tk = self.token_lido
        if tk == TOKEN.FOR:
            self.ForStmt()
        elif tk == TOKEN.WHILE:
            self.WhileStmt()
        elif tk == TOKEN.IF:
            self.IfStmt()
        elif tk == TOKEN.abreChave:
            self.CompoundStmt()
        elif tk == TOKEN.BREAK:
            if self.loop_level == 0: self.erro_semantico("'break' fora de laço.")
            self.consome(TOKEN.BREAK);
            self.consome(TOKEN.ptoVirg)
        elif tk == TOKEN.CONTINUE:
            if self.loop_level == 0: self.erro_semantico("'continue' fora de laço.")
            self.consome(TOKEN.CONTINUE);
            self.consome(TOKEN.ptoVirg)
        elif tk == TOKEN.RETURN:
            self.consome(TOKEN.RETURN)
            if not self.funcao_atual: self.erro_semantico("Return fora de função.")

            tipo_expr = self.Expr()

            if not checar_atribuicao(self.funcao_atual.tipo, tipo_expr):
                t_esp = f"{TOKEN.msg(self.funcao_atual.tipo[0])}"
                t_rec = f"{TOKEN.msg(tipo_expr[0])}"
                self.erro_semantico(f"Retorno inválido. Esperado {t_esp}, recebido {t_rec}.")
            self.consome(TOKEN.ptoVirg)

        elif tk in [TOKEN.INT, TOKEN.FLOAT, TOKEN.CHAR]:
            self.Declaration()
        elif tk == TOKEN.ptoVirg:
            self.consome(TOKEN.ptoVirg)
        else:
            self.Expr()
            self.consome(TOKEN.ptoVirg)

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
        tipo_base = self.Type()
        self.IdentList(tipo_base)
        self.consome(TOKEN.ptoVirg)

    def Type(self):
        tk = self.token_lido
        if tk not in [TOKEN.INT, TOKEN.FLOAT, TOKEN.CHAR]:
            self.erro_semantico("Esperado tipo (int, float, char).")
        self.consome(tk)
        return (tk, False)

    def IdentList(self, tipo_base_tuple):
        self.IdentDeclar(tipo_base_tuple)
        while self.token_lido == TOKEN.virg:
            self.consome(TOKEN.virg)
            self.IdentDeclar(tipo_base_tuple)

    def IdentDeclar(self, tipo_base_tuple):
        nome = self.lexico.lexema_atual
        self.consome(TOKEN.ident)

        token_base = tipo_base_tuple[0]
        eh_array = False

        if self.token_lido == TOKEN.abreColch:
            self.consome(TOKEN.abreColch)
            if self.token_lido != TOKEN.valorInt:
                self.erro_semantico("Tamanho do array deve ser inteiro.")
            self.consome(TOKEN.valorInt)
            self.consome(TOKEN.fechaColch)
            eh_array = True

        tipo_final = (token_base, eh_array)
        categoria = 'array' if eh_array else 'variavel'
        simbolo = Simbolo(nome, tipo_final, categoria, info_extras={'base_token': token_base})

        if not self.tabela.adicionar(simbolo):
            self.erro_semantico(f"Variável '{nome}' redeclarada.")

    # --- EXPRESSÕES ---

    def Expr(self):
        t_esq = self.Log()

        if self.token_lido == TOKEN.atrib:
            self.consome(TOKEN.atrib)
            t_dir = self.Expr()

            if not checar_atribuicao(t_esq, t_dir):
                self.erro_semantico(f"Atribuição inválida entre tipos.")

            return t_esq
        return t_esq

    def Log(self):
        t_atual = self.Rel()
        while self.token_lido in [TOKEN.AND, TOKEN.OR]:
            op = self.token_lido
            self.consome(op)
            t_dir = self.Rel()

            res = checar_operacao_binaria(t_atual, op, t_dir)
            if res is None:
                self.erro_semantico(f"Operação lógica incompatível.")
            t_atual = res
        return t_atual

    def Rel(self):
        t_atual = self.Soma()
        if self.token_lido == TOKEN.opRel:
            op = self.token_lido
            self.consome(op)
            t_dir = self.Soma()

            res = checar_operacao_binaria(t_atual, op, t_dir)
            if res is None:
                self.erro_semantico(f"Operação relacional incompatível.")
            t_atual = res
        return t_atual

    def Soma(self):
        t_atual = self.Mult()
        while self.token_lido in [TOKEN.mais, TOKEN.menos]:
            op = self.token_lido
            self.consome(op)
            t_dir = self.Mult()

            res = checar_operacao_binaria(t_atual, op, t_dir)
            if res is None:
                self.erro_semantico(f"Operação aritmética (+/-) inválida.")
            t_atual = res
        return t_atual

    def Mult(self):
        t_atual = self.Uno()
        while self.token_lido in [TOKEN.multiplica, TOKEN.divide, TOKEN.mod]:
            op = self.token_lido
            self.consome(op)
            t_dir = self.Uno()

            res = checar_operacao_binaria(t_atual, op, t_dir)
            if res is None:
                if op == TOKEN.mod:
                    self.erro_semantico("Módulo (%) requer inteiros.")
                else:
                    self.erro_semantico(f"Operação aritmética (*,/,%) inválida.")
            t_atual = res
        return t_atual

    def Uno(self):
        if self.token_lido in [TOKEN.mais, TOKEN.menos, TOKEN.NOT]:
            op = self.token_lido
            self.consome(op)
            t_tuple = self.Uno()

            res = checar_operacao_unaria(op, t_tuple)
            if res is None:
                self.erro_semantico("Operação unária inválida.")
            return res
        return self.Folha()

    def Folha(self):
        tk = self.token_lido

        if tk == TOKEN.abrePar:
            self.consome(TOKEN.abrePar)
            t = self.Expr()
            self.consome(TOKEN.fechaPar)
            return t

        elif tk == TOKEN.ident:
            return self.Identifier()

        elif tk == TOKEN.valorInt:
            self.consome(tk);
            return (TOKEN.INT, False)
        elif tk == TOKEN.valorFloat:
            self.consome(tk);
            return (TOKEN.FLOAT, False)
        elif tk == TOKEN.valorChar:
            self.consome(tk);
            return (TOKEN.CHAR, False)
        elif tk == TOKEN.valorString:
            # String é um array de char
            self.consome(tk);
            return (TOKEN.CHAR, True)

        self.erro_semantico("Esperado expressão.")

    def Identifier(self):
        nome = self.lexico.lexema_atual
        simbolo = self.tabela.buscar(nome)
        if not simbolo:
            self.erro_semantico(f"Identificador '{nome}' não declarado.")
        self.consome(TOKEN.ident)

        # 1. Array com índice -> v[i]
        if self.token_lido == TOKEN.abreColch:
            eh_array = simbolo.tipo[1]

            if not eh_array:
                self.erro_semantico(f"'{nome}' não é array.")

            self.consome(TOKEN.abreColch)
            t_idx = self.Expr()
            # Indice deve ser inteiro (INT ou CHAR) e NÃO pode ser array
            if t_idx[0] not in [TOKEN.INT, TOKEN.CHAR] or t_idx[1]:
                self.erro_semantico("Índice deve ser inteiro.")
            self.consome(TOKEN.fechaColch)

            # Retorna o tipo base: (TOKEN.INT, False)
            return (simbolo.tipo[0], False)

        # 2. Função -> f()
        if self.token_lido == TOKEN.abrePar:
            if simbolo.categoria != 'funcao':
                self.erro_semantico(f"'{nome}' não é função.")
            self.consome(TOKEN.abrePar)
            params_reais = self.Params()
            self.consome(TOKEN.fechaPar)

            params_formais = simbolo.info_extras['params']
            if len(params_reais) != len(params_formais):
                self.erro_semantico(f"Número de argumentos incorreto p/ '{nome}'.")

            for i, (t_real, t_formal) in enumerate(zip(params_reais, params_formais)):
                if not checar_atribuicao(t_formal, t_real):
                    self.erro_semantico(f"Argumento {i + 1} incompatível.")

            return simbolo.tipo  # Retorna tipo da função

        # 3. Variável simples, Parâmetro ou Nome do array (sem colchetes)
        return simbolo.tipo

    def Params(self):
        lista = []
        first = [TOKEN.ident, TOKEN.valorInt, TOKEN.valorFloat, TOKEN.valorChar, TOKEN.valorString, TOKEN.abrePar]

        if self.token_lido in first:
            t = self.Expr()
            lista.append(t)
            while self.token_lido == TOKEN.virg:
                self.consome(TOKEN.virg)
                t = self.Expr()
                lista.append(t)
        return lista

