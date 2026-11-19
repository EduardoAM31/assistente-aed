---
titulo: Laço while em C
linguagem: C
topicos:
  - lacos
  - while
  - do-while
  - repeticao
---

# Laço while em C

## Como funciona o laço while em C

O laço `while` em C repete um bloco enquanto uma condição for verdadeira. A condição é testada antes de cada repetição, inclusive a primeira: se ela já começar falsa, o bloco não roda nenhuma vez.

```c
#include <stdio.h>

int main(void) {
    int n = 4096;
    int digitos = 0;
    while (n > 0) {
        n = n / 10;
        digitos++;
    }
    printf("%d digitos\n", digitos);  /* 4 digitos */
    return 0;
}
```

Esse programa conta os dígitos de um número dividindo por 10 até chegar a zero. Não dá para saber de antemão quantas voltas o laço vai dar: isso depende do número. Esse é o uso típico do `while`, repetir até que alguma coisa aconteça. Dentro do bloco, algo precisa mudar a condição, senão o laço nunca termina.

## Laço infinito com while em C: por que acontece

Um laço `while` em C vira um laço infinito quando a condição nunca fica falsa. O motivo mais comum é esquecer de atualizar a variável da condição dentro do bloco:

```c
int i = 0;
while (i < 5) {
    printf("%d\n", i);
    /* falta i++: i fica sempre 0 e o laço não para */
}
```

Também acontece quando a atualização vai na direção errada (`i--` em vez de `i++`) ou com um `;` logo depois do parêntese, como em `while (i < 5);`, que repete um comando vazio sem parar. Para interromper no terminal um programa preso num laço infinito, use Ctrl+C.

Às vezes o laço infinito é proposital: `while (1)` repete sem parar, e um `break` dentro do bloco encerra o laço quando uma condição é atingida. Isso é comum em menus que rodam até o usuário escolher "sair".

## O laço do-while em C roda pelo menos uma vez

O `do-while` em C é uma variação do `while` em que a condição é testada no fim, depois do bloco. Por isso o bloco sempre roda pelo menos uma vez. Ele é útil para validar entradas: pedir um valor e repetir o pedido enquanto o valor for inválido.

```c
#include <stdio.h>

int main(void) {
    int nota;
    do {
        printf("Digite uma nota de 0 a 10: ");
        scanf("%d", &nota);
    } while (nota < 0 || nota > 10);
    printf("Nota valida: %d\n", nota);
    return 0;
}
```

Repare no ponto e vírgula depois do `while (...)` no final: no `do-while` ele é obrigatório, e esquecê-lo causa erro de compilação. Com um `while` comum, a mesma validação exigiria ler o valor uma vez antes do laço e de novo dentro dele.

## Como ler valores até um sentinela com while em C

Um uso comum do `while` em C é ler valores até o usuário digitar um valor especial que indica o fim, chamado de sentinela. Como a quantidade de valores não é conhecida antes, o `while` é a escolha natural:

```c
#include <stdio.h>

int main(void) {
    int x, soma = 0;
    while (scanf("%d", &x) == 1 && x != 0) {
        soma += x;
    }
    printf("soma = %d\n", soma);
    return 0;
}
```

Aqui o sentinela é o 0: o laço soma os números lidos e para quando o usuário digita 0. A condição também confere o retorno do `scanf`, que devolve quantos valores conseguiu ler. Se a entrada acabar ou o usuário digitar algo que não é número, o `scanf` não devolve 1, e o laço termina em vez de repetir para sempre com o último valor lido.
