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
            # Desfaz o avanço do ponteiro
            self.posicao -= 1
            # Importante: A lógica de voltar linha/coluna não é trivial,
            # mas para a máquina de estados, o importante é que o caractere
            # correto será lido na próxima iteração.
            # O ponto de início do token já foi salvo.

    def prox_token(self):
        estado = Estado.INICIAL
        lexema_local = []

        while True:
            # Guarda a posição no início de cada token potencial
            if not lexema_local:
                self.token_linha = self._linha
                self.token_coluna = self._coluna

            char = self._proximo_char()

            # --- ESTADO INICIAL: Ponto de partida e filtro de espaços/comentários ---
            if estado == Estado.INICIAL:
                # CORREÇÃO: Ignora brancos e comentários DENTRO do estado inicial
                if char in ' \t\r\n':
                    # Reseta a posição de início do token, pois estamos apenas pulando
                    self.token_linha = self._linha
                    self.token_coluna = self._coluna
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
                        lexema_local = []  # Descarta a barra inicial do comentário
                        estado = Estado.EM_COMENTARIO
                    else:
                        self._devolver_char()
                        self.lexema_atual = '/'
                        return TOKEN.divide
                elif char == '+':
                    self.lexema_atual = '+'; return TOKEN.mais
                elif char == '-':
                    self.lexema_atual = '-'; return TOKEN.menos
                elif char == '*':
                    self.lexema_atual = '*'; return TOKEN.multiplica
                elif char == '%':
                    self.lexema_atual = '%'; return TOKEN.mod
                elif char == '(':
                    self.lexema_atual = '('; return TOKEN.abrePar
                elif char == ')':
                    self.lexema_atual = ')'; return TOKEN.fechaPar
                elif char == '{':
                    self.lexema_atual = '{'; return TOKEN.abreChave
                elif char == '}':
                    self.lexema_atual = '}'; return TOKEN.fechaChave
                elif char == '[':
                    self.lexema_atual = '['; return TOKEN.abreColch
                elif char == ']':
                    self.lexema_atual = ']'; return TOKEN.fechaColch
                elif char == ',':
                    self.lexema_atual = ','; return TOKEN.virg
                elif char == ';':
                    self.lexema_atual = ';'; return TOKEN.ptoVirg
                elif char == '\0':
                    self.lexema_atual = '<eof>'; return TOKEN.eof
                else:
                    self.lexema_atual = char; return TOKEN.erro

            # --- ESTADO DE COMENTÁRIO ---
            elif estado == Estado.EM_COMENTARIO:
                if char in ['\n', '\0']:
                    estado = Estado.INICIAL  # Volta ao estado inicial para procurar o próximo token
                continue  # Continua consumindo caracteres do comentário

            # --- OUTROS ESTADOS ---

            elif estado == Estado.EM_IDENTIFICADOR:
                if char.isalnum() or char == '_':
                    lexema_local.append(char)
                else:
                    self._devolver_char()
                    self.lexema_atual = "".join(lexema_local)
                    return TOKEN.reservada(self.lexema_atual)

            elif estado == Estado.EM_INTEIRO:
                if char.isdigit():
                    lexema_local.append(char)
                elif char == '.':
                    lexema_local.append(char)
                    estado = Estado.EM_FLOAT
                # CORREÇÃO: Trata erro "9var"
                elif char.isalpha():
                    lexema_local.append(char)
                    while True:
                        proximo = self._proximo_char()
                        if proximo.isalnum():
                            lexema_local.append(proximo)
                        else:
                            self._devolver_char()
                            break
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
                    # CORREÇÃO: Trata erro "3."
                    if self.lexema_atual.endswith('.'):
                        return TOKEN.erro
                    return TOKEN.valorFloat

            elif estado == Estado.EM_STRING:
                lexema_local.append(char)
                if char == '"':
                    self.lexema_atual = "".join(lexema_local)
                    return TOKEN.valorString
                # CORREÇÃO: Finaliza corretamente string não terminada no fim do arquivo
                if char == '\0':
                    self.lexema_atual = "".join(lexema_local[:-1])  # Remove o \0 do lexema
                    return TOKEN.erro

            elif estado == Estado.EM_CHAR:
                # CORREÇÃO: Lógica mais robusta para validar char
                conteudo = []
                # Consome o conteúdo
                if char == '\\':  # Sequência de escape
                    conteudo.append(char)
                    conteudo.append(self._proximo_char())
                else:
                    # Consome até encontrar o fechamento ou erro
                    temp_char = char
                    while temp_char != "'" and temp_char not in ['\n', '\0']:
                        conteudo.append(temp_char)
                        temp_char = self._proximo_char()
                    char = temp_char  # Atualiza o char para o que finalizou o loop

                lexema_local.extend(conteudo)

                if char == "'":
                    lexema_local.append(char)
                    self.lexema_atual = "".join(lexema_local)
                    # Valida o tamanho do conteúdo
                    if len(conteudo) == 1 or (len(conteudo) == 2 and conteudo[0] == '\\'):
                        return TOKEN.valorChar

                # Se chegou aqui, é erro (não fechou ou tamanho inválido)
                self.lexema_atual = "".join(lexema_local)
                return TOKEN.erro

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
                    self._devolver_char()
                    self.lexema_atual = "".join(lexema_local)
                    return TOKEN.erro

            elif estado == Estado.EM_OP_OR:
                if char == '|':
                    lexema_local.append(char)
                    self.lexema_atual = "".join(lexema_local)
                    return TOKEN.OR
                else:
                    self._devolver_char()
                    self.lexema_atual = "".join(lexema_local)
                    return TOKEN.erro


# Bloco de execução para teste do analisador léxico
if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("\nUso: python lexico.py <arquivo_de_entrada>\n")
        sys.exit(1)

    nome_arquivo = sys.argv[1]
    analisador = Lexico(nome_arquivo)

    print("-" * 50)
    print(f"Analisando o arquivo (Modo Máquina de Estados): '{nome_arquivo}'")
    print("-" * 50)

    while True:
        token = analisador.prox_token()
        linha = analisador.token_linha
        coluna = analisador.token_coluna
        tipo = TOKEN.msg(token)
        lexema = analisador.lexema_atual

        print(f"L:{linha:03}, C:{coluna:03} | Token: {tipo:<18}| Lexema: '{lexema}'")

        if token == TOKEN.eof:
            break

    print("-" * 50)
    print("Análise léxica concluída.")
    print("-" * 50)