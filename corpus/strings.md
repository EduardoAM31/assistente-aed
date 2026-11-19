---
titulo: Strings em C
linguagem: C
topicos:
  - strings
  - char
  - string.h
  - entrada e saida
---

# Strings em C

## Em C, uma string é um vetor de char terminado em '\0'

C não tem um tipo próprio para texto. Uma string em C é um vetor de `char` em que o fim do texto é marcado por um caractere especial, o `'\0'` (caractere nulo, de valor zero). As funções de string, como `printf` com `%s` e `strlen`, leem caractere por caractere até encontrar o `'\0'`.

```c
#include <stdio.h>
#include <string.h>

int main(void) {
    char nome[6] = "Maria";   /* 'M','a','r','i','a','\0' */
    printf("%s tem %zu letras\n", nome, strlen(nome));  /* 5 */
    printf("o vetor tem %zu bytes\n", sizeof(nome));    /* 6 */
    return 0;
}
```

Por isso o vetor precisa de uma posição a mais que o número de letras: "Maria" tem 5 letras e ocupa 6 posições. Se faltar espaço para o `'\0'`, as funções de string continuam lendo a memória depois do vetor, o que é comportamento indefinido. O `strlen` conta só as letras, sem o `'\0'`.

## Como ler uma string em C com scanf e fgets

Para ler uma palavra em C, pode-se usar `scanf` com `%s`. Diferente dos números, a string não leva `&`, porque o nome do vetor já é convertido no endereço do primeiro elemento. O `scanf` com `%s` para no primeiro espaço, então "Ana Maria" vira só "Ana".

Para ler uma linha inteira, com espaços, use `fgets`:

```c
#include <stdio.h>
#include <string.h>

int main(void) {
    char nome[50];
    fgets(nome, sizeof(nome), stdin);
    nome[strcspn(nome, "\n")] = '\0';   /* tira o \n do final */
    printf("[%s]\n", nome);
    return 0;
}
```

O `fgets` recebe o tamanho do vetor e nunca escreve além dele, o que evita estouro. Ele também guarda o `\n` do Enter, por isso a linha seguinte o remove. Com `scanf`, dá para limitar o tamanho com `%49s`. Um problema comum: depois de um `scanf("%d", ...)`, o `\n` do Enter fica na entrada, e o `fgets` seguinte lê uma linha vazia.

## Por que não dá para comparar strings em C com ==

Em C, comparar duas strings com `==` não compara o texto: compara os endereços de memória onde cada uma começa. Duas strings com o mesmo conteúdo, guardadas em lugares diferentes, têm endereços diferentes, e o `==` dá falso. Para comparar o conteúdo, use `strcmp`, da biblioteca `<string.h>`:

```c
#include <stdio.h>
#include <string.h>

int main(void) {
    char resposta[10] = "sim";
    if (strcmp(resposta, "sim") == 0) {
        printf("iguais\n");
    }
    return 0;
}
```

O `strcmp` devolve 0 quando as strings são iguais, um valor negativo quando a primeira vem antes na ordem dos códigos dos caracteres e um valor positivo quando vem depois (na tabela ASCII, as maiúsculas vêm antes das minúsculas). Um erro comum é escrever `if (strcmp(a, b))` achando que isso testa igualdade: como 0 é falso em C, essa condição é verdadeira justamente quando as strings são diferentes.

## Como copiar e juntar strings em C com strcpy e strcat

Em C, não dá para atribuir uma string a um vetor com `=` depois da declaração: `nome = "Ana";` causa erro de compilação. O `=` só funciona na inicialização, como em `char nome[10] = "Ana";`. Para copiar e juntar strings, usam-se funções de `<string.h>`:

```c
#include <stdio.h>
#include <string.h>

int main(void) {
    char nome[20];
    strcpy(nome, "Ana");        /* copia: nome fica "Ana" */
    strcat(nome, " Silva");     /* junta: nome fica "Ana Silva" */
    printf("%s (%zu)\n", nome, strlen(nome));  /* Ana Silva (9) */
    return 0;
}
```

O `strcpy(destino, origem)` copia a origem para o destino, e o `strcat(destino, origem)` acrescenta a origem no fim do destino. Nenhuma das duas confere o tamanho: o vetor de destino precisa ter espaço para todas as letras e para o `'\0'`. Se não tiver, a função escreve além do vetor, o que é comportamento indefinido.
