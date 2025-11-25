# main.py

import sys
from semantico import Semantico


def main():

    if len(sys.argv) != 2:
        print("\nUso: python main.py <arquivo_de_entrada>\n")
        sys.exit(1)

    nome_arquivo_entrada = sys.argv[1]

    # 2. Instancie a classe Semantico em vez de Sintatico
    analisador = Semantico(nome_arquivo_entrada)

    try:
        analisador.analisa()
        print(f"--- Análise finalizada. ---")
    except Exception as e:
        # Apenas imprima 'e', pois a formatação já está na mensagem da exceção
        print(e)



# Bloco de execução principal
if __name__ == "__main__":
    main()