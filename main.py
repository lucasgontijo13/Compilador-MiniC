# main.py

import sys
# 1. Mude a importação de 'sintatico' para 'semantico'
from semantico import Semantico  # << MUDANÇA AQUI


def main():

    if len(sys.argv) != 2:
        print("\nUso: python main.py <arquivo_de_entrada>\n")
        sys.exit(1)

    nome_arquivo_entrada = sys.argv[1]

    # 2. Instancie a classe Semantico em vez de Sintatico
    analisador = Semantico(nome_arquivo_entrada)  # << MUDANÇA AQUI

    print(f"--- Iniciando análise completa do arquivo: {nome_arquivo_entrada} ---")
    analisador.analisa()
    print(f"--- Análise finalizada. ---")


# Bloco de execução principal
if __name__ == "__main__":
    main()