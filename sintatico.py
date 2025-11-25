# sintatico.py
import sys
from lexico import Lexico
from ttoken import TOKEN
from semantico import Semantico
# Importante: Precisamos disso para validar os argumentos das funções
from tabela_de_simbolos import checar_atribuicao


class Sintatico:
    def __init__(self, lexico):
        self.lexico = lexico
        self.tokenLido = None
        # O Sintático instancia o validador
        self.semantico = Semantico()

    def analisa(self):
        self.tokenLido = self.lexico.prox_token()
        try:
            self.Program()
            self.consome(TOKEN.eof)
            print('\n---------------------------------------------------')
            print('✅ Análise sintática e semântica concluída com sucesso!')
            print('---------------------------------------------------')
        except Exception as e:
            self.imprimir_erro_detalhado(e)

    def imprimir_erro_detalhado(self, erro):
        """
        Formata o erro (Sintático ou Semântico) com contexto visual.
        """
        linha = self.lexico.token_linha
        # Tenta pegar o lexema atual do léxico
        lexema = self.lexico.lexema_atual

        # Recupera a linha do código fonte para mostrar o contexto
        txt_linha = "..."
        try:
            # O léxico tem o buffer completo do arquivo
            linhas_codigo = self.lexico.buffer.splitlines()
            if 0 <= linha - 1 < len(linhas_codigo):
                txt_linha = linhas_codigo[linha - 1].strip()
        except:
            pass

        print(f"\n🛑 ERRO (Linha {linha})")
        print("-" * 55)
        print(f"Descrição : {erro}")
        print(f"Contexto  : {txt_linha}")
        if lexema:
            print(f"Causador  : '{lexema}'")
        print("-" * 55 + "\n")

    def consome(self, token_esperado):
        token_atual = self.tokenLido
        if token_atual == token_esperado:
            self.tokenLido = self.lexico.prox_token()
        else:
            # Lança apenas a mensagem técnica. A formatação visual é feita no 'analisa'.
            msg_esp = TOKEN.msg(token_esperado)
            msg_rec = TOKEN.msg(token_atual)
            raise Exception(f"Esperado '{msg_esp}', mas encontrei '{msg_rec}'.")

    def Program(self):
        tipos = [TOKEN.INT, TOKEN.FLOAT, TOKEN.CHAR]
        while self.tokenLido in tipos:
            self.Function()

        # Validação final: Tem main?
        try:
            self.semantico.verificar_existencia('main')
        except Exception as e:
            raise Exception("Função 'main' não encontrada no código.")

    def Function(self):
        tipo_ret = self.Type()  # Retorna (TOKEN.INT, False)

        nome = self.lexico.lexema_atual
        self.consome(TOKEN.ident)

        self.consome(TOKEN.abrePar)

        # Lê parâmetros (retorna lista de dicts com nome e tipo)
        lista_params = self.ArgList()

        self.consome(TOKEN.fechaPar)

        # SEMANTICO: Declara a função e abre escopo
        self.semantico.declarar_funcao(nome, tipo_ret, lista_params)
        self.semantico.entrar_escopo()

        # SEMANTICO: Declara os parâmetros dentro do escopo da função
        for p in lista_params:
            self.semantico.declarar_parametro(p['nome'], p['tipo'])

        self.CompoundStmt(is_func=True)

        # SEMANTICO: Fecha escopo
        self.semantico.sair_escopo()

    def ArgList(self):
        # Retorna lista de parâmetros encontrados
        params = []
        tipos = [TOKEN.INT, TOKEN.FLOAT, TOKEN.CHAR]
        if self.tokenLido in tipos:
            params.append(self.Arg())
            params.extend(self.RestoArgList())
        return params

    def RestoArgList(self):
        params = []
        if self.tokenLido == TOKEN.virg:
            self.consome(TOKEN.virg)
            params.append(self.Arg())
            params.extend(self.RestoArgList())
        return params

    def Arg(self):
        tipo_base = self.Type()
        nome = self.lexico.lexema_atual
        self.consome(TOKEN.ident)
        is_array = self.OpcIdentArg()

        return {'nome': nome, 'tipo': (tipo_base[0], is_array)}

    def OpcIdentArg(self):
        if self.tokenLido == TOKEN.abreColch:
            self.consome(TOKEN.abreColch)
            self.consome(TOKEN.fechaColch)
            return True
        return False

    def CompoundStmt(self, is_func=False):
        self.consome(TOKEN.abreChave)

        # Se NÃO for corpo de função, abre um escopo novo (ex: if, while)
        if not is_func:
            self.semantico.entrar_escopo()

        self.StmtList()

        if not is_func:
            self.semantico.sair_escopo()

        self.consome(TOKEN.fechaChave)

    def StmtList(self):
        first_stmt = [TOKEN.FOR, TOKEN.WHILE, TOKEN.IF, TOKEN.abreChave, TOKEN.BREAK, TOKEN.CONTINUE, TOKEN.RETURN,
                      TOKEN.ptoVirg] + self.first_of_expr() + [TOKEN.INT, TOKEN.FLOAT, TOKEN.CHAR]
        while self.tokenLido in first_stmt:
            self.Stmt()

    def Stmt(self):
        token = self.tokenLido

        if token == TOKEN.FOR:
            self.ForStmt()
        elif token == TOKEN.WHILE:
            self.WhileStmt()
        elif token == TOKEN.IF:
            self.IfStmt()
        elif token == TOKEN.abreChave:
            self.CompoundStmt()
        elif token == TOKEN.BREAK:
            self.semantico.verificar_break_continue()
            self.consome(TOKEN.BREAK);
            self.consome(TOKEN.ptoVirg)
        elif token == TOKEN.CONTINUE:
            self.semantico.verificar_break_continue()
            self.consome(TOKEN.CONTINUE);
            self.consome(TOKEN.ptoVirg)
        elif token == TOKEN.RETURN:
            self.consome(TOKEN.RETURN)
            t_expr = self.Expr()  # Pega o tipo da expressão
            self.semantico.verificar_return(t_expr)  # Valida se bate com a função
            self.consome(TOKEN.ptoVirg)
        elif token in [TOKEN.INT, TOKEN.FLOAT, TOKEN.CHAR]:
            self.Declaration()
        elif token == TOKEN.ptoVirg:
            self.consome(TOKEN.ptoVirg)
        else:
            self.Expr()  # Apenas calcula e ignora o resultado
            self.consome(TOKEN.ptoVirg)

    def ForStmt(self):
        self.consome(TOKEN.FOR)
        self.semantico.entrar_loop()
        self.consome(TOKEN.abrePar)
        self.Expr()
        self.consome(TOKEN.ptoVirg)
        self.OptExpr()
        self.consome(TOKEN.ptoVirg)
        self.OptExpr()
        self.consome(TOKEN.fechaPar)
        self.Stmt()
        self.semantico.sair_loop()

    def WhileStmt(self):
        self.consome(TOKEN.WHILE)
        self.semantico.entrar_loop()
        self.consome(TOKEN.abrePar)
        self.Expr()
        self.consome(TOKEN.fechaPar)
        self.Stmt()
        self.semantico.sair_loop()

    def IfStmt(self):
        self.consome(TOKEN.IF)
        self.consome(TOKEN.abrePar)
        self.Expr()
        self.consome(TOKEN.fechaPar)
        self.Stmt()
        self.ElsePart()

    def ElsePart(self):
        if self.tokenLido == TOKEN.ELSE:
            self.consome(TOKEN.ELSE)
            self.Stmt()

    def Declaration(self):
        tipo_base = self.Type()
        self.IdentList(tipo_base)
        self.consome(TOKEN.ptoVirg)

    def IdentList(self, tipo_base):
        self.IdentDeclar(tipo_base)
        self.RestoIdentList(tipo_base)

    def RestoIdentList(self, tipo_base):
        if self.tokenLido == TOKEN.virg:
            self.consome(TOKEN.virg)
            self.IdentDeclar(tipo_base)
            self.RestoIdentList(tipo_base)

    def IdentDeclar(self, tipo_base):
        nome = self.lexico.lexema_atual
        self.consome(TOKEN.ident)

        eh_array = self.OpcIdentDeclar()
        tipo_final = (tipo_base[0], eh_array)

        self.semantico.declarar_variavel(nome, tipo_final)

    def OpcIdentDeclar(self):
        if self.tokenLido == TOKEN.abreColch:
            self.consome(TOKEN.abreColch)
            self.consome(TOKEN.valorInt)
            self.consome(TOKEN.fechaColch)
            return True
        return False

    def Type(self):
        token = self.tokenLido
        if token in [TOKEN.INT, TOKEN.FLOAT, TOKEN.CHAR]:
            self.consome(token)
            return (token, False)
        else:
            raise Exception("Tipo (int, float, char) esperado.")

    def OptExpr(self):
        if self.tokenLido in self.first_of_expr():
            return self.Expr()
        return (TOKEN.INT, False)  # Retorno padrão

    # --- EXPRESSÕES (Agora retornam TIPO) ---

    def first_of_expr(self):
        return [TOKEN.ident, TOKEN.valorInt, TOKEN.valorFloat, TOKEN.valorChar, TOKEN.valorString,
                TOKEN.abrePar, TOKEN.mais, TOKEN.menos, TOKEN.NOT]

    def Expr(self):
        t1 = self.Log()
        if self.tokenLido == TOKEN.atrib:
            self.consome(TOKEN.atrib)
            t2 = self.Expr()
            self.semantico.verificar_atribuicao(t1, t2)
            return t1
        return t1

    def Log(self):
        t1 = self.Nao()
        while self.tokenLido in [TOKEN.AND, TOKEN.OR]:
            op = self.tokenLido
            self.consome(op)
            t2 = self.Nao()
            t1 = self.semantico.calcular_binario(t1, op, t2)
        return t1

    def Nao(self):
        if self.tokenLido == TOKEN.NOT:
            op = self.tokenLido
            self.consome(TOKEN.NOT)
            t = self.Rel()
            return self.semantico.calcular_unario(op, t)
        return self.Rel()

    def Rel(self):
        t1 = self.Soma()
        if self.tokenLido == TOKEN.opRel:
            op = self.tokenLido
            self.consome(op)
            t2 = self.Soma()
            t1 = self.semantico.calcular_binario(t1, op, t2)
        return t1

    def Soma(self):
        t1 = self.Mult()
        while self.tokenLido in [TOKEN.mais, TOKEN.menos]:
            op = self.tokenLido
            self.consome(op)
            t2 = self.Mult()
            t1 = self.semantico.calcular_binario(t1, op, t2)
        return t1

    def Mult(self):
        t1 = self.Uno()
        while self.tokenLido in [TOKEN.multiplica, TOKEN.divide, TOKEN.mod]:
            op = self.tokenLido
            self.consome(op)
            t2 = self.Uno()
            t1 = self.semantico.calcular_binario(t1, op, t2)
        return t1

    def Uno(self):
        if self.tokenLido in [TOKEN.mais, TOKEN.menos]:
            op = self.tokenLido
            self.consome(op)
            t = self.Uno()
            return self.semantico.calcular_unario(op, t)
        return self.Folha()

    def Folha(self):
        token = self.tokenLido
        if token == TOKEN.abrePar:
            self.consome(TOKEN.abrePar)
            t = self.Expr()
            self.consome(TOKEN.fechaPar)
            return t
        elif token == TOKEN.ident:
            return self.Identifier()
        elif token == TOKEN.valorInt:
            self.consome(TOKEN.valorInt)
            return (TOKEN.INT, False)
        elif token == TOKEN.valorFloat:
            self.consome(TOKEN.valorFloat)
            return (TOKEN.FLOAT, False)
        elif token == TOKEN.valorChar:
            self.consome(TOKEN.valorChar)
            return (TOKEN.CHAR, False)
        elif token == TOKEN.valorString:
            self.consome(TOKEN.valorString)
            return (TOKEN.CHAR, True)
        else:
            raise Exception("Expressão esperada (identificador, número ou parenteses).")

    def Identifier(self):
        nome = self.lexico.lexema_atual
        # Primeiro, buscamos na tabela para saber o que é
        simbolo = self.semantico.verificar_existencia(nome)
        self.consome(TOKEN.ident)

        return self.OpcIdentifier(simbolo)

    def OpcIdentifier(self, simbolo):
        token = self.tokenLido

        # Array: v[i]
        if token == TOKEN.abreColch:
            if not simbolo.tipo[1]:  # Não é array
                raise Exception(f"Erro Semântico: '{simbolo.nome}' não é array.")

            self.consome(TOKEN.abreColch)
            t_idx = self.Expr()
            if t_idx[0] not in [TOKEN.INT, TOKEN.CHAR] or t_idx[1]:
                raise Exception("Erro Semântico: Índice deve ser inteiro.")
            self.consome(TOKEN.fechaColch)
            return (simbolo.tipo[0], False)  # Retorna o tipo base do elemento

        # Função: f(x)
        elif token == TOKEN.abrePar:
            if simbolo.categoria != 'funcao':
                raise Exception(f"Erro Semântico: '{simbolo.nome}' não é função.")

            self.consome(TOKEN.abrePar)
            self.Params(simbolo)
            self.consome(TOKEN.fechaPar)
            return simbolo.tipo  # Retorna o tipo de retorno da função

        # Variável simples
        return simbolo.tipo

    def Params(self, simbolo_func):
        params_formais = simbolo_func.info_extras['params']
        if self.tokenLido in self.first_of_expr():
            # Verifica o primeiro argumento
            if len(params_formais) < 1:
                raise Exception(f"Erro Semântico: Excesso de argumentos em {simbolo_func.nome}")

            t_arg = self.Expr()
            if not checar_atribuicao(params_formais[0], t_arg):
                raise Exception(f"Erro Semântico: Argumento 1 inválido em {simbolo_func.nome}")

            self.RestoParams(simbolo_func, params_formais, 1)
        else:
            if len(params_formais) > 0:
                raise Exception(f"Erro Semântico: Faltam argumentos em {simbolo_func.nome}")

    def RestoParams(self, simbolo_func, params_formais, index):
        if self.tokenLido == TOKEN.virg:
            self.consome(TOKEN.virg)

            if index >= len(params_formais):
                raise Exception(f"Erro Semântico: Excesso de argumentos em {simbolo_func.nome}")

            t_arg = self.Expr()
            if not checar_atribuicao(params_formais[index], t_arg):
                raise Exception(f"Erro Semântico: Argumento {index + 1} inválido em {simbolo_func.nome}")

            self.RestoParams(simbolo_func, params_formais, index + 1)