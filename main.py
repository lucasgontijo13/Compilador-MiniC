# main.py
import sys
from lexico import Lexico
from sintatico import Sintatico  # Mudamos de Semantico para Sintatico


def main():
    if len(sys.argv) != 2:
        print("\nUso: python main.py <arquivo_de_entrada>\n")
        sys.exit(1)

    nome_arquivo_entrada = sys.argv[1]

    # Cria o Lexico
    lexico = Lexico(nome_arquivo_entrada)

    # Cria o Sintatico e passa o Lexico
    # (O Sintatico vai criar o Semantico internamente)
    analisador = Sintatico(lexico)

    print(f"--- Iniciando análise de: {nome_arquivo_entrada} ---")
    analisador.analisa()


if __name__ == "__main__":
    main()