# sintatico.py
import sys
from lexico import Lexico
from ttoken import TOKEN
from semantico import Semantico
from tabela_de_simbolos import checar_atribuicao


class Sintatico:
    def __init__(self, lexico):
        self.lexico = lexico
        self.tokenLido = None
        self.semantico = Semantico()

    def analisa(self):
        self.tokenLido = self.lexico.prox_token()
        try:
            self.Program()
            self.consome(TOKEN.eof)
            return self.semantico.obter_codigo_final()  # Retorna o código Python
        except Exception as e:
            self.imprimir_erro_detalhado(e)
            return None

    def consome(self, token_esperado):
        token_atual = self.tokenLido
        if token_atual == token_esperado:
            self.tokenLido = self.lexico.prox_token()
        else:
            raise Exception(f"Esperado '{TOKEN.msg(token_esperado)}', mas encontrei '{TOKEN.msg(token_atual)}'.")

    def imprimir_erro_detalhado(self, erro):
        # Captura as informações atuais do léxico
        linha = self.lexico.token_linha
        lexema = self.lexico.lexema_atual
        txt_linha = "..."

        # Tenta pegar a linha exata do código fonte para mostrar o contexto
        try:
            if hasattr(self.lexico, 'buffer'):
                linhas_codigo = self.lexico.buffer.splitlines()
                # Ajusta índice (linha começa em 1, lista em 0)
                if 0 <= linha - 1 < len(linhas_codigo):
                    txt_linha = linhas_codigo[linha - 1].strip()
        except Exception:
            pass  # Se der erro ao pegar a linha, segue a vida

        print(f"\n🛑 ERRO (Linha {linha})")
        print("-" * 55)
        print(f"Descrição : {erro}")
        print(f"Contexto  : {txt_linha}")
        if lexema:
            print(f"Causador  : '{lexema}'")
        else:
            print(f"Causador  : (fim de arquivo ou token desconhecido)")
        print("-" * 55 + "\n")

    # --- GERAÇÃO DE CÓDIGO ---

    def Program(self):
        # 1. Gera cabeçalho padrão (simula stdlib do C em Python)
        self.semantico.gera(0, "import sys")
        self.semantico.gera(0, "")
        self.semantico.gera(0, "# --- Biblioteca Padrão Simulada ---")

        # --- FUNÇÕES DE SAÍDA ---
        self.semantico.gera(0, "def putint(x): print(x, end='')")
        self.semantico.gera(0, "def putfloat(x): print(x, end='')")
        self.semantico.gera(0, "def putstr(x): print(x, end='')")
        self.semantico.gera(0, "def putchar(x): print(x, end='')")

        # --- FUNÇÕES DE ENTRADA (O que faltava!) ---
        # Lê uma linha e converte para inteiro
        self.semantico.gera(0, "def getint(): return int(float(input()))")
        # Lê uma linha e converte para float
        self.semantico.gera(0, "def getfloat(): return float(input())")
        # Lê uma linha e pega o primeiro caractere (ou '\0' se vazio)
        self.semantico.gera(0, "def getchar(): return input()[0] if input() else '\\0'")

        self.semantico.gera(0, "")
        self.semantico.gera(0, "# --- Código do Usuário ---")

        tipos = [TOKEN.INT, TOKEN.FLOAT, TOKEN.CHAR]
        while self.tokenLido in tipos:
            self.Function()

        # Verifica Main e gera chamada de execução
        try:
            self.semantico.verificar_existencia('main')
            self.semantico.gera(0, "")
            self.semantico.gera(0, "if __name__ == '__main__':")
            self.semantico.gera(1, "main()")
        except:
            raise Exception("Função 'main' não encontrada.")

    def Function(self):
        tipo_ret = self.Type()
        nome = self.lexico.lexema_atual
        self.consome(TOKEN.ident)
        self.consome(TOKEN.abrePar)

        lista_params = self.ArgList()  # [{'nome':'x', 'tipo':...}]
        self.consome(TOKEN.fechaPar)

        self.semantico.declarar_funcao(nome, tipo_ret, lista_params)

        # Gera definição Python: def nome(p1, p2):
        nomes_params = [p['nome'] for p in lista_params]
        params_str = ", ".join(nomes_params)
        self.semantico.gera(0, f"def {nome}({params_str}):")

        self.semantico.entrar_escopo()
        for p in lista_params:
            self.semantico.declarar_parametro(p['nome'], p['tipo'])

        self.CompoundStmt(indent=1, is_func=True)
        self.semantico.sair_escopo()
        self.semantico.gera(0, "")  # Linha em branco após função

    def ArgList(self):
        params = []
        if self.tokenLido in [TOKEN.INT, TOKEN.FLOAT, TOKEN.CHAR]:
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
            self.consome(TOKEN.abreColch);
            self.consome(TOKEN.fechaColch)
            return True
        return False

    def CompoundStmt(self, indent, is_func=False):
        self.consome(TOKEN.abreChave)
        if not is_func: self.semantico.entrar_escopo()

        self.StmtList(indent)

        if not is_func: self.semantico.sair_escopo()
        self.consome(TOKEN.fechaChave)

    def StmtList(self, indent):
        first_stmt = [TOKEN.FOR, TOKEN.WHILE, TOKEN.IF, TOKEN.abreChave, TOKEN.BREAK,
                      TOKEN.CONTINUE, TOKEN.RETURN, TOKEN.ptoVirg, TOKEN.INT, TOKEN.FLOAT,
                      TOKEN.CHAR] + self.first_of_expr()
        while self.tokenLido in first_stmt:
            self.Stmt(indent)

    def Stmt(self, indent):
        tok = self.tokenLido

        if tok == TOKEN.FOR:
            self.ForStmt(indent)
        elif tok == TOKEN.WHILE:
            self.WhileStmt(indent)
        elif tok == TOKEN.IF:
            self.IfStmt(indent)
        elif tok == TOKEN.abreChave:
            self.CompoundStmt(indent)

        elif tok == TOKEN.BREAK:
            self.semantico.verificar_dentro_loop('break')
            self.consome(TOKEN.BREAK);
            self.consome(TOKEN.ptoVirg)
            self.semantico.gera(indent, "break")

        elif tok == TOKEN.CONTINUE:
            self.semantico.verificar_dentro_loop('continue')
            self.consome(TOKEN.CONTINUE);
            self.consome(TOKEN.ptoVirg)

            # --- TRUQUE DO GUSTAVO ---
            # Se for um FOR, precisamos rodar o incremento antes de pular
            incremento = self.semantico.pegar_incremento_atual()
            if incremento:
                self.semantico.gera(indent, incremento)

            self.semantico.gera(indent, "continue")

        elif tok == TOKEN.RETURN:
            self.consome(TOKEN.RETURN)
            t_expr = self.Expr()
            self.semantico.verificar_return(t_expr[0])
            self.consome(TOKEN.ptoVirg)
            self.semantico.gera(indent, f"return {t_expr[1]}")

        elif tok in [TOKEN.INT, TOKEN.FLOAT, TOKEN.CHAR]:
            self.Declaration(indent)
        elif tok == TOKEN.ptoVirg:
            self.consome(TOKEN.ptoVirg)
        else:
            t_expr = self.Expr()
            self.consome(TOKEN.ptoVirg)
            self.semantico.gera(indent, t_expr[1])

    def ForStmt(self, indent):
        self.consome(TOKEN.FOR)
        self.consome(TOKEN.abrePar)

        # 1. Inicialização (gera linha antes do loop)
        t_init = self.Expr()
        self.semantico.gera(indent, t_init[1])

        self.consome(TOKEN.ptoVirg)

        # 2. Condição
        t_cond = self.OptExpr()
        cond_str = t_cond[1] if t_cond[1] != "" else "True"

        self.consome(TOKEN.ptoVirg)

        # 3. Incremento (Guardamos a string, não geramos agora)
        t_incr = self.OptExpr()
        incr_str = t_incr[1]

        self.consome(TOKEN.fechaPar)

        # 4. Gera o WHILE simulando o FOR
        self.semantico.gera(indent, f"while {cond_str}:")

        # Registra no semântico que estamos num FOR e qual é o incremento
        self.semantico.entrar_loop('for', codigo_incremento=incr_str)

        self.Stmt(indent + 1)

        # Executa o incremento no final do laço
        if incr_str:
            self.semantico.gera(indent + 1, incr_str)

        self.semantico.sair_loop()

    def WhileStmt(self, indent):
        self.consome(TOKEN.WHILE)
        self.consome(TOKEN.abrePar)
        t_cond = self.Expr()
        self.consome(TOKEN.fechaPar)

        self.semantico.gera(indent, f"while {t_cond[1]}:")

        self.semantico.entrar_loop('while')  # While não tem incremento automático
        self.Stmt(indent + 1)
        self.semantico.sair_loop()

    def IfStmt(self, indent):
        self.consome(TOKEN.IF)
        self.consome(TOKEN.abrePar)
        t_cond = self.Expr()
        self.consome(TOKEN.fechaPar)

        self.semantico.gera(indent, f"if {t_cond[1]}:")
        self.Stmt(indent + 1)

        if self.tokenLido == TOKEN.ELSE:
            self.consome(TOKEN.ELSE)
            self.semantico.gera(indent, "else:")
            self.Stmt(indent + 1)

    def Declaration(self, indent):
        tipo_base = self.Type()
        self.IdentList(tipo_base, indent)
        self.consome(TOKEN.ptoVirg)

    def IdentList(self, tipo_base, indent):
        self.IdentDeclar(tipo_base, indent)
        if self.tokenLido == TOKEN.virg:
            self.consome(TOKEN.virg)
            self.IdentList(tipo_base, indent)

    def IdentDeclar(self, tipo_base, indent):
        nome = self.lexico.lexema_atual
        self.consome(TOKEN.ident)
        eh_array, tamanho = self.OpcIdentDeclar()  # Alterado para retornar tamanho

        # Inicializa a variável em Python para ela existir
        if eh_array:
            # Ex: v = [0] * 10
            self.semantico.gera(indent, f"{nome} = [0] * {tamanho}")
        else:
            # Ex: x = 0
            valor_init = "0.0" if tipo_base[0] == TOKEN.FLOAT else "0"
            self.semantico.gera(indent, f"{nome} = {valor_init}")

        self.semantico.declarar_variavel(nome, (tipo_base[0], eh_array))

    def OpcIdentDeclar(self):
        if self.tokenLido == TOKEN.abreColch:
            self.consome(TOKEN.abreColch)
            tam = self.lexico.lexema_atual
            self.consome(TOKEN.valorInt)
            self.consome(TOKEN.fechaColch)
            return True, tam
        return False, 0

    def Type(self):
        tok = self.tokenLido
        if tok in [TOKEN.INT, TOKEN.FLOAT, TOKEN.CHAR]:
            self.consome(tok)
            return (tok, False)
        raise Exception("Tipo esperado")

    # --- Expressões (Adaptando operadores para Python) ---

    def first_of_expr(self):
        return [TOKEN.ident, TOKEN.valorInt, TOKEN.valorFloat, TOKEN.valorChar, TOKEN.valorString,
                TOKEN.abrePar, TOKEN.mais, TOKEN.menos, TOKEN.NOT]

    def OptExpr(self):
        if self.tokenLido in self.first_of_expr(): return self.Expr()
        return ((TOKEN.INT, False), "")

    def Expr(self):
        t1 = self.Log()
        if self.tokenLido == TOKEN.atrib:
            self.consome(TOKEN.atrib)
            t2 = self.Expr()
            self.semantico.verificar_atribuicao(t1[0], t2[0])
            return (t1[0], f"{t1[1]} = {t2[1]}")
        return t1

    def Log(self):
        t1 = self.Nao()
        while self.tokenLido in [TOKEN.AND, TOKEN.OR]:
            op = self.tokenLido
            op_str = " and " if op == TOKEN.AND else " or "
            self.consome(op)
            t2 = self.Nao()
            tipo_res = self.semantico.calcular_binario(t1[0], op, t2[0])
            t1 = (tipo_res, f"{t1[1]}{op_str}{t2[1]}")
        return t1

    def Nao(self):
        if self.tokenLido == TOKEN.NOT:
            op = self.tokenLido
            self.consome(TOKEN.NOT)
            t = self.Rel()
            tipo_res = self.semantico.calcular_unario(op, t[0])
            return (tipo_res, f"not {t[1]}")
        return self.Rel()

    def Rel(self):
        t1 = self.Soma()
        if self.tokenLido == TOKEN.opRel:
            op = self.tokenLido
            op_lex = self.lexico.lexema_atual  # Pega >, <, ==
            self.consome(op)
            t2 = self.Soma()
            tipo_res = self.semantico.calcular_binario(t1[0], op, t2[0])
            t1 = (tipo_res, f"{t1[1]} {op_lex} {t2[1]}")
        return t1

    def Soma(self):
        t1 = self.Mult()
        while self.tokenLido in [TOKEN.mais, TOKEN.menos]:
            op = self.tokenLido
            op_lex = "+" if op == TOKEN.mais else "-"
            self.consome(op)
            t2 = self.Mult()
            tipo_res = self.semantico.calcular_binario(t1[0], op, t2[0])
            t1 = (tipo_res, f"{t1[1]} {op_lex} {t2[1]}")
        return t1

    def Mult(self):
        t1 = self.Uno()
        while self.tokenLido in [TOKEN.multiplica, TOKEN.divide, TOKEN.mod]:
            op = self.tokenLido
            op_lex = "*" if op == TOKEN.multiplica else "/" if op == TOKEN.divide else "%"
            self.consome(op)
            t2 = self.Uno()
            tipo_res = self.semantico.calcular_binario(t1[0], op, t2[0])
            # Se for divisão inteira em C, Python usa //? O Gustavo usa / normal
            if op == TOKEN.divide and t1[0] == (TOKEN.INT, False) and t2[0] == (TOKEN.INT, False):
                op_lex = "//"
            t1 = (tipo_res, f"{t1[1]} {op_lex} {t2[1]}")
        return t1

    def Uno(self):
        if self.tokenLido in [TOKEN.mais, TOKEN.menos]:
            op = self.tokenLido
            op_lex = "+" if op == TOKEN.mais else "-"
            self.consome(op)
            t = self.Uno()
            return (t[0], f"{op_lex}{t[1]}")
        return self.Folha()

    def Folha(self):
        tok = self.tokenLido
        lexema = self.lexico.lexema_atual

        if tok == TOKEN.abrePar:
            self.consome(TOKEN.abrePar)
            t = self.Expr()
            self.consome(TOKEN.fechaPar)
            return (t[0], f"({t[1]})")

        elif tok == TOKEN.ident:
            return self.Identifier()

        elif tok in [TOKEN.valorInt, TOKEN.valorFloat]:
            self.consome(tok)
            return ((TOKEN.INT if tok == TOKEN.valorInt else TOKEN.FLOAT, False), lexema)

        elif tok == TOKEN.valorChar:
            self.consome(tok)
            return ((TOKEN.CHAR, False), lexema)  # 'a'

        elif tok == TOKEN.valorString:
            self.consome(tok)
            return ((TOKEN.CHAR, True), lexema)  # "abc"

        else:
            raise Exception("Expressão inválida.")

    def Identifier(self):
        nome = self.lexico.lexema_atual
        simbolo = self.semantico.verificar_existencia(nome)
        self.consome(TOKEN.ident)
        return self.OpcIdentifier(simbolo, nome)

    def OpcIdentifier(self, simbolo, nome):
        token = self.tokenLido
        if token == TOKEN.abreColch:
            self.consome(TOKEN.abreColch)
            t_idx = self.Expr()
            self.consome(TOKEN.fechaColch)
            return ((simbolo.tipo[0], False), f"{nome}[{t_idx[1]}]")

        elif token == TOKEN.abrePar:
            self.consome(TOKEN.abrePar)
            cod_args = self.Params(simbolo)
            self.consome(TOKEN.fechaPar)
            return (simbolo.tipo, f"{nome}({cod_args})")

        return (simbolo.tipo, nome)

    def Params(self, simbolo_func):
        params_formais = simbolo_func.info_extras['params']
        codigos_args = []
        if self.tokenLido in self.first_of_expr():
            t_arg = self.Expr()
            codigos_args.append(t_arg[1])
            self.RestoParams(codigos_args)
        return ", ".join(codigos_args)

    def RestoParams(self, lista_codigos):
        if self.tokenLido == TOKEN.virg:
            self.consome(TOKEN.virg)
            t_arg = self.Expr()
            lista_codigos.append(t_arg[1])
            self.RestoParams(lista_codigos)