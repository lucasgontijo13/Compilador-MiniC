int main(){

    // Declarações corretas
    //int x = 10;
    //float y = 3.14;
    //char c = 'A';

    // --- Situações intencionalmente erradas para testar o léxico ---

    // 1) identificador começando com dígito (inválido)
    int 9var = 5;

    // 2) número float mal formado (dois pontos)
    float z = 3..14;

    // 3) número com letra no meio (erro léxico em número)
    int a = 12a;

    // 4) literal char com mais de um caractere (deveria ser erro/aviso)
    char multi = 'AB';

    // 5) string não terminada
    char s = "hello;

    // 6) char não terminado
    char unter = 'B

    // 7) operador lógico inválido (&&&)
    if (x >= 10 &&& y < 4.0) {
        x = x + 1;
    }

    // 8) uso de um & isolado (lexema não reconhecido pelo estado '&')
    if (x & y) {
        x = x - 1;
    }

    // 9) uso de | isolado (lexema não reconhecido pelo estado '|')
    if (x | y) {
        x = x * 2;
    }

    // 10) caractere inválido '@' e símbolo '$' em identificador
    @invalid_token;
    int var$ = 7;

    // 11) ponto final em número sem dígitos depois (123.)
    float f = 123.;

    // 12) comentário estilo C (/* ... */) aberto e não fechado — o léxico só trata '//' como comentário
    x = x + 1;

    // 13) uso de operador de atribuição errado (:=)
    y := 2.0;

    // 14) separador inesperado em meio a identificador
    int my,var = 3; // vírgula é token mas aqui cria ambiguidade proposital

    // 15) cadeia com quebra de linha no meio (string multilinha sem fechamento)
    // essa string ta errada, deve ser:
    char longstr1 = "uma string muito longa" +
    "que quebra de linha sem fechar";

    char longstr = "uma string muito longa
    que quebra de linha sem fechar";

    // 16) operador '?' não reconhecido
    int q = ?;

    // 17) número hex com prefixo confuso (0xG1)
    int h = 0xG1;

    // 18) uso de comentário com duas barras e depois EOF sem nova linha
    // comentário no fim do arquivo sem quebra de linha

}