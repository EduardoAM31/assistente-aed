---
titulo: if e else em C
linguagem: C
topicos:
  - condicionais
  - if
  - else
  - operadores relacionais
  - operadores logicos
---

# if e else em C

## Como funciona o if em C

O `if` em C executa um bloco de código só quando uma condição é verdadeira. A condição fica entre parênteses, e o bloco fica entre chaves:

```c
#include <stdio.h>

int main(void) {
    int idade = 20;
    if (idade >= 18) {
        printf("Maior de idade\n");
    }
    return 0;
}
```

Em C, a condição do `if` não precisa ser de um tipo booleano: qualquer valor diferente de zero conta como verdadeiro, e zero conta como falso. Os operadores de comparação (`==`, `!=`, `<`, `>`, `<=`, `>=`) produzem 1 quando a comparação é verdadeira e 0 quando é falsa. Por isso `if (5)` sempre executa o bloco, e `if (0)` nunca executa.

## Como usar else e else if em C

O `else` em C define o que fazer quando a condição do `if` é falsa. Para testar várias possibilidades em sequência, usa-se `else if`:

```c
#include <stdio.h>

int main(void) {
    double nota = 7.5;
    if (nota >= 9.0) {
        printf("A\n");
    } else if (nota >= 7.0) {
        printf("B\n");
    } else {
        printf("C\n");
    }
    return 0;
}
```

As condições são testadas de cima para baixo, e só o primeiro bloco cuja condição é verdadeira é executado. Os outros são pulados, mesmo que também fossem verdadeiros. Por isso a ordem importa: se `nota >= 7.0` viesse antes de `nota >= 9.0`, uma nota 9.5 cairia no "B". O `else` final é opcional e só roda quando nenhuma condição anterior foi verdadeira.

## O erro de usar = em vez de == no if em C

Em C, `=` é atribuição e `==` é comparação. Trocar um pelo outro dentro do `if` é um erro comum, e o programa compila mesmo assim:

```c
int x = 3;
if (x == 5) { /* compara: falso, o bloco não roda */ }
if (x = 5)  { /* ERRADO: guarda 5 em x, e 5 conta como verdadeiro */ }
```

Na segunda linha, `x = 5` coloca 5 em `x`, e o valor da expressão inteira é 5. Como qualquer valor diferente de zero é verdadeiro em C, o bloco sempre executa, e o valor original de `x` ainda se perde. Compilando com `gcc -Wall`, o compilador avisa sobre esse caso e sugere parênteses em volta da atribuição. Por isso vale sempre compilar com os avisos ligados e ler os avisos, não só os erros.

## Como combinar condições no if em C com && e ||

Para combinar condições no `if` em C, usam-se os operadores lógicos: `&&` (e), `||` (ou) e `!` (não). Com `&&`, o resultado é verdadeiro só se as duas condições forem verdadeiras. Com `||`, basta uma delas.

```c
#include <stdio.h>

int main(void) {
    int x = 15;
    if (x > 0 && x < 10) {
        printf("entre 1 e 9\n");
    }
    if (0 < x < 10) {  /* ERRADO: sempre verdadeiro */
        printf("isto sempre aparece\n");
    }
    return 0;
}
```

Escrever `0 < x < 10`, como na matemática, não funciona em C. A expressão é calculada como `(0 < x) < 10`: a primeira comparação dá 0 ou 1, e tanto 0 quanto 1 são menores que 10. O certo é `x > 0 && x < 10`. Os operadores `&&` e `||` também param cedo: se a primeira parte de um `&&` for falsa, a segunda nem é avaliada.
