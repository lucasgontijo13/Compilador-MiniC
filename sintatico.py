# sintatico.py
# Analisador Sintático COMPLETO para a linguagem Mini-C.

import sys
from lexico import Lexico
from ttoken import TOKEN


class Sintatico:
    def __init__(self, nomeArquivo):
        self.lexico = Lexico(nomeArquivo)
        self.tokenLido = None

    def analisa(self):
        self.tokenLido = self.lexico.proxToken()
        try:
            self.Program()
            self.consome(TOKEN.eof)
            print('\nAnálise sintática concluída com sucesso.')
        except Exception as e:
            print(f'\n[ANÁLISE INTERROMPIDA] {e}')

    def consome(self, token_esperado):
        (token_val, lexema, linha, col) = self.tokenLido
        if token_val == token_esperado:
            self.tokenLido = self.lexico.proxToken()
        else:
            msg_recebida = f"'{lexema}' ({TOKEN.msg(token_val)})"
            msg_esperada = f"'{TOKEN.msg(token_esperado)}'"
            raise Exception(
                f'Erro Sintático na Linha {linha}, Coluna {col}: Esperado {msg_esperada}, mas foi recebido {msg_recebida}.')

    def Program(self):
        tipos = [TOKEN.INT, TOKEN.FLOAT, TOKEN.CHAR]
        while self.tokenLido[0] in tipos:
            self.Function()

    def Function(self):
        self.Type();
        self.consome(TOKEN.ident);
        self.consome(TOKEN.abrePar)
        self.ArgList();
        self.consome(TOKEN.fechaPar);
        self.CompoundStmt()

    def ArgList(self):
        tipos = [TOKEN.INT, TOKEN.FLOAT, TOKEN.CHAR]
        if self.tokenLido[0] in tipos:
            self.Arg();
            self.RestoArgList()

    def RestoArgList(self):
        if self.tokenLido[0] == TOKEN.virg:
            self.consome(TOKEN.virg);
            self.Arg();
            self.RestoArgList()

    def Arg(self):
        self.Type(); self.IdentArg()

    def IdentArg(self):
        self.consome(TOKEN.ident); self.OpcIdentArg()

    def OpcIdentArg(self):
        if self.tokenLido[0] == TOKEN.abreColch:
            self.consome(TOKEN.abreColch);
            self.consome(TOKEN.fechaColch)

    def CompoundStmt(self):
        self.consome(TOKEN.abreChave);
        self.StmtList();
        self.consome(TOKEN.fechaChave)

    def StmtList(self):
        first_stmt = [TOKEN.FOR, TOKEN.WHILE, TOKEN.IF, TOKEN.abreChave, TOKEN.BREAK, TOKEN.CONTINUE, TOKEN.RETURN,
                      TOKEN.ptoVirg] + self.first_of_expr() + [TOKEN.INT, TOKEN.FLOAT, TOKEN.CHAR]
        while self.tokenLido[0] in first_stmt:
            self.Stmt()

    def Stmt(self):
        token = self.tokenLido[0]
        if token == TOKEN.FOR:
            self.ForStmt()
        elif token == TOKEN.WHILE:
            self.WhileStmt()
        elif token == TOKEN.IF:
            self.IfStmt()
        elif token == TOKEN.abreChave:
            self.CompoundStmt()
        elif token == TOKEN.BREAK:
            self.consome(TOKEN.BREAK); self.consome(TOKEN.ptoVirg)
        elif token == TOKEN.CONTINUE:
            self.consome(TOKEN.CONTINUE); self.consome(TOKEN.ptoVirg)
        elif token == TOKEN.RETURN:
            self.consome(TOKEN.RETURN); self.Expr(); self.consome(TOKEN.ptoVirg)
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
        self.OptExpr();
        self.consome(TOKEN.ptoVirg)
        self.OptExpr();
        self.consome(TOKEN.fechaPar);
        self.Stmt()

    def OptExpr(self):
        if self.tokenLido[0] in self.first_of_expr(): self.Expr()

    def WhileStmt(self):
        self.consome(TOKEN.WHILE);
        self.consome(TOKEN.abrePar);
        self.Expr();
        self.consome(TOKEN.fechaPar);
        self.Stmt()

    def IfStmt(self):
        self.consome(TOKEN.IF);
        self.consome(TOKEN.abrePar);
        self.Expr();
        self.consome(TOKEN.fechaPar);
        self.Stmt();
        self.ElsePart()

    def ElsePart(self):
        if self.tokenLido[0] == TOKEN.ELSE: self.consome(TOKEN.ELSE); self.Stmt()

    def Declaration(self):
        self.Type();
        self.IdentList();
        self.consome(TOKEN.ptoVirg)

    def Type(self):
        token = self.tokenLido[0]
        if token in [TOKEN.INT, TOKEN.FLOAT, TOKEN.CHAR]:
            self.consome(token)
        else:
            raise Exception(f"Erro: Tipo (int, float, char) esperado na linha {self.tokenLido[2]}")

    def IdentList(self):
        self.IdentDeclar(); self.RestoIdentList()

    def RestoIdentList(self):
        if self.tokenLido[0] == TOKEN.virg: self.consome(TOKEN.virg); self.IdentDeclar(); self.RestoIdentList()

    def IdentDeclar(self):
        self.consome(TOKEN.ident); self.OpcIdentDeclar()

    def OpcIdentDeclar(self):
        if self.tokenLido[0] == TOKEN.abreColch:
            self.consome(TOKEN.abreColch);
            self.consome(TOKEN.valorInt);
            self.consome(TOKEN.fechaColch)

    # --- NOVA ANÁLISE DE EXPRESSÃO (ESTILO ITERATIVO) ---

    def first_of_expr(self):  # Helper para saber se um token pode iniciar uma expressão
        return [TOKEN.ident, TOKEN.valorInt, TOKEN.valorFloat, TOKEN.valorChar, TOKEN.valorString,
                TOKEN.abrePar, TOKEN.mais, TOKEN.menos, TOKEN.NOT]

    def Expr(self):  # Expr -> Log [ = Expr ]
        self.Log()
        if self.tokenLido[0] == TOKEN.atrib:
            self.consome(TOKEN.atrib);
            self.Expr()

    def Log(self):  # Log -> Nao { (&& | ||) Nao }
        self.Nao()
        while self.tokenLido[0] in [TOKEN.AND, TOKEN.OR]:
            self.consome(self.tokenLido[0]);
            self.Nao()

    def Nao(self):  # Nao -> [!] Rel
        if self.tokenLido[0] == TOKEN.NOT: self.consome(TOKEN.NOT)
        self.Rel()

    def Rel(self):  # Rel -> Soma [ opRel Soma ]
        self.Soma()
        if self.tokenLido[0] == TOKEN.opRel:
            self.consome(TOKEN.opRel);
            self.Soma()

    def Soma(self):  # Soma -> Mult { (+|-) Mult }
        self.Mult()
        while self.tokenLido[0] in [TOKEN.mais, TOKEN.menos]:
            self.consome(self.tokenLido[0]);
            self.Mult()

    def Mult(self):  # Mult -> Uno { (*|/|%) Uno }
        self.Uno()
        while self.tokenLido[0] in [TOKEN.multiplica, TOKEN.divide, TOKEN.mod]:
            self.consome(self.tokenLido[0]);
            self.Uno()

    def Uno(self):  # Uno -> (+|-) Uno | Folha
        if self.tokenLido[0] in [TOKEN.mais, TOKEN.menos]:
            self.consome(self.tokenLido[0]);
            self.Uno()
        else:
            self.Folha()

    def Folha(self):  # Folha -> ( Expr ) | Identifier | valorInt | valorFloat | valorChar | valorString
        token = self.tokenLido[0]
        if token == TOKEN.abrePar:
            self.consome(TOKEN.abrePar); self.Expr(); self.consome(TOKEN.fechaPar)
        elif token == TOKEN.ident:
            self.Identifier()
        elif token in [TOKEN.valorInt, TOKEN.valorFloat, TOKEN.valorChar, TOKEN.valorString]:
            self.consome(token)
        else:
            raise Exception(
                f"Erro: Expressão esperada (ident, número ou '('), mas veio '{self.tokenLido[1]}' na linha {self.tokenLido[2]}")

    def Identifier(self):  # Identifier -> ident OpcIdentifier
        self.consome(TOKEN.ident);
        self.OpcIdentifier()

    def OpcIdentifier(self):  # OpcIdentifier -> [ Expr ] | ( Params ) | LAMBDA
        token = self.tokenLido[0]
        if token == TOKEN.abreColch:
            self.consome(TOKEN.abreColch); self.Expr(); self.consome(TOKEN.fechaColch)
        elif token == TOKEN.abrePar:
            self.consome(TOKEN.abrePar); self.Params(); self.consome(TOKEN.fechaPar)

    def Params(self):  # Params -> Expr RestoParams | LAMBDA
        if self.tokenLido[0] in self.first_of_expr(): self.Expr(); self.RestoParams()

    def RestoParams(self):  # RestoParams -> , Expr RestoParams | LAMBDA
        if self.tokenLido[0] == TOKEN.virg: self.consome(TOKEN.virg); self.Expr(); self.RestoParams()