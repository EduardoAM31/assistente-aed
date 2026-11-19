---
titulo: Indentação e chaves em C
linguagem: C
topicos:
  - indentacao
  - chaves
  - blocos
  - legibilidade
---

# Indentação e chaves em C

## Em C, a indentação não muda o funcionamento do programa

Em C, ao contrário de Python, a indentação (os espaços no começo das linhas) não muda o que o programa faz. Fora das strings e das diretivas como `#include` e `#define`, o compilador usa espaços, tabulações e quebras de linha só para separar as palavras do código, e a quantidade deles não importa. Quem define quais comandos pertencem a um `if`, `for` ou `while` são as chaves `{` e `}`, não o alinhamento.

Os dois `if` deste programa fazem exatamente a mesma coisa, apesar da diferença de formatação:

```c
#include <stdio.h>

int main(void) {
    int x = 3;
    if (x > 0) {
        printf("positivo\n");
    }
if (x > 0) { printf("positivo\n"); }
    return 0;
}
```

A indentação existe para as pessoas. Ela mostra visualmente a estrutura do código e ajuda a encontrar erros, como uma chave fechada no lugar errado. Um código mal indentado funciona igual, mas é muito mais difícil de ler e de corrigir.

## O erro do if sem chaves com duas linhas indentadas em C

Em C, um `if` sem chaves controla só o próximo comando. Indentar uma segunda linha não a coloca dentro do `if`:

```c
#include <stdio.h>

int main(void) {
    int saldo = 50;
    if (saldo < 0)
        printf("Saldo negativo\n");
        printf("Conta bloqueada\n");   /* roda SEMPRE */
    return 0;
}
```

Quem lê imagina que as duas mensagens dependem do `if`, mas para o compilador o `if` controla apenas o primeiro `printf`. O segundo `printf` é um comando normal, que roda sempre. Com `saldo` igual a 50, o programa mostra "Conta bloqueada" mesmo com saldo positivo. Compilando com `gcc -Wall`, o compilador avisa sobre essa indentação enganosa. A correção é colocar chaves em volta das duas linhas. A mesma regra vale para `else`, `for` e `while` sem chaves.

## A qual if pertence o else em C

Quando há dois `if` seguidos sem chaves, o `else` em C pertence sempre ao `if` mais próximo que ainda não tem `else`, independentemente da indentação:

```c
#include <stdio.h>

int main(void) {
    int x = -1;
    if (x > 0)
        if (x > 100)
            printf("grande\n");
    else
        printf("nao positivo\n");   /* na verdade, é do if (x > 100) */
    return 0;
}
```

A indentação sugere que o `else` é do primeiro `if`, mas ele pertence ao segundo, `if (x > 100)`. Com `x` igual a -1, o primeiro `if` é falso e nada é mostrado. Esse problema é conhecido como "else pendurado" (dangling else). Com chaves, a intenção fica explícita: `if (x > 0) { if (x > 100) { ... } } else { ... }`.

## Boas práticas de chaves e indentação em C

Algumas práticas simples evitam a maioria dos erros de chaves e indentação em C:

- **Use chaves sempre**, mesmo quando o bloco tem uma linha só. Assim, acrescentar uma segunda linha depois não cria o erro do `if` que controla só o primeiro comando.
- **Indente cada nível de forma consistente**, por exemplo com 4 espaços. Tudo que está dentro de um bloco fica um nível à direita.
- **Alinhe a chave de fechamento** com a linha que abriu o bloco, para ver onde cada bloco termina.
- **Use o formatador do editor** (no VS Code, com a extensão de C/C++, o comando "Format Document") para corrigir a indentação automaticamente.
- **Compile com `gcc -Wall`**: o compilador avisa sobre indentação enganosa e sobre `else` ambíguo.

Esse cuidado é ainda mais importante para quem vem de Python, em que a indentação define os blocos. Em C, só as chaves definem.
