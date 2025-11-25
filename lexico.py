# lexico.py
import sys
from enum import Enum, auto
from ttoken import TOKEN


# Enumeração para controlar os estados do autômato
class Estado(Enum):
    INICIAL = auto()
    EM_IDENTIFICADOR = auto()
    EM_INTEIRO = auto()
    EM_FLOAT = auto()
    EM_STRING = auto()
    EM_CHAR = auto()
    EM_OP_MAIOR_MENOR = auto()
    EM_OP_IGUAL = auto()
    EM_OP_DIFERENTE = auto()
    EM_OP_AND = auto()
    EM_OP_OR = auto()
    EM_COMENTARIO = auto()


class Lexico:
    def __init__(self, nome_arquivo):
        try:
            with open(nome_arquivo, 'r', encoding='utf-8') as f:
                self.buffer = f.read()
        except IOError:
            print(f"Erro: Não foi possível abrir o arquivo '{nome_arquivo}'.")
            sys.exit(1)

        self.posicao = 0
        self.tamanho_buffer = len(self.buffer)
        self.lexema_atual = ''
        self.token_linha = 1
        self.token_coluna = 1
        self._linha = 1
        self._coluna = 1

    def _proximo_char(self):
        if self.posicao >= self.tamanho_buffer:
            return '\0'
        char = self.buffer[self.posicao]
        self.posicao += 1
        if char == '\n':
            self._linha += 1
            self._coluna = 1
        else:
            self._coluna += 1
        return char

    def _devolver_char(self):
        if self.posicao > 0:
            self.posicao -= 1
            # Nota: Retroceder linha/coluna não é preciso aqui pois a
            # posição de início do token (token_linha) já foi salva.

    def prox_token(self):
        estado = Estado.INICIAL
        lexema_local = []

        while True:
            # Guarda a posição no início de cada token
            if not lexema_local:
                self.token_linha = self._linha
                self.token_coluna = self._coluna

            char = self._proximo_char()

            # --- ESTADO INICIAL ---
            if estado == Estado.INICIAL:
                # Ignora espaços em branco
                if char in ' \t\r\n':
                    continue

                lexema_local.append(char)

                if char.isalpha() or char == '_':
                    estado = Estado.EM_IDENTIFICADOR
                elif char.isdigit():
                    estado = Estado.EM_INTEIRO
                elif char == "'":
                    estado = Estado.EM_CHAR
                elif char == '"':
                    estado = Estado.EM_STRING
                elif char in ['<', '>']:
                    estado = Estado.EM_OP_MAIOR_MENOR
                elif char == '=':
                    estado = Estado.EM_OP_IGUAL
                elif char == '!':
                    estado = Estado.EM_OP_DIFERENTE
                elif char == '&':
                    estado = Estado.EM_OP_AND
                elif char == '|':
                    estado = Estado.EM_OP_OR
                elif char == '/':
                    proximo = self._proximo_char()
                    if proximo == '/':
                        lexema_local = []
                        estado = Estado.EM_COMENTARIO
                    else:
                        self._devolver_char()
                        self.lexema_atual = '/'
                        return TOKEN.divide
                elif char == '+':
                    self.lexema_atual = '+';
                    return TOKEN.mais
                elif char == '-':
                    self.lexema_atual = '-';
                    return TOKEN.menos
                elif char == '*':
                    self.lexema_atual = '*';
                    return TOKEN.multiplica
                elif char == '%':
                    self.lexema_atual = '%';
                    return TOKEN.mod
                elif char == '(':
                    self.lexema_atual = '(';
                    return TOKEN.abrePar
                elif char == ')':
                    self.lexema_atual = ')';
                    return TOKEN.fechaPar
                elif char == '{':
                    self.lexema_atual = '{';
                    return TOKEN.abreChave
                elif char == '}':
                    self.lexema_atual = '}';
                    return TOKEN.fechaChave
                elif char == '[':
                    self.lexema_atual = '[';
                    return TOKEN.abreColch
                elif char == ']':
                    self.lexema_atual = ']';
                    return TOKEN.fechaColch
                elif char == ',':
                    self.lexema_atual = ',';
                    return TOKEN.virg
                elif char == ';':
                    self.lexema_atual = ';';
                    return TOKEN.ptoVirg
                elif char == '\0':
                    self.lexema_atual = '<eof>';
                    return TOKEN.eof
                else:
                    self.lexema_atual = char;
                    return TOKEN.erro

            # --- ESTADO DE COMENTÁRIO ---
            elif estado == Estado.EM_COMENTARIO:
                if char in ['\n', '\0']:
                    estado = Estado.INICIAL
                continue

            # --- IDENTIFICADOR ---
            elif estado == Estado.EM_IDENTIFICADOR:
                if char.isalnum() or char == '_':
                    lexema_local.append(char)
                else:
                    self._devolver_char()
                    self.lexema_atual = "".join(lexema_local)
                    return TOKEN.reservada(self.lexema_atual)

            # --- NÚMEROS (INT / FLOAT) ---
            elif estado == Estado.EM_INTEIRO:
                if char.isdigit():
                    lexema_local.append(char)
                elif char == '.':
                    lexema_local.append(char)
                    estado = Estado.EM_FLOAT
                elif char.isalpha():  # Erro léxico: 9var
                    lexema_local.append(char)
                    self.lexema_atual = "".join(lexema_local)
                    return TOKEN.erro
                else:
                    self._devolver_char()
                    self.lexema_atual = "".join(lexema_local)
                    return TOKEN.valorInt

            elif estado == Estado.EM_FLOAT:
                if char.isdigit():
                    lexema_local.append(char)
                else:
                    self._devolver_char()
                    self.lexema_atual = "".join(lexema_local)
                    if self.lexema_atual.endswith('.'): return TOKEN.erro
                    return TOKEN.valorFloat

            # --- STRING ---
            elif estado == Estado.EM_STRING:
                lexema_local.append(char)
                if char == '"':
                    self.lexema_atual = "".join(lexema_local)
                    return TOKEN.valorString
                if char == '\0': return TOKEN.erro

            # --- CHAR (CORRIGIDO) ---
            elif estado == Estado.EM_CHAR:
                # O 'char' atual é o conteúdo (ex: 'a' ou '\')

                # 1. Trata o conteúdo
                if char == '\\':  # Escape (ex: \n)
                    lexema_local.append(char)
                    escapado = self._proximo_char()
                    lexema_local.append(escapado)
                elif char != "'":  # Normal (ex: a)
                    lexema_local.append(char)
                else:
                    # Se veio aspa logo de cara ('') é erro ou vazio inválido
                    self.lexema_atual = "".join(lexema_local)
                    return TOKEN.erro

                # 2. Verifica fechamento obrigatório
                fechamento = self._proximo_char()
                if fechamento == "'":
                    lexema_local.append("'")
                    self.lexema_atual = "".join(lexema_local)
                    return TOKEN.valorChar
                else:
                    # Se não fechou (ex: 'ab), é erro
                    self.lexema_atual = "".join(lexema_local)
                    return TOKEN.erro

            # --- OPERADORES ---
            elif estado in [Estado.EM_OP_MAIOR_MENOR, Estado.EM_OP_IGUAL, Estado.EM_OP_DIFERENTE]:
                if char == '=':
                    lexema_local.append(char)
                    self.lexema_atual = "".join(lexema_local)
                    return TOKEN.opRel
                else:
                    self._devolver_char()
                    self.lexema_atual = "".join(lexema_local)
                    if estado == Estado.EM_OP_IGUAL: return TOKEN.atrib
                    if estado == Estado.EM_OP_DIFERENTE: return TOKEN.NOT
                    return TOKEN.opRel

            elif estado == Estado.EM_OP_AND:
                if char == '&':
                    lexema_local.append(char)
                    self.lexema_atual = "".join(lexema_local)
                    return TOKEN.AND
                else:
                    return TOKEN.erro

            elif estado == Estado.EM_OP_OR:
                if char == '|':
                    lexema_local.append(char)
                    self.lexema_atual = "".join(lexema_local)
                    return TOKEN.OR
                else:
                    return TOKEN.erro