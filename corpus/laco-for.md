---
titulo: Laço for em C
linguagem: C
topicos:
  - lacos
  - for
  - repeticao
---

# Laço for em C

## As três partes do laço for em C

O laço `for` em C repete um bloco de código e tem três partes entre parênteses, separadas por ponto e vírgula: inicialização, condição e incremento.

```c
#include <stdio.h>

int main(void) {
    for (int i = 1; i <= 5; i++) {
        printf("%d\n", i);
    }
    return 0;
}
```

A ordem de execução é sempre esta:

1. A inicialização (`int i = 1`) roda uma única vez, antes de tudo.
2. A condição (`i <= 5`) é testada. Se for falsa, o laço termina.
3. O corpo do laço (o bloco entre chaves) é executado.
4. O incremento (`i++`) é executado, e o programa volta para o passo 2.

Esse programa mostra os números de 1 a 5. Quando `i` vale 6, a condição fica falsa e o laço acaba. Como a condição é testada antes do corpo, se ela já começar falsa, o corpo não roda nenhuma vez.

## Como contar de trás para frente ou de 2 em 2 com o for em C

O incremento do `for` em C não precisa ser `i++`. Qualquer expressão serve, o que permite contar de trás para frente ou pular valores:

```c
#include <stdio.h>

int main(void) {
    for (int i = 10; i >= 1; i--) {
        printf("%d ", i);       /* 10 9 8 ... 1 */
    }
    printf("\n");
    for (int i = 0; i <= 10; i += 2) {
        printf("%d ", i);       /* 0 2 4 6 8 10 */
    }
    printf("\n");
    return 0;
}
```

Ao contar para trás, a condição também muda: em vez de `i <= limite`, usa-se `i >= limite`. Um erro comum é esquecer de trocar o sinal e escrever `i <= 1` com `i` começando em 10: a condição já é falsa no começo, e o laço não roda nenhuma vez. Outro erro é usar `i++` num laço que deveria descer, e aí o laço não para quando deveria.

## O erro do ponto e vírgula depois do for em C

Colocar ponto e vírgula logo depois dos parênteses do `for` em C é um erro difícil de ver. O `;` sozinho é um comando vazio, e ele vira o corpo do laço:

```c
#include <stdio.h>

int main(void) {
    int i;
    for (i = 0; i < 5; i++);   /* ERRADO: o ; é o corpo do laço */
    {
        printf("%d\n", i);     /* roda uma vez só e mostra 5 */
    }
    return 0;
}
```

O laço roda cinco vezes sem fazer nada. Depois que ele termina, o bloco entre chaves é executado uma única vez, com `i` valendo 5. O programa compila, e o resultado parece um laço que "não repete". Nesse exemplo, o `gcc -Wall` dá um aviso de indentação enganosa, mas nem sempre há aviso. A mesma coisa acontece com `while (condicao);` e com `if (condicao);`. A correção é apagar o `;` depois do parêntese.

## A variável declarada no for em C só existe dentro do laço

No `for` em C, a variável de controle pode ser declarada na própria inicialização, como em `for (int i = 0; i < n; i++)`. Essa forma existe desde o padrão C99, e a variável só existe dentro do laço: tentar usar `i` depois do `for` causa erro de compilação.

Se o valor da variável for necessário depois do laço, por exemplo para saber em que posição uma busca parou, a variável precisa ser declarada antes:

```c
#include <stdio.h>

int main(void) {
    int v[5] = {4, 8, 15, 16, 23};
    int i;
    for (i = 0; i < 5; i++) {
        if (v[i] == 15) {
            break;
        }
    }
    printf("parou no indice %d\n", i);  /* 2 */
    return 0;
}
```

O `break` encerra o laço na hora, sem executar o incremento. Por isso `i` fica com o índice em que o valor foi encontrado.
