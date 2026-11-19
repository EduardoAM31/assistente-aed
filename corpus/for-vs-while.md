---
titulo: Diferença entre for e while em C
linguagem: C
topicos:
  - lacos
  - for
  - while
  - comparacao
---

# Diferença entre for e while em C

## Em C, todo for pode ser escrito como while

Em C, `for` e `while` têm o mesmo poder: qualquer laço `for` pode ser reescrito como `while`, e vice-versa. O `for` só junta num lugar as três partes que, no `while`, ficam espalhadas:

```c
#include <stdio.h>

int main(void) {
    for (int i = 0; i < 3; i++) {
        printf("%d\n", i);
    }

    int j = 0;           /* inicialização */
    while (j < 3) {      /* condição */
        printf("%d\n", j);
        j++;             /* incremento */
    }
    return 0;
}
```

Os dois laços mostram 0, 1 e 2. A diferença entre eles é de organização e legibilidade, não de capacidade nem de velocidade: o compilador gera praticamente o mesmo código para os dois. A escolha entre `for` e `while` serve para deixar mais claro, para quem lê, que tipo de repetição está acontecendo.

## Quando usar for em C

O `for` em C é a escolha mais clara quando o número de repetições é conhecido antes do laço começar, ou quando existe um contador que avança de forma regular. Exemplos típicos:

- percorrer um vetor do índice 0 até o tamanho menos 1;
- repetir algo exatamente `n` vezes;
- contar de 10 até 1, ou de 2 em 2.

Nesses casos, quem lê a linha `for (int i = 0; i < n; i++)` entende de uma vez onde o laço começa, quando ele para e como avança. Com `while`, essas informações ficariam em três lugares diferentes, e seria mais fácil esquecer o incremento e criar um laço infinito.

## Quando usar while em C

O `while` em C é a escolha mais clara quando o número de repetições não é conhecido antes e depende de algo que acontece durante o laço. Exemplos típicos:

- ler valores até o usuário digitar um valor de parada (sentinela);
- repetir um menu até o usuário escolher "sair";
- dividir um número por 10 até ele chegar a zero, para contar os dígitos;
- pedir uma entrada de novo enquanto ela for inválida (aqui, o `do-while` costuma ser ainda melhor, porque roda pelo menos uma vez).

Nesses casos não existe um contador natural, e o que importa é a condição de parada. Escrever isso com `for` funciona, mas fica forçado, como em `for (; x != 0; )`, que é só um `while` disfarçado.

## Diferença do continue no for e no while em C

Existe um caso em que trocar `for` por `while` muda o comportamento: o `continue`. Ele pula o resto do corpo e vai para a próxima repetição. No `for`, a próxima repetição começa pelo incremento. No `while`, o incremento é uma linha comum do corpo, e o `continue` pode pulá-lo:

```c
#include <stdio.h>

int main(void) {
    for (int i = 0; i < 5; i++) {
        if (i == 2) {
            continue;           /* pula o 2, mas o i++ roda */
        }
        printf("%d ", i);       /* 0 1 3 4 */
    }
    printf("\n");
    return 0;
}
```

Se esse laço for reescrito como `while`, com `i++` no fim do bloco, o `continue` pula o `i++` quando `i` vale 2. Aí `i` fica preso em 2, e o laço nunca termina. Ao converter um `for` com `continue` em `while`, o incremento precisa vir antes do `continue`.
