---
titulo: Diferença entre map e set em C++
linguagem: C++
topicos:
  - map
  - set
  - std::map
  - std::set
  - comparacao
---

# Diferença entre map e set em C++

## A diferença entre map e set em C++: chave com valor ou só a chave

A diferença entre `map` e `set` em C++ é o que cada elemento guarda. O `std::set` guarda só valores: cada elemento é a própria chave. O `std::map` guarda pares de chave e valor: cada chave está ligada a um valor, como o nome de um aluno ligado à sua nota.

Fora isso, os dois funcionam do mesmo jeito. As chaves não se repetem, ficam sempre em ordem crescente e são inseridas, buscadas e removidas em tempo proporcional a log n. Por isso, um jeito de pensar no `set` é como um `map` sem os valores.

As bibliotecas também são separadas: o `set` vem de `<set>`, e o `map` vem de `<map>`. A biblioteca padrão da linguagem C não tem nenhuma das duas estruturas.

## Quando usar set e quando usar map em C++

Use um `set` em C++ quando a pergunta é só se um valor está presente. Exemplos: "este número já apareceu?", "este aluno já entregou o trabalho?" e "quais valores diferentes existem nesta lista?".

Use um `map` em C++ quando, além de saber se a chave existe, é preciso guardar uma informação ligada a ela. Exemplos: quantas vezes cada palavra aparece, a nota de cada aluno e o telefone de cada contato.

Uma regra prática para escolher: se você só marcaria "sim" ou "não" para cada chave, use um `set`. Se você escreveria um número ou um texto ao lado de cada chave, use um `map`. Usar um `map` com valor `bool` só para marcar presença funciona, mas o `set` deixa a intenção mais clara.

## Exemplo em C++: set para saber se apareceu e map para contar

Este programa percorre o mesmo vetor e usa as duas estruturas: o `set` para saber quais valores apareceram, e o `map` para contar quantas vezes cada um apareceu.

```cpp
#include <iostream>
#include <map>
#include <set>
#include <vector>

int main() {
    std::vector<int> v = {4, 1, 4, 2, 1, 4};
    std::set<int> vistos;
    std::map<int, int> contagem;
    for (int x : v) {
        vistos.insert(x);   // guarda só o valor
        contagem[x]++;      // guarda o valor e quantas vezes apareceu
    }
    std::cout << vistos.size() << " valores diferentes\n";        // 3
    std::cout << "o 4 apareceu " << contagem[4] << " vezes\n";    // 3
    return 0;
}
```

O `set` termina com 1, 2 e 4, e não sabe quantas vezes cada um apareceu. O `map` termina com os pares (1, 2), (2, 1) e (4, 3), e responde as duas coisas: quais valores apareceram e quantas vezes.

## Operações parecidas entre map e set em C++

Muitas operações têm o mesmo nome no `map` e no `set` em C++: `insert`, `find`, `count`, `erase`, `size` e `empty`. As duas estruturas também são percorridas com um `for` de intervalo, sempre em ordem crescente de chave.

As diferenças aparecem no acesso. O `map` tem o operador `[]` e o método `at`, que devolvem o valor ligado a uma chave, e cada elemento percorrido é um par com `first` (a chave) e `second` (o valor). O `set` não tem `[]`, e cada elemento percorrido é o próprio valor. No `set`, nenhum elemento pode ser alterado no lugar. No `map`, a chave não pode ser alterada, mas o valor pode.

Existem variações: `std::multiset` e `std::multimap` aceitam chaves repetidas, e `std::unordered_set` e `std::unordered_map` não mantêm ordem, mas costumam ser mais rápidos na média.
