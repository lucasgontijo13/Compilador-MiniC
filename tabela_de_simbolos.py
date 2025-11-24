# tabela_de_simbolos.py
from tipo import Tipo

class Simbolo:
    def __init__(self, nome, tipo, categoria, info_extras=None):
        self.nome = nome
        self.tipo = tipo # Um valor do Enum Tipo
        self.categoria = categoria # 'variavel', 'funcao', 'parametro', 'array'
        self.info_extras = info_extras if info_extras is not None else {} # Ex: {'params': [Tipo.INT, ...], 'return': Tipo.FLOAT}

    def __str__(self):
        return f"Simbolo(Nome: {self.nome}, Tipo: {self.tipo.value}, Categoria: {self.categoria})"

class TabelaDeSimbolos:
    def __init__(self):
        # A tabela é uma pilha de dicionários, onde cada dicionário é um escopo.
        self.escopos = [{}] # Começa com o escopo global

    def entrar_escopo(self):
        # Empilha um novo escopo (dicionário vazio)
        self.escopos.append({})

    def sair_escopo(self):
        # Desempilha o escopo atual, se não for o global
        if len(self.escopos) > 1:
            self.escopos.pop()

    def adicionar(self, simbolo):
        escopo_atual = self.escopos[-1]
        if simbolo.nome in escopo_atual:
            # Erro: Símbolo já declarado neste escopo
            return False
        escopo_atual[simbolo.nome] = simbolo
        return True

    def buscar(self, nome):
        # Procura o símbolo do escopo mais interno para o mais externo
        for escopo in reversed(self.escopos):
            if nome in escopo:
                return escopo[nome]
        # Símbolo não encontrado
        return None