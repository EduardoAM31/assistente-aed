---
titulo: Ponteiros em C
linguagem: C
topicos:
  - ponteiros
  - enderecos
  - memoria
  - NULL
---

# Ponteiros em C

## O que é um ponteiro em C e os operadores & e *

Um ponteiro em C é uma variável que guarda um endereço de memória, normalmente o endereço de outra variável. Dois operadores são usados com ponteiros: `&` dá o endereço de uma variável, e `*` acessa o valor que está no endereço guardado pelo ponteiro.

```c
#include <stdio.h>

int main(void) {
    int x = 10;
    int *p = &x;          /* p guarda o endereço de x */
    printf("%d\n", *p);   /* 10: o valor que está em x */
    *p = 20;              /* muda x através de p */
    printf("%d\n", x);    /* 20 */
    return 0;
}
```

O `*` tem dois papéis diferentes. Na declaração `int *p`, ele indica que `p` é um ponteiro para `int`. Numa expressão como `*p = 20`, ele significa "o valor no endereço guardado em `p`". O tipo do ponteiro precisa combinar com o tipo da variável: um `int *` aponta para `int`, e um `double *` aponta para `double`.

## Como uma função altera uma variável em C usando ponteiros

Em C, uma função recebe cópias dos argumentos, então não consegue alterar diretamente as variáveis de quem chamou. Com ponteiros, a função recebe o endereço da variável e pode mudar o valor original. O exemplo clássico é trocar dois valores:

```c
#include <stdio.h>

void trocar(int *a, int *b) {
    int temp = *a;
    *a = *b;
    *b = temp;
}

int main(void) {
    int x = 1, y = 2;
    trocar(&x, &y);
    printf("%d %d\n", x, y);   /* 2 1 */
    return 0;
}
```

Na chamada, `&x` e `&y` passam os endereços. Dentro da função, `*a` e `*b` são as próprias variáveis `x` e `y`. Se a função recebesse `int a, int b`, ela trocaria só as cópias, e nada mudaria no `main`. O `scanf` funciona do mesmo jeito: `scanf("%d", &x)` recebe o endereço de `x` para guardar o valor lido.

## Ponteiro não inicializado e ponteiro NULL em C

Um ponteiro em C declarado sem valor, como `int *p;` dentro de uma função, guarda um endereço indeterminado. Usar `*p` nesse estado é comportamento indefinido: o programa pode travar ou escrever por cima de outro dado sem nenhum aviso.

```c
int *p;          /* ERRADO usar *p: o endereço é indeterminado */
int *q = NULL;   /* certo: q não aponta para nada, e isso é testável */
if (q != NULL) {
    *q = 5;      /* só usa o ponteiro se ele for válido */
}
```

`NULL` é um valor especial que significa "não aponta para nada", definido em `<stdio.h>`, `<stdlib.h>` e outras bibliotecas. Acessar `*q` com `q` valendo `NULL` também é comportamento indefinido, mas na prática costuma encerrar o programa com um erro como "segmentation fault", que é mais fácil de perceber do que um valor errado silencioso. Por isso a regra é: inicialize todo ponteiro, com um endereço válido ou com `NULL`, e confira se ele não é `NULL` antes de usar.

## Ponteiros e vetores em C

Em C, ponteiros e vetores estão ligados. Na maioria das expressões, o nome de um vetor é convertido num ponteiro para o primeiro elemento. Por isso um ponteiro pode percorrer um vetor, e a notação `p[i]` funciona com ponteiros, valendo o mesmo que `*(p + i)`:

```c
#include <stdio.h>

int main(void) {
    int v[3] = {10, 20, 30};
    int *p = v;                          /* o mesmo que &v[0] */
    printf("%d %d\n", p[1], *(p + 2));   /* 20 30 */
    return 0;
}
```

Somar 1 a um ponteiro avança um elemento inteiro, não um byte: em `p + 2`, o compilador já leva em conta o tamanho de um `int`. Mesmo assim, vetor e ponteiro não são a mesma coisa. Um vetor reserva espaço para todos os elementos, e `sizeof(v)` dá o tamanho do vetor inteiro, enquanto `sizeof(p)` dá só o tamanho do ponteiro. Além disso, um ponteiro pode receber outro endereço (`p = &x;`), mas um vetor não pode receber outro vetor.
