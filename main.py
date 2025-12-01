# main.py
import sys
import subprocess
from lexico import Lexico
from sintatico import Sintatico


def main():
    if len(sys.argv) != 2:
        print("\nUso: python main.py <arquivo_de_entrada>\n")
        sys.exit(1)

    nome_arquivo_entrada = sys.argv[1]

    lexico = Lexico(nome_arquivo_entrada)
    analisador = Sintatico(lexico)

    print(f"--- Iniciando compilação de: {nome_arquivo_entrada} ---")

    # Agora o analisa retorna uma string com o código Python
    codigo_python = analisador.analisa()

    if codigo_python:
        # Salva o código gerado em um arquivo temporário
        arquivo_saida = "saida_gerada.py"
        with open(arquivo_saida, "w", encoding="utf-8") as f:
            f.write(codigo_python)

        print(f"✅ Compilação Sucesso! Código gerado em '{arquivo_saida}'.")
        print("---------------------------------------------------")
        print("🚀 EXECUTANDO O CÓDIGO GERADO...\n")

        # Executa o código gerado
        subprocess.run([sys.executable, arquivo_saida])
        print("\n---------------------------------------------------")


if __name__ == "__main__":
    main()