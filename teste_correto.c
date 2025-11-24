// teste_correto.c
// Exemplo de código válido para o compilador Mini-C

// Função auxiliar para testar chamada de função, parâmetros e retorno.
int soma(int a, int b) {
    return a + b;
}

int main() {
    // --- Declarações de variáveis ---
    int x;
    int y;
    float z;
    char c;
    int vet[5]; // Declaração de um array de inteiros
    int i;      // Variável de controle para o laço for

    // --- Atribuições e Expressões ---
    x = 10;
    y = 20;
    z = 3.14;
    c = 'A';

    // --- Chamada de Função ---
    // A variável 'x' receberá o resultado de 10 + 20
    x = soma(x, y);

    // --- Estrutura Condicional (IF/ELSE) ---
    if (x == 30) {
        z = z + 1.0; // Expressão com float
    } else {
        z = 0.0;
    }

    // --- Laço WHILE com break e continue ---
    y = 0;
    while (y < 5) {
        if (y == 2) {
            y = y + 1;
            continue; // Pula o resto do laço e vai para a próxima iteração
        }

        vet[y] = y * 10; // Atribuição a um elemento do array

        if (y == 4) {
            break; // Interrompe o laço
        }
        y = y + 1;
    }

    // --- Laço FOR ---
    for (i = 0; i < 5; i = i + 1) {
        vet[i] = vet[i] + i; // Acessando e modificando elementos do array
    }

    return 0;
}