---
titulo: Alocação dinâmica de memória em C
linguagem: C
topicos:
  - alocacao dinamica
  - malloc
  - free
  - memoria
---

# Alocação dinâmica de memória em C

## O que é alocação dinâmica em C e quando usar malloc

Um vetor comum em C tem o tamanho definido na declaração e deixa de existir quando o bloco em que foi declarado termina. Com alocação dinâmica, o programa pede memória enquanto roda, do tamanho que precisar, e essa memória continua válida até ser liberada com `free`, mesmo depois que a função que a pediu termina. A função `malloc`, da biblioteca `<stdlib.h>`, recebe a quantidade de bytes e devolve um ponteiro para o início do bloco, ou `NULL` se não houver memória disponível.

```c
#include <stdio.h>
#include <stdlib.h>

int main(void) {
    int n;
    if (scanf("%d", &n) != 1 || n <= 0) {
        return 1;
    }
    int *v = malloc(n * sizeof(int));   /* vetor de n inteiros */
    if (v == NULL) {
        printf("Sem memoria\n");
        return 1;
    }
    for (int i = 0; i < n; i++) {
        v[i] = i * i;
    }
    printf("%d\n", v[n - 1]);
    free(v);
    return 0;
}
```

Use alocação dinâmica quando o tamanho só é conhecido durante a execução, como um vetor do tamanho que o usuário digitou, ou quando os dados precisam continuar existindo depois que uma função termina, como os nós de uma lista encadeada. Teste sempre se o retorno foi `NULL` antes de usar o ponteiro.

## Por que usar sizeof no malloc em C

O `malloc` em C conta bytes, não elementos. Por isso, `malloc(10)` reserva 10 bytes, e não 10 inteiros. Como um `int` costuma ocupar 4 bytes, esse bloco só tem espaço para 2 inteiros, e usar `v[5]` nele é acesso fora dos limites, com comportamento indefinido.

```c
int *v = malloc(10);                 /* ERRADO: 10 bytes */
int *w = malloc(10 * sizeof(int));   /* certo: 10 inteiros */
```

O certo é multiplicar a quantidade de elementos pelo tamanho de cada um, usando `sizeof`. O tamanho dos tipos pode mudar de um computador para outro, e o `sizeof` sempre dá o valor certo para a máquina em que o programa roda. Outra forma comum é `malloc(10 * sizeof *w)`, que usa o tipo apontado por `w` e continua certa se o tipo mudar. Em C, não é preciso converter o retorno com `(int *)`: o `void *` devolvido pelo `malloc` é convertido automaticamente. Em C++, essa conversão é obrigatória.

## Como liberar memória com free em C: vazamento e ponteiro solto

Toda memória obtida com `malloc` em C precisa ser devolvida com `free` quando não for mais usada. Esquecer o `free` causa um vazamento de memória (memory leak): o programa ocupa cada vez mais memória, o que é grave em programas que rodam por muito tempo ou que alocam memória dentro de laços. Na maioria dos sistemas, a memória volta quando o programa termina, mas isso não justifica deixar de liberar.

```c
int *p = malloc(sizeof(int));
/* ... usa p ... */
free(p);
p = NULL;   /* evita usar por engano a memória já liberada */
```

Depois do `free`, o ponteiro continua guardando o endereço antigo, mas a memória não pertence mais ao programa. Usar esse ponteiro solto (dangling pointer) ou chamar `free` duas vezes no mesmo bloco é comportamento indefinido. Colocar `NULL` no ponteiro logo depois do `free` ajuda, porque `free(NULL)` não faz nada, e um acesso por `NULL` costuma falhar de forma visível.

## calloc e realloc em C: memória zerada e mudança de tamanho

Além do `malloc`, a biblioteca `<stdlib.h>` tem duas funções de alocação muito usadas. O `calloc(n, tamanho)` reserva espaço para `n` elementos e coloca zero em todos os bytes. O `realloc(ponteiro, novo_tamanho)` muda o tamanho de um bloco já alocado, mantendo o conteúdo antigo, e pode mudar o bloco de lugar na memória.

```c
#include <stdio.h>
#include <stdlib.h>

int main(void) {
    int *v = calloc(3, sizeof(int));   /* 3 inteiros, todos 0 */
    if (v == NULL) {
        return 1;
    }
    int *maior = realloc(v, 6 * sizeof(int));   /* agora cabem 6 */
    if (maior == NULL) {
        free(v);   /* o bloco antigo continua valendo */
        return 1;
    }
    v = maior;
    v[5] = 42;
    printf("%d %d\n", v[0], v[5]);   /* 0 42 */
    free(v);
    return 0;
}
```

O cuidado com o `realloc` é não escrever `v = realloc(v, ...)` direto. Se ele falhar, devolve `NULL` e o bloco antigo continua alocado: com a atribuição direta, o único ponteiro para esse bloco se perde, e a memória vaza. O certo é guardar o resultado numa variável separada e só trocar depois de conferir que não é `NULL`. As posições novas criadas pelo `realloc` começam com valores indeterminados.
