---
titulo: switch e case em C
linguagem: C
topicos:
  - condicionais
  - switch
  - case
  - break
---

# switch e case em C

## Como funciona o switch em C

O `switch` em C compara o valor de uma expressão com uma lista de valores fixos, os `case`, e pula para o `case` que for igual. Se nenhum for igual, executa o `default`, que é opcional:

```c
#include <stdio.h>

int main(void) {
    int opcao = 2;
    switch (opcao) {
        case 1:
            printf("Cadastrar\n");
            break;
        case 2:
            printf("Listar\n");
            break;
        default:
            printf("Opcao invalida\n");
    }
    return 0;
}
```

A expressão do `switch` precisa ser de um tipo inteiro, como `int` ou `char`. Cada `case` precisa ser uma constante, como `1` ou `'a'`, e dois `case` não podem ter o mesmo valor. O `switch` é comum em menus, em que o usuário digita um número para escolher uma opção.

## Por que o break é necessário no switch em C

No `switch` em C, o `case` só marca o ponto de entrada. Depois de entrar num `case`, o programa continua executando as linhas seguintes, inclusive as dos próximos `case`, até encontrar um `break` ou o fim do `switch`. Esse comportamento se chama fall-through.

```c
#include <stdio.h>

int main(void) {
    int opcao = 1;
    switch (opcao) {
        case 1:
            printf("Um\n");   /* sem break: continua */
        case 2:
            printf("Dois\n");
            break;
    }
    return 0;
}
```

Com `opcao` igual a 1, esse programa mostra "Um" e também "Dois", porque falta o `break` no `case 1`. Esquecer o `break` é o erro mais comum com `switch`. O fall-through às vezes é usado de propósito, para vários valores terem a mesma ação: `case 'a': case 'e': case 'i':` seguidos de um único bloco de código.

## O que o switch em C não aceita: strings, números reais e faixas

O `switch` em C só compara a expressão com constantes inteiras, uma de cada vez. Por isso ele não serve para quatro situações comuns:

- **Strings:** `case "sim":` não compila. Para comparar strings, usa-se `strcmp` dentro de um `if`.
- **Números reais:** a expressão do `switch` não pode ser `float` nem `double`.
- **Faixas de valores:** no C padrão, não existe `case` que signifique "de 0 a 5". Seria preciso um `case` para cada valor. O GCC aceita `case 0 ... 5:` como extensão, mas isso não faz parte dos padrões C99, C11 e C23.
- **Variáveis no case:** `case limite:` não compila se `limite` for uma variável.

Nesses casos, a solução é usar `if` e `else if`, que aceitam qualquer condição, como `nota >= 7.0` ou `x > 0 && x < 10`.

## Quando usar switch ou if-else em C

Em C, todo `switch` pode ser reescrito com `if` e `else if`, mas o contrário nem sempre. O `switch` costuma ser a escolha mais legível quando uma única variável inteira é comparada com vários valores fixos, como num menu de opções ou na escolha de uma operação por um caractere (`'+'`, `'-'`, `'*'`, `'/'`).

O `if-else` é necessário quando a condição envolve faixas de valores (`nota >= 7.0`), mais de uma variável, números reais ou strings. Ele também é mais simples quando há só duas ou três possibilidades.

Uma regra prática: se cada caso é "a variável vale exatamente X", o `switch` funciona bem. Se algum caso é "a variável está entre X e Y" ou depende de outra coisa, use `if-else`. Com o `switch`, lembre de colocar `break` no fim de cada `case`.
