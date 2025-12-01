import sys

# --- Biblioteca Padrão Simulada ---
def putint(x): print(x, end='')
def putfloat(x): print(x, end='')
def putstr(x): print(x, end='')
def putchar(x): print(x, end='')
def getint(): return int(float(input()))
def getfloat(): return float(input())
def getchar(): return input()[0] if input() else '\0'

# --- Código do Usuário ---
def ordena(vetor, tam):
    topo = 0
    bolha = 0
    topo = tam - 1
    while topo > 1:
        bolha = 0
        while bolha < topo:
            if vetor[bolha] > vetor[bolha + 1]:
                aux = 0
                aux = vetor[bolha + 1]
                vetor[bolha + 1] = vetor[bolha]
                vetor[bolha] = aux
            bolha = bolha + 1
        topo = topo - 1

def prompt(i):
    putstr("Digite o ")
    putint(i)
    putstr("o inteiro: ")

def main():
    buffer = [0] * 15
    i = 0
    putstr("ENTRADA \n")
    i = 0
    while i < 15:
        prompt(i + 1)
        buffer[i] = getint()
        i = i + 1
    ordena(buffer, 15)
    putstr("SAIDA \n")
    i = 0
    while i < 15:
        putint(buffer[i])
        putchar('\n')
        i = i + 1
    x = 0.0
    x = 3.14
    z = 0


if __name__ == '__main__':
    main()