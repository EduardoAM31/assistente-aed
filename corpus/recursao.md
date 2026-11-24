---
titulo: Recursão em C
linguagem: C
topicos:
  - recursao
  - funcoes
  - caso base
  - pilha de chamadas
---

# Recursão em C

## O que é recursão em C

Recursão em C é quando uma função chama a si mesma para resolver uma versão menor do mesmo problema. Toda função recursiva tem duas partes: o caso base, que resolve o problema pequeno direto, sem nova chamada, e o passo recursivo, que reduz o problema e chama a função de novo.

```c
#include <stdio.h>

long long fatorial(int n) {
    if (n <= 1) {
        return 1;                  /* caso base */
    }
    return n * fatorial(n - 1);   /* passo recursivo */
}

int main(void) {
    printf("%lld\n", fatorial(5));   /* 120 */
    return 0;
}
```

O fatorial de 5 é 5 vezes o fatorial de 4, que é 4 vezes o fatorial de 3, e assim por diante, até chegar ao fatorial de 1, que é 1. Cada chamada recebe um `n` menor, e por isso a sequência de chamadas sempre chega ao caso base. O tipo `long long` aguenta até o fatorial de 20. A partir do 21, o resultado não cabe mais.

## O caso base da recursão em C e o que acontece sem ele

O caso base é o que faz uma função recursiva em C parar de chamar a si mesma. Sem ele, ou com um caso base que nunca é alcançado, as chamadas não terminam.

Cada chamada de função ocupa um espaço na pilha de chamadas, com as suas variáveis locais, e esse espaço só é liberado quando a função retorna. Numa recursão que nunca para, a pilha de chamadas acaba ficando sem espaço, e o programa costuma terminar com um erro de "stack overflow" ou de falha de segmentação.

Um erro comum é um caso base que deixa algum valor de fora. Se o fatorial tivesse o caso base `if (n == 0)`, a chamada `fatorial(-1)` passaria por -2, -3 e assim por diante, sem nunca chegar a 0. Usar `n <= 1` cobre também os valores negativos. Antes de escrever o passo recursivo, confira duas coisas: se todo valor de entrada chega ao caso base, e se cada chamada deixa o problema menor.

## Como a pilha de chamadas funciona na recursão em C

Na recursão em C, cada chamada da função tem as suas próprias variáveis, guardadas na pilha de chamadas. A chamada `fatorial(3)` acontece assim:

1. `fatorial(3)` precisa de `fatorial(2)` e fica esperando, com o seu `n` valendo 3.
2. `fatorial(2)` precisa de `fatorial(1)` e fica esperando, com o seu `n` valendo 2.
3. `fatorial(1)` chega ao caso base e devolve 1.
4. `fatorial(2)` recebe o 1 e devolve 2 × 1 = 2.
5. `fatorial(3)` recebe o 2 e devolve 3 × 2 = 6.

As chamadas vão sendo empilhadas até o caso base. Depois, elas são resolvidas na ordem inversa, da última para a primeira, como numa pilha. Cada `n` é uma variável diferente, e mudar o `n` de uma chamada não afeta as outras. É por isso que a recursão consegue "voltar" e terminar as contas que ficaram esperando.

## Recursão ou laço em C: quando usar cada um

Todo problema resolvido com recursão em C também pode ser resolvido com um laço, e o contrário também vale. O fatorial, por exemplo, pode ser calculado com um `for` que multiplica de 1 até `n`.

A recursão deixa o código mais natural quando o problema se divide em partes menores do mesmo tipo: percorrer uma árvore, ordenar com merge sort ou quick sort, resolver a Torre de Hanói e explorar todas as combinações de um conjunto. Nesses casos, a versão com laço costuma precisar de uma pilha controlada à mão, e fica mais difícil de ler.

O laço costuma ser a melhor escolha quando o problema é uma repetição simples, como somar um vetor ou calcular um fatorial. Ele não gasta espaço na pilha de chamadas a cada repetição, então não corre o risco de "stack overflow" com entradas grandes, e normalmente é um pouco mais rápido.

## O problema das chamadas repetidas na recursão em C: Fibonacci

A sequência de Fibonacci (0, 1, 1, 2, 3, 5, 8, ...) tem uma definição recursiva direta: cada termo é a soma dos dois anteriores. Escrita assim em C, a função funciona, mas fica muito lenta:

```c
int fib(int n) {
    if (n < 2) {
        return n;   /* fib(0) = 0 e fib(1) = 1 */
    }
    return fib(n - 1) + fib(n - 2);
}
```

O problema é que a função recalcula os mesmos valores muitas vezes. O `fib(5)` chama `fib(4)` e `fib(3)`, mas o `fib(4)` também chama `fib(3)`, e assim por diante. O número de chamadas cresce de forma exponencial: o `fib(40)` faz mais de 300 milhões de chamadas.

A solução é não recalcular. Uma opção é um laço que guarda os dois últimos termos. Outra é guardar num vetor os valores já calculados e consultar esse vetor antes de fazer a chamada recursiva, o que se chama memoização. Com essas formas, o `fib(40)` precisa de cerca de 40 passos.
