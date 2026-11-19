---
titulo: Funções em C
linguagem: C
topicos:
  - funcoes
  - parametros
  - retorno
  - prototipo
---

# Funções em C

## Como declarar e chamar uma função em C

Uma função em C é um bloco de código com nome, que pode receber valores (parâmetros) e devolver um resultado. A definição tem o tipo do retorno, o nome, os parâmetros entre parênteses e o corpo entre chaves:

```c
#include <stdio.h>

int soma(int a, int b) {
    return a + b;
}

int main(void) {
    int r = soma(2, 3);
    printf("%d\n", r);   /* 5 */
    return 0;
}
```

Na chamada `soma(2, 3)`, o valor 2 vai para `a` e o 3 vai para `b`, na ordem. O `return` encerra a função e devolve o valor para quem chamou, que pode guardá-lo numa variável ou usá-lo direto, como em `printf("%d", soma(2, 3))`. Funções servem para não repetir código e para dividir um programa grande em partes menores, cada uma com uma tarefa.

## Funções void e o return em C

Uma função em C que não devolve nenhum valor é declarada com o tipo `void`. Ela pode usar `return;` sozinho para terminar mais cedo, mas não devolve nada:

```c
#include <stdio.h>

void mostrar_linha(int n) {
    for (int i = 0; i < n; i++) {
        printf("-");
    }
    printf("\n");
}

int main(void) {
    mostrar_linha(10);
    return 0;
}
```

Já uma função com tipo de retorno, como `int` ou `double`, precisa chegar a um `return` com um valor em todos os caminhos. Se ela chegar ao fim sem `return` e quem chamou usar o resultado, o comportamento é indefinido. O `gcc -Wall` avisa nesse caso. Outro ponto: o `return` devolve um único valor. Para uma função entregar mais de um resultado, usam-se ponteiros como parâmetros.

## Por que declarar o protótipo de uma função em C

Em C, o compilador lê o arquivo de cima para baixo. Se o `main` chama uma função que só é definida mais abaixo, o compilador ainda não a conhece no momento da chamada. Desde o padrão C99, chamar uma função não declarada não é permitido, e o GCC trata isso como erro a partir da versão 14. Versões antigas davam só um aviso e supunham que a função devolvia `int`. A solução é declarar o protótipo antes do `main`:

```c
#include <stdio.h>

double media(double a, double b);   /* protótipo */

int main(void) {
    printf("%.1f\n", media(7.0, 8.0));   /* 7.5 */
    return 0;
}

double media(double a, double b) {
    return (a + b) / 2.0;
}
```

O protótipo é a primeira linha da função terminada com ponto e vírgula. Ele informa o nome, o tipo de retorno e os tipos dos parâmetros, e com ele o compilador passa a conferir as chamadas. Outra opção é definir as funções antes do `main`.

## Passagem por valor em C: a função recebe uma cópia

Em C, os argumentos são passados por valor: a função recebe uma cópia de cada valor, não a variável original. Mudar o parâmetro dentro da função não muda a variável de quem chamou:

```c
#include <stdio.h>

void dobrar(int x) {
    x = x * 2;   /* muda só a cópia */
}

int main(void) {
    int n = 5;
    dobrar(n);
    printf("%d\n", n);   /* continua 5 */
    return 0;
}
```

Para a função alterar a variável original, há duas saídas. A primeira é devolver o novo valor com `return` e guardar o resultado: `n = dobrar(n);`, com `dobrar` retornando `int`. A segunda é passar o endereço da variável, com um ponteiro: a função recebe `int *x`, a chamada fica `dobrar(&n)`, e dentro da função se escreve `*x = *x * 2;`. É por isso que o `scanf` recebe `&n`: ele precisa do endereço para guardar o valor lido.

## Como passar um vetor para uma função em C

Quando um vetor é passado para uma função em C, a função não recebe uma cópia do vetor: recebe o endereço do primeiro elemento. Por isso, ao contrário das variáveis comuns, alterar os elementos dentro da função altera o vetor original. Como a função não tem como descobrir o tamanho do vetor, ele é passado como outro parâmetro:

```c
#include <stdio.h>

void zerar(int v[], int n) {
    for (int i = 0; i < n; i++) {
        v[i] = 0;
    }
}

int main(void) {
    int notas[3] = {7, 8, 9};
    zerar(notas, 3);
    printf("%d %d %d\n", notas[0], notas[1], notas[2]);  /* 0 0 0 */
    return 0;
}
```

Na chamada, usa-se só o nome do vetor, `notas`, sem colchetes e sem `&`. O parâmetro `int v[]` é equivalente a `int *v`. Se a função não deve alterar o vetor, o parâmetro pode ser declarado como `const int v[]`, e o compilador acusa erro em qualquer tentativa de alteração.
