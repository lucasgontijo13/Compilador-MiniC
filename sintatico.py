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
            print('\n---------------------------------------------------')
            print('✅ Sucesso Total! Código aceito.')
            print('---------------------------------------------------')
        except Exception as e:
            self.imprimir_erro_detalhado(e)

    def imprimir_erro_detalhado(self, erro):
        linha = self.lexico.token_linha
        lexema = self.lexico.lexema_atual
        txt_linha = "..."
        try:
            linhas_codigo = self.lexico.buffer.splitlines()
            if 0 <= linha - 1 < len(linhas_codigo):
                txt_linha = linhas_codigo[linha - 1].strip()
        except:
            pass
        print(f"\n🛑 ERRO (Linha {linha})")
        print("-" * 55)
        print(f"Descrição : {erro}")
        print(f"Contexto  : {txt_linha}")
        if lexema: print(f"Causador  : '{lexema}'")
        print("-" * 55 + "\n")

    def consome(self, token_esperado):
        token_atual = self.tokenLido
        if token_atual == token_esperado:
            self.tokenLido = self.lexico.prox_token()
        else:
            raise Exception(f"Esperado '{TOKEN.msg(token_esperado)}', mas encontrei '{TOKEN.msg(token_atual)}'.")

    # --- ESTRUTURA ---

    def Program(self):
        tipos = [TOKEN.INT, TOKEN.FLOAT, TOKEN.CHAR]
        while self.tokenLido in tipos:
            self.Function()
        try:
            self.semantico.verificar_existencia('main')
        except:
            raise Exception("Função 'main' não encontrada.")

    def Function(self):
        tipo_ret = self.Type()
        nome = self.lexico.lexema_atual
        self.consome(TOKEN.ident)
        self.consome(TOKEN.abrePar)

        lista_params = self.ArgList()  # [{'nome': 'x', 'tipo': ...}]

        self.consome(TOKEN.fechaPar)

        self.semantico.declarar_funcao(nome, tipo_ret, lista_params)
        self.semantico.entrar_escopo()
        for p in lista_params:
            self.semantico.declarar_parametro(p['nome'], p['tipo'])

        self.CompoundStmt(is_func=True)
        self.semantico.sair_escopo()

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

    def CompoundStmt(self, is_func=False):
        self.consome(TOKEN.abreChave)
        if not is_func: self.semantico.entrar_escopo()
        self.StmtList()
        if not is_func: self.semantico.sair_escopo()
        self.consome(TOKEN.fechaChave)

    def StmtList(self):
        # First de Stmt + Expr
        while self.tokenLido in [TOKEN.FOR, TOKEN.WHILE, TOKEN.IF, TOKEN.abreChave, TOKEN.BREAK,
                                 TOKEN.CONTINUE, TOKEN.RETURN, TOKEN.ptoVirg, TOKEN.INT, TOKEN.FLOAT, TOKEN.CHAR] + \
                self.first_of_expr():
            self.Stmt()

    def Stmt(self):
        tok = self.tokenLido
        if tok == TOKEN.FOR:
            self.ForStmt()
        elif tok == TOKEN.WHILE:
            self.WhileStmt()
        elif tok == TOKEN.IF:
            self.IfStmt()
        elif tok == TOKEN.abreChave:
            self.CompoundStmt()
        elif tok == TOKEN.BREAK:
            self.semantico.verificar_break_continue()
            self.consome(TOKEN.BREAK);
            self.consome(TOKEN.ptoVirg)
        elif tok == TOKEN.CONTINUE:
            self.semantico.verificar_break_continue()
            self.consome(TOKEN.CONTINUE);
            self.consome(TOKEN.ptoVirg)
        elif tok == TOKEN.RETURN:
            self.consome(TOKEN.RETURN)
            t_expr = self.Expr()  # (tipo, codigo, cat)
            self.semantico.verificar_return(t_expr[0])  # Passa só o TIPO
            self.consome(TOKEN.ptoVirg)
        elif tok in [TOKEN.INT, TOKEN.FLOAT, TOKEN.CHAR]:
            self.Declaration()
        elif tok == TOKEN.ptoVirg:
            self.consome(TOKEN.ptoVirg)
        else:
            self.Expr()
            self.consome(TOKEN.ptoVirg)

    def ForStmt(self):
        self.consome(TOKEN.FOR);
        self.semantico.entrar_loop();
        self.consome(TOKEN.abrePar)
        self.Expr();
        self.consome(TOKEN.ptoVirg)
        self.OptExpr();
        self.consome(TOKEN.ptoVirg)
        self.OptExpr();
        self.consome(TOKEN.fechaPar)
        self.Stmt();
        self.semantico.sair_loop()

    def WhileStmt(self):
        self.consome(TOKEN.WHILE);
        self.semantico.entrar_loop();
        self.consome(TOKEN.abrePar)
        self.Expr();
        self.consome(TOKEN.fechaPar)
        self.Stmt();
        self.semantico.sair_loop()

    def IfStmt(self):
        self.consome(TOKEN.IF);
        self.consome(TOKEN.abrePar)
        self.Expr();
        self.consome(TOKEN.fechaPar)
        self.Stmt()
        if self.tokenLido == TOKEN.ELSE:
            self.consome(TOKEN.ELSE);
            self.Stmt()

    def Declaration(self):
        tipo_base = self.Type()
        self.IdentList(tipo_base)
        self.consome(TOKEN.ptoVirg)

    def IdentList(self, tipo_base):
        self.IdentDeclar(tipo_base)
        if self.tokenLido == TOKEN.virg:
            self.consome(TOKEN.virg)
            self.IdentList(tipo_base)  # Recursão simplificada

    def IdentDeclar(self, tipo_base):
        nome = self.lexico.lexema_atual
        self.consome(TOKEN.ident)

        eh_array = self.OpcIdentDeclar()
        tipo_final = (tipo_base[0], eh_array)

        self.semantico.declarar_variavel(nome, tipo_final)



    def OpcIdentDeclar(self):
        if self.tokenLido == TOKEN.abreColch:
            self.consome(TOKEN.abreColch);
            self.consome(TOKEN.valorInt);
            self.consome(TOKEN.fechaColch)
            return True
        return False

    def Type(self):
        tok = self.tokenLido
        if tok in [TOKEN.INT, TOKEN.FLOAT, TOKEN.CHAR]:
            self.consome(tok)
            return (tok, False)
        raise Exception("Esperado tipo (int, float, char)")

    def OptExpr(self):
        if self.tokenLido in self.first_of_expr(): return self.Expr()
        return ((TOKEN.INT, False), "", "vazio")

    # --- EXPRESSÕES (Retornam TUPLA: (Tipo, Codigo, Categoria)) ---

    def first_of_expr(self):
        return [TOKEN.ident, TOKEN.valorInt, TOKEN.valorFloat, TOKEN.valorChar, TOKEN.valorString,
                TOKEN.abrePar, TOKEN.mais, TOKEN.menos, TOKEN.NOT]

    def Expr(self):
        t1 = self.Log()
        if self.tokenLido == TOKEN.atrib:
            self.consome(TOKEN.atrib)
            t2 = self.Expr()
            # t1 e t2 são tuplas. Validamos tipos: t1[0] e t2[0]
            self.semantico.verificar_atribuicao(t1[0], t2[0])
            # Retorna o tipo do lado esquerdo, e o código da atribuição
            return (t1[0], f"{t1[1]} = {t2[1]}", "atribuicao")
        return t1

    def Log(self):
        t1 = self.Nao()
        while self.tokenLido in [TOKEN.AND, TOKEN.OR]:
            op = self.tokenLido;
            self.consome(op)
            t2 = self.Nao()
            # Calcula tipo resultante
            tipo_res = self.semantico.calcular_binario(t1[0], op, t2[0])
            # Gera código intermediário (ex: "x && y")
            novo_cod = f"{t1[1]} {TOKEN.msg(op)} {t2[1]}"
            t1 = (tipo_res, novo_cod, "logica")
        return t1

    def Nao(self):
        if self.tokenLido == TOKEN.NOT:
            op = self.tokenLido;
            self.consome(TOKEN.NOT)
            t = self.Rel()
            tipo_res = self.semantico.calcular_unario(op, t[0])
            return (tipo_res, f"!{t[1]}", "unario")
        return self.Rel()

    def Rel(self):
        t1 = self.Soma()
        if self.tokenLido == TOKEN.opRel:
            op = self.tokenLido;
            self.consome(op)
            t2 = self.Soma()
            tipo_res = self.semantico.calcular_binario(t1[0], op, t2[0])
            t1 = (tipo_res, f"{t1[1]} {TOKEN.msg(op)} {t2[1]}", "relacional")
        return t1

    def Soma(self):
        t1 = self.Mult()
        while self.tokenLido in [TOKEN.mais, TOKEN.menos]:
            op = self.tokenLido;
            self.consome(op)
            t2 = self.Mult()
            tipo_res = self.semantico.calcular_binario(t1[0], op, t2[0])
            t1 = (tipo_res, f"{t1[1]} {TOKEN.msg(op)} {t2[1]}", "aritmetica")
        return t1

    def Mult(self):
        t1 = self.Uno()
        while self.tokenLido in [TOKEN.multiplica, TOKEN.divide, TOKEN.mod]:
            op = self.tokenLido;
            self.consome(op)
            t2 = self.Uno()
            tipo_res = self.semantico.calcular_binario(t1[0], op, t2[0])
            t1 = (tipo_res, f"{t1[1]} {TOKEN.msg(op)} {t2[1]}", "aritmetica")
        return t1

    def Uno(self):
        if self.tokenLido in [TOKEN.mais, TOKEN.menos]:
            op = self.tokenLido;
            self.consome(op)
            t = self.Uno()
            tipo_res = self.semantico.calcular_unario(op, t[0])
            return (tipo_res, f"{TOKEN.msg(op)}{t[1]}", "unario")
        return self.Folha()

    def Folha(self):
        # Retorna: ((TIPO, IsArr), "Lexema", "Categoria")
        tok = self.tokenLido
        lexema = self.lexico.lexema_atual

        if tok == TOKEN.abrePar:
            self.consome(TOKEN.abrePar);
            t = self.Expr();
            self.consome(TOKEN.fechaPar)
            return (t[0], f"({t[1]})", "parenteses")

        elif tok == TOKEN.ident:
            return self.Identifier()

        elif tok == TOKEN.valorInt:
            self.consome(tok)
            return ((TOKEN.INT, False), lexema, "literal")
        elif tok == TOKEN.valorFloat:
            self.consome(tok)
            return ((TOKEN.FLOAT, False), lexema, "literal")
        elif tok == TOKEN.valorChar:
            self.consome(tok)
            return ((TOKEN.CHAR, False), lexema, "literal")
        elif tok == TOKEN.valorString:
            self.consome(tok)
            return ((TOKEN.CHAR, True), lexema, "literal")
        else:
            raise Exception("Expressão inválida.")

    def Identifier(self):
        nome = self.lexico.lexema_atual
        simbolo = self.semantico.verificar_existencia(nome)
        self.consome(TOKEN.ident)

        # Passamos o SÍMBOLO e o NOME para gerar o código correto
        return self.OpcIdentifier(simbolo, nome)

    def OpcIdentifier(self, simbolo, nome):
        token = self.tokenLido

        # Array: v[i]
        if token == TOKEN.abreColch:
            if not simbolo.tipo[1]:  # Se não é array
                raise Exception(f"Erro Semântico: '{simbolo.nome}' não é array.")

            self.consome(TOKEN.abreColch)

            # Expr retorna ((TIPO, IsArr), Codigo, Cat)
            t_idx = self.Expr()

            # Extraímos a tupla de tipo: (TOKEN.INT, False)
            tipo_indice = t_idx[0]

            # Verificamos:
            # 1. Se o tipo primitivo (tipo_indice[0]) não é INT nem CHAR
            # 2. OU se é um array (tipo_indice[1] é True)
            if tipo_indice[0] not in [TOKEN.INT, TOKEN.CHAR] or tipo_indice[1]:
                raise Exception("Erro Semântico: Índice deve ser inteiro.")

            self.consome(TOKEN.fechaColch)

            # Retorna o elemento acessado. Ex: vetor[1]
            return ((simbolo.tipo[0], False), f"{nome}[{t_idx[1]}]", "acesso_array")

        # Função: f(x)
        elif token == TOKEN.abrePar:
            if simbolo.categoria != 'funcao':
                raise Exception(f"Erro Semântico: '{simbolo.nome}' não é função.")

            self.consome(TOKEN.abrePar)
            cod_args = self.Params(simbolo)
            self.consome(TOKEN.fechaPar)
            return (simbolo.tipo, f"{nome}({cod_args})", "chamada_func")

        # Variável simples
        return (simbolo.tipo, nome, "variavel")

    def Params(self, simbolo_func):
        params_formais = simbolo_func.info_extras['params']
        codigos_args = []

        if self.tokenLido in self.first_of_expr():
            if len(params_formais) < 1: raise Exception("Excesso de argumentos.")

            t_arg = self.Expr()  # (tipo, cod, cat)
            if not checar_atribuicao(params_formais[0], t_arg[0]): raise Exception("Tipo arg 1 inválido.")
            codigos_args.append(t_arg[1])

            self.RestoParams(simbolo_func, params_formais, 1, codigos_args)
        elif len(params_formais) > 0:
            raise Exception("Faltam argumentos.")

        return ", ".join(codigos_args)

    def RestoParams(self, simbolo_func, params_formais, index, lista_codigos):
        if self.tokenLido == TOKEN.virg:
            self.consome(TOKEN.virg)
            if index >= len(params_formais):
                raise Exception(f"Excesso de argumentos em '{simbolo_func.nome}'.")

            t_arg = self.Expr()
            if not checar_atribuicao(params_formais[index], t_arg[0]):
                raise Exception(f"Tipo do argumento {index + 1} inválido em '{simbolo_func.nome}'.")

            lista_codigos.append(t_arg[1])

            self.RestoParams(simbolo_func, params_formais, index + 1, lista_codigos)
        else:
            if index < len(params_formais):
                raise Exception(
                    f"Faltam argumentos em '{simbolo_func.nome}'. Esperado {len(params_formais)}, recebeu {index}.")