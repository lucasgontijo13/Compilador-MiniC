from enum import IntEnum


class TOKEN(IntEnum):
    """
    Enumeração que define os tokens da nova linguagem.
    """
    # Tokens de Controle (1-2)
    erro = 1
    eof = 2

    # Literais (3-7)
    ident = 3
    valorInt = 4
    valorFloat = 5
    valorChar = 6
    valorString = 7

    # Palavras Reservadas (8-17)
    FOR = 8
    WHILE = 9
    IF = 10
    ELSE = 11
    BREAK = 12
    CONTINUE = 13
    RETURN = 14
    INT = 15
    FLOAT = 16
    CHAR = 17

    # Operadores Lógicos como Símbolos (18-20)
    AND = 18  # &&
    OR = 19  # ||
    NOT = 20  # !

    # Símbolos (21-28)
    abrePar = 21  # (
    fechaPar = 22  # )
    abreChave = 23  # {
    fechaChave = 24  # }
    abreColch = 25  # [
    fechaColch = 26  # ]
    virg = 27  # ,
    ptoVirg = 28  # ;

    # Outros Operadores (29-30)
    atrib = 29  # =
    opRel = 30  # ==, !=, <, <=, >, >=

    # --- Aritméticos (31-35) ---
    mais = 31  # +
    menos = 32  # -
    multiplica = 33  # *
    divide = 34  # /
    mod = 35  # %

    @classmethod
    def msg(cls, token):
        """ Retorna a representação em string de um token. """
        nomes = {
            1: 'erro',
            2: '<eof>',
            3: 'identificador',
            4: 'valor_inteiro',
            5: 'valor_float',
            6: 'valor_char',
            7: 'valor_string',
            8: 'for',
            9: 'while',
            10: 'if',
            11: 'else',
            12: 'break',
            13: 'continue',
            14: 'return',
            15: 'int',
            16: 'float',
            17: 'char',
            18: '&&',
            19: '||',
            20: '!',
            21: '(',
            22: ')',
            23: '{',
            24: '}',
            25: '[',
            26: ']',
            27: ',',
            28: ';',
            29: '=',
            30: 'op_relacional',
            31: '+',
            32: '-',
            33: '*',
            34: '/',
            35: '%'
        }
        return nomes[token]

    @classmethod
    def reservada(cls, lexema):
        """ Verifica se um lexema é uma palavra reservada. """
        reservadas = {
            'for': TOKEN.FOR,
            'while': TOKEN.WHILE,
            'if': TOKEN.IF,
            'else': TOKEN.ELSE,
            'break': TOKEN.BREAK,
            'continue': TOKEN.CONTINUE,
            'return': TOKEN.RETURN,
            'int': TOKEN.INT,
            'float': TOKEN.FLOAT,
            'char': TOKEN.CHAR,
        }
        if lexema in reservadas:
            return reservadas[lexema]
        else:
            return TOKEN.ident