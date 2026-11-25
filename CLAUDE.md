# CLAUDE.md: assistente-aed

Contexto para o Claude Code trabalhar neste repositório. Leia inteiro antes de começar qualquer tarefa.

## O projeto
Assistente que responde dúvidas de iniciantes em **Algoritmos e Estruturas de Dados (AED)** usando RAG. As respostas vêm de notas em Markdown da pasta `corpus/`, baseadas nas dúvidas mais comuns em monitorias da disciplina.

Fluxo:
1. **Ingestão:** a nota é dividida em chunks (pedaços) pelas seções `##`.
2. **Embeddings:** cada chunk vira um vetor.
3. **Armazenamento:** os vetores são gravados no PostgreSQL com pgvector.
4. **Busca:** a pergunta vira um vetor, e o banco devolve os chunks mais próximos.
5. **Resposta:** o LLM recebe a pergunta e os trechos e responde citando a fonte.

## Como trabalhar neste projeto
- **Responda sempre em português.**
- **Código simples e didático.** Cada parte do projeto precisa poder ser explicada com clareza. Por isso:
  - Evite abstrações que o projeto não precisa.
  - Explique as escolhas importantes (por que essa biblioteca, por que esse formato) em poucas linhas, depois de cada etapa.
  - Avance em passos pequenos, fáceis de revisar.
- **Nunca invente resultados nem métricas.** Só entram no README números que foram medidos rodando o código de verdade.
- Antes de uma mudança grande ou difícil de desfazer, pergunte.

## Ambiente
- Windows 11 com PowerShell. A RAM é de 8 GB e é o recurso mais escasso. GPU NVIDIA com 6 GB de VRAM.
- Python 3.14 num venv em `.venv` (ativar com `.venv\Scripts\Activate.ps1`).
- **Postgres 16 + pgvector 0.8.7** no Docker Compose (serviço `db`, imagem `pgvector/pgvector:pg16`). Configuração vem do `.env`, e o modelo de variáveis está em `.env.example`.
  - Subir: `docker compose up -d`. Parar: `docker compose down`.
  - **Nunca rode `docker compose down -v` sem perguntar:** isso apaga o banco (volume `pgdata`, com as 25 notas e os vetores) e o cache dos modelos (volume `modelos`).
  - O `sql/init.sql` só roda quando o volume está vazio. Como o volume já existe, mudanças no `init.sql` são aplicadas à mão, sem apagar nada (o script é idempotente por causa do `IF NOT EXISTS`): `Get-Content sql/init.sql | docker compose exec -T db psql -U rag -d aed`. O PowerShell não aceita `<` para redirecionar a entrada, por isso o `Get-Content` com pipe.
  - **Porta 5433:** neste computador, um PostgreSQL 18 instalado no Windows (serviço `postgresql-x64-18`) já ocupa a porta 5432. Por isso o `.env` usa `POSTGRES_PORT=5433`, e o Compose publica o banco do Docker em `5433:5432`. O `.env.example` continua com 5432, o padrão.
- **Smart App Control ligado:** o Windows bloqueia DLLs nativas sem reputação. Já aconteceu com o `psycopg[binary]` e com executáveis de teste do gcc (esses rodam no WSL). Ao instalar uma dependência com código nativo, teste o `import` no venv logo em seguida. Na etapa 5, `torch` 2.15.0 (CPU) e `sentence-transformers` 6.3.0 foram instalados no venv (Python 3.14.0) e importam normalmente.
- **Ollama** roda direto no Windows, fora do Docker, para usar a GPU. Modelo: `qwen2.5:3b`, que roda 100% na GPU, com contexto de 4096 tokens. API em `http://localhost:11434`.
- A API pode rodar no venv (`uvicorn app.main:app --reload`) ou no container `api` do Compose (veja a seção "Docker (etapa 9)"). As duas usam a porta 8000, então rode uma de cada vez.
- O CI (GitHub Actions) roda em Ubuntu.

## Convenções de código
- **Funcionar em Windows e Linux:**
  - Caminhos com `pathlib`.
  - Toda configuração vem de variáveis de ambiente, lidas com `pydantic-settings`. Nada de endereço, porta ou nome de modelo fixo no código.
  - O `.gitattributes` mantém os arquivos em LF.
- **Nomes de funções, variáveis e rotas em português**, como `gerar_resposta`, `POST /documentos` e `POST /perguntas`. Use type hints.
- **O provedor do LLM fica atrás da interface `gerar_resposta(pergunta, contexto)`** (`app/geracao/base.py`). Ollama e Hugging Face são implementações dessa interface, e o provedor é escolhido pelo `.env`.
- **Banco:** driver `pg8000`, escrito só em Python, porque o Smart App Control bloqueia as DLLs do `psycopg[binary]`. Usamos a interface `pg8000.native` (parâmetros nomeados, como `:nome_arquivo`) e **SQL escrito à mão, sem ORM**. O `pgvector` tem suporte ao pg8000.
- **Testes com pytest.** Os testes não podem baixar modelos nem depender do Ollama: use um embedder e um LLM falsos (fakes). Os testes de integração usam o Postgres (no CI, como service container).
- **Dependências:** coloque em `requirements.txt` só o que for usado, com versões fixadas.
- **Commits:** pequenos, com mensagem em português que diga o que mudou. Nunca versionar `.env` nem `.venv`.

## Estrutura planejada
```
app/        main.py, config.py, db.py, schemas.py, notas.py, chunking.py, embeddings.py, busca.py
app/geracao/  __init__.py, base.py (interface e prompt), ollama.py, huggingface.py (depois)
corpus/     notas .md
avaliacao/  perguntas_rascunho.md, perguntas.jsonl, baseline_com_rag.json, baseline_sem_rag.md, avaliar.py, resultados/
sql/        init.sql
scripts/    contar_tokens.py, reindexar.py
tests/      conftest.py (banco aed_teste e fakes), test_*.py
.github/workflows/testes.yml
docker-compose.yml, Dockerfile, .dockerignore, requirements.txt, .env.example, .gitattributes, README.md
```

## Corpus (`corpus/`)
- Cerca de 25 notas, uma por dúvida comum de iniciantes.
- **Linguagem:** a disciplina usava C++ e depois passou para C, então os exemplos são em C. As notas de `map` e `set` usam C++ (`std::map`, `std::set`), porque C não tem essas estruturas na biblioteca padrão.
- **Formato de cada nota:**
  - Arquivo `corpus/<nome-em-kebab-case>.md`, sem acentos no nome.
  - Cabeçalho YAML com `titulo`, `linguagem` (`C` ou `C++`) e `topicos` (lista).
  - Um título `#` e de 3 a 5 seções `##`.
  - **Cada seção precisa fazer sentido sozinha**, com 60 a 200 palavras e uma ideia por seção. A busca devolve seções soltas, então não escreva "como vimos acima". Repita o assunto no título da seção, por exemplo "Por que o for que percorre um vetor começa em 0" em vez de "Por que começa em 0".
  - **Exemplos de código curtos e corretos.** Compile os exemplos em C com `gcc -Wall` (e os de C++ com `g++`) antes de colocar na nota, quando houver compilador disponível. Se não houver, avise.
- **Precisão técnica é prioridade.** Uma nota errada ensina o erro ao modelo. Cuidados conhecidos:
  - Em C, a indentação não muda o funcionamento do programa, ao contrário de Python. A nota explica legibilidade e o erro do `if` sem chaves com duas linhas indentadas.
  - O índice começa em 0 porque é o deslocamento a partir do início do vetor: `v[i]` é o mesmo que `*(v + i)`.
  - Acesso fora dos limites é comportamento indefinido.
- A nota-modelo é `corpus/indice-zero.md`: siga o mesmo formato.
- **Toda nota passa por revisão manual antes do commit.** Entregue as notas em lotes pequenos para facilitar a revisão.
- **Lista de notas:**
  - Parte 1, básico de C: `if-else`, `switch-case`, `laco-for`, `laco-while`, `for-vs-while`, `indentacao-e-chaves`, `vetores`, `indice-zero`, `erros-com-vetores`, `strings`, `funcoes`, `ponteiros`, `matrizes`.
  - Parte 2, estruturas e algoritmos: `alocacao-dinamica`, `lista-encadeada`, `pilha`, `fila`, `pilha-vs-fila`, `map` (C++), `set` (C++), `map-vs-set`, `busca-linear-e-binaria`, `ordenacao-simples`, `recursao`, `complexidade-big-o`.
  - Os temas vizinhos (for × while, pilha × fila, map × set) estão na lista de propósito, para a busca ter concorrência.

## Avaliação (`avaliacao/`): regras importantes
- **As perguntas de avaliação serão feitas manualmente, não pelo Claude.**
  - Não crie, complete nem reescreva `perguntas_rascunho.md` ou `perguntas.jsonl`.
  - **Não leia a pasta `avaliacao/` enquanto escreve ou edita notas do corpus.** Se as notas forem escritas com o vocabulário das perguntas, a busca fica fácil e o recall@3 sai inflado.
  - Se pedirem notas novas e o `avaliacao/perguntas_rascunho.md` ainda não existir, lembre que as perguntas devem ser escritas antes.
- **Métrica principal: recall@3 da busca.** Cada pergunta é rotulada com a **nota e a seção** corretas, não com o id do chunk, porque os ids mudam quando muda o tamanho do chunk. Conta acerto quando algum dos 3 primeiros chunks vem da seção correta.
- **Experimentos:** 2 modelos de embedding (`paraphrase-multilingual-MiniLM-L12-v2` e `multilingual-e5-small`) × 3 tamanhos de chunk (máximo de palavras/overlap): **40/8, 60/10 e sem limite**. A tabela de resultados vai no README, com a porcentagem de chunks cortados pelo limite de tokens em cada combinação. Os tamanhos foram escolhidos com a contagem de tokens da etapa 5 e conferidos com as 25 notas na etapa 7 (seção "Medições registradas"). Outras configurações, como 80/15 ou 120/20, podem ser testadas depois. A escolha final é manual.
- **Prefixos dos modelos de embedding:** o `multilingual-e5-small` exige `passage: ` no começo de cada chunk e `query: ` no começo de cada pergunta. O `paraphrase-multilingual-MiniLM-L12-v2` não usa prefixo. Esses prefixos e o prefixo com os títulos que o chunking coloca em todo chunk (`# <nota>` e `## <seção>`) contam no limite de tokens do modelo, mesmo não contando no limite de palavras do chunking.
- **Limites de tokens (medidos):** o MiniLM tem `max_seq_length` = 128 e o e5-small tem 512. Texto além do limite é ignorado no cálculo do vetor, sem erro. Só o vetor é afetado: o texto do chunk continua inteiro no banco e vai inteiro para o LLM.
- **Baseline sem RAG:** o `qwen2.5:3b` respondeu sozinho, sem contexto, à pergunta "Por que o índice de vetores em C começa em 0?". A resposta foi longa e com erros factuais: disse que os arrays de C são "tipados dinamicamente", que C++ conta a partir de 1 e que C deixa escolher o índice inicial. A resposta está em `avaliacao/baseline_sem_rag.md`, colocada à mão pelo usuário, e a resposta com RAG está em `avaliacao/baseline_com_rag.json`, para a comparação no README.
- **`avaliacao/perguntas.jsonl` (etapa 10):** foi escrito e rotulado à mão pelo usuário. Os rótulos foram revisados uma vez, depois da 1ª rodada (veja "Medições registradas"), e **agora o arquivo está congelado**. Mudar uma pergunta ou um rótulo depois de ver os erros faz a pergunta passar por causa da mudança, e não por causa da busca. Se ele mudar de novo, todas as combinações da etapa 11 precisam ser medidas outra vez, e a mudança fica registrada.
  - **Formato:** uma linha JSON por pergunta, com `id`, `pergunta`, `nota` (o `nome_arquivo`) e `secao` (o título exato da seção `##`). Uma pergunta que nenhuma nota cobre tem `"sem_resposta": true` e fica fora do recall. Uma variante com erro de digitação tem `variante_de`, com o id da principal, e o mesmo rótulo dela.
  - **Regras da rotulagem:** uma seção por pergunta. Letra minúscula no lugar de maiúscula não conta como erro de digitação. Já contam abreviação ("q", "pq"), acento faltando, palavra errada ("identação") e palavra faltando. **Não escreva notas para cobrir as perguntas sem resposta:** essa decisão é do usuário.
- **`avaliacao/avaliar.py`:** rode na raiz, com o venv ativo e o banco no ar, com `python -m avaliacao.avaliar`. Não precisa da API nem do Ollama, e usa o banco do `.env` (o `aed`).
  - Confere o jsonl e os rótulos no `corpus/` antes de medir. Se um rótulo não existir, para e mostra os títulos que a nota tem.
  - Busca com `busca.buscar`, com k=3 fixo no script.
  - Calcula o recall@3 das principais e, à parte, o das variantes, e lista os erros e as perguntas sem resposta.
  - Grava um JSON em `avaliacao/resultados/` (versionado). O nome do arquivo tem a data, o modelo e o chunking.
  - **O banco não guarda com qual modelo nem com qual chunking os vetores foram gerados.** Por isso, o `avaliar.py` avisa quando o número de chunks do banco não bate com o que o chunking do `.env` gera para o corpus, e quando o vetor guardado de 5 chunks fica a mais de 0,01 do vetor recalculado com o modelo do `.env`. **Rodada com aviso não vale como medição.**
  - **Os dois recalls não medem o mesmo grupo de perguntas.** O das variantes vem só das 23 perguntas que têm variante. Para medir o efeito do erro de digitação, compare cada variante com a sua principal (veja "Medições registradas").
- **Correção de erros de digitação** (corrigir as palavras da pergunta pela similaridade com o vocabulário do corpus): só depois da etapa 11. O "antes" é o recall das variantes da etapa 10.

## Estilo das respostas do assistente
As respostas devem ser **curtas e diretas**, para iniciantes. Para isso:
- O prompt manda responder em poucas frases, com no máximo um exemplo curto de código, usando só os trechos recebidos e citando a fonte (nota e seção).
- Se os trechos não respondem a pergunta, o modelo deve dizer que não sabe.
- No Ollama: `num_predict` para limitar o tamanho da resposta e `temperature` baixa.

## Etapa atual: 12 (README final)
Objetivo (do roteiro): o README final, com diagrama, prints, resultados, limitações e a comparação com e sem RAG.

**O que já existe:**
- **Resultados medidos:**
  - o recall@3 das 2 rodadas da etapa 10;
  - a tabela das 6 combinações da etapa 11, com chunks, % cortados e os 3 recalls;
  - a contagem de tokens da etapa 7;
  - as medições do Docker da etapa 9.

  Está tudo em "Medições registradas" e na seção do Docker. **Só esses números entram no README.**
- **A comparação com e sem RAG:** o `avaliacao/baseline_sem_rag.md` e o `avaliacao/baseline_com_rag.json`, os dois com a pergunta "Por que o índice de vetores em C começa em 0?". A resposta com RAG foi gerada na etapa 6, com o MiniLM e o 60/10.
- **Observações da geração:** etapas 6 e 7, feitas com o MiniLM e o 60/10. São observações, e não métricas.
- **A configuração final:** e5-small sem limite, no `.env`, no `.env.example` e no banco.

**O que o README precisa ter** (do roteiro e da seção "README" abaixo):
- o que o projeto faz e o fluxo do RAG (ingestão, chunking, embeddings, pgvector, busca e geração), com um diagrama;
- como rodar: Docker Compose, Ollama no Windows, `.env`, ingestão das notas e as rotas;
- os resultados, com os acertos junto da porcentagem e a explicação da revisão dos rótulos e da amostra pequena;
- a comparação com e sem RAG;
- as limitações (as do modelo de 3B, as da avaliação e as do corpus);
- como o projeto foi feito, com honestidade: "notas escritas com auxílio de IA e revisadas manualmente, a partir das dúvidas recorrentes das monitorias".

**A decidir antes de começar (é do usuário):**
- **A ordem do PR dos ajustes da geração:** antes ou depois do README. Fazer antes deixa o README descrever a geração final. Fazer depois deixa o README pronto mais cedo, e ele é atualizado depois.
- **Refazer a resposta com RAG do baseline com a configuração final?** A de hoje é do MiniLM com 60/10. Se não refizer, o README precisa dizer com qual configuração ela foi gerada.
- **O diagrama:** em Mermaid, que o GitHub desenha, ou como imagem.
- **Os prints:** quais telas (o `/docs`, uma resposta do `POST /perguntas`, a saída do `avaliar.py`). As imagens são tiradas pelo usuário, e o Claude só indica onde elas entram.
- **A língua do README:** só em português, ou também em inglês.

**Cuidados:**
- **Nenhum número novo sem medir.** Se faltar algum número, meça antes ou deixe o assunto fora do README.
- **Os dois recalls da etapa 10 e a revisão dos rótulos entram com a explicação do viés.**
- **Com 53 perguntas, uma diferença de 1 ou 2 acertos não permite dizer que uma configuração é melhor.**

**Pronto quando:**
- [ ] O README tem todas as partes acima, com os números de "Medições registradas" e nenhum outro.
- [ ] Os comandos do README foram testados numa execução do zero.
- [ ] O usuário revisou o texto.

Ao terminar, marque a etapa 12 no roteiro.

## Docker (etapa 9): como usar e o que foi medido
- **Subir tudo:** `docker compose up -d`, com o `db` e a `api` (porta 8000). **Só o banco, para usar a API no venv:** `docker compose up -d db`, ou `docker compose stop api`. As duas APIs usam a porta 8000.
- **Dentro do container,** a API usa `db:5432` (o `environment:` do Compose vale mais que o `.env`) e `http://host.docker.internal:11434`. O Ollama não precisou de `OLLAMA_HOST=0.0.0.0`: ele continua escutando só em `127.0.0.1`.
- **Os modelos de embedding ficam no volume `modelos`** (`HF_HOME=/modelos`), e são baixados na primeira chamada que precisa deles. Depois de recriar o container, o modelo carrega do volume, sem internet (testado com `HF_HUB_OFFLINE=1`).
- **Medido (Docker Desktop no Windows):**
  - imagem de **2,11 GB**, com build de 132 s sem cache. 817 MB são do `torch` CPU;
  - primeiro `POST /embeddings` (12 chunks) em 36,6 s, contando o download de 458 MB do MiniLM. Depois de recriar o container, a primeira busca levou 6,6 s;
  - RAM, numa VM de 2,84 GiB: a API teve **pico de 1.236 MiB** e fica em **840 MiB** parada, com o modelo carregado. O `db` usa cerca de 58 MiB. O `POST /embeddings?refazer=true` dos 324 chunks não foi medido no container.
  - **Decisão do usuário:** o tamanho da imagem e o uso de RAM são aceitáveis.
- **Conferido na imagem:** o `.env` não está nela, o processo roda como o usuário `app` (sem root), o Python é o 3.14.10 e o torch é o `2.15.0+cpu`.
- **CI:** o job `imagem` monta a imagem, confere que o `.env` não entra nela e que `import app.main` funciona. No PR #8, em 2 execuções, o job `imagem` levou de 106 s a 134 s (92 s a 123 s de build) e o `testes` de 85 s a 89 s (62 s a 63 s de instalação). No push na `main` depois do merge, foram 110 s e 89 s.

## Pendência: ajustes da geração (PR pequeno e separado, sem misturar com outra etapa)
Vem das 4 respostas com problema do teste manual da etapa 7 (seção abaixo):
- **Resposta cortada pelo `num_predict`:** subir o `LLM_NUM_PREDICT` para 400 a 512 e pedir no prompt só as linhas principais do exemplo, sem `#include` e `main`, e sem copiar o trecho inteiro. Os exemplos das notas são programas completos e passam do limite de 6 linhas que o prompt pede. Opcional: um campo `cortada` na resposta da API quando `done_reason` for `length`.
- **Falso "não sei":** dizer "não sei" só se nenhum trecho tratar do assunto, e responder com o que os trechos dizem quando eles trazem a resposta só em parte. Teste nas duas direções (perguntas fora do corpus e perguntas do corpus), com 1 ou 2 rodadas no máximo.
- Os outros 2 problemas (o detalhe errado sobre a lista encadeada e a resposta vaga sobre laços aninhados) são limitações do modelo de 3B e vão para o README. **Não edite as notas para corrigi-los.**
- **Não troque o `qwen2.5:3b`:** a comparação com e sem RAG do README usa esse modelo.
- Depois do ajuste, repita as mesmas perguntas e outras que não foram usadas no ajuste, e registre o que melhorou e o que não melhorou. A qualidade das respostas é avaliada só por observação, e a única métrica do projeto é o recall@3 da busca.
- **Desde a etapa 11, a busca usa o e5 sem limite:** o LLM recebe 3 seções inteiras, cada uma com até 411 tokens, em vez de pedaços de 60 palavras. As observações das etapas 6 e 7 foram feitas com o MiniLM e o 60/10, e a geração ainda não foi testada com a configuração nova. Teste as mesmas perguntas antes de ajustar o prompt e confira o tamanho do prompt no log do Ollama (o `num_ctx` é 4096).

## Teste manual da etapa 7
Foram 10 perguntas escolhidas à mão, sem consultar a pasta `avaliacao/`, com as 25 notas no banco (MiniLM, 60/10, k=3, `qwen2.5:3b` na GPU). São observações, e não métricas: a medida da busca é o recall@3 da etapa 10.
- **Busca:** nas 9 perguntas cobertas pelas notas, as fontes vieram da nota esperada. Em todas as 10, as `fontes` bateram com o `GET /busca`.
- **Respostas corretas e curtas (6):** pilha × fila, `malloc(10)`, chave no `map` sem criar (`count`, `find` e `contains`), por que a busca binária precisa do vetor ordenado e recursão sem caso base. A pergunta fora do corpus (Dijkstra) também acertou, com "Não sei responder isso com base nas notas."
- **Respostas com problema (4):**
  - **"Qual a diferença entre bubble sort e insertion sort?"** respondeu "Não sei…", embora a seção de comparação estivesse entre os trechos recebidos. É um falso "não sei".
  - **"Como tirar números repetidos de um vetor em C++?"** copiou um trecho inteiro, com o exemplo longo, e **foi cortada pelo `num_predict` 256** (`done_reason: "length"`, com o aviso no log). Na etapa 6, nenhuma das 5 perguntas tinha sido cortada.
  - **"Como eu libero a memória de uma lista encadeada?"** acertou a ideia de guardar o próximo nó antes do `free`, mas disse para "chamar a função `liberar` para cada nó", o que está errado: a função percorre a lista inteira.
  - **"Dois for um dentro do outro é sempre O(n²)?"** ficou vaga: disse que "depende", sem explicar o caso de tamanhos diferentes (O(n × m)) que a nota traz.
- **Tempo:** a primeira pergunta levou 13 s, porque carrega os modelos. As outras levaram de 0,3 a 2,8 s.
- **Para o README e as próximas etapas:** essas falhas são do modelo de 3B, já que a busca trouxe os trechos certos. Ajustes possíveis, sem prometer resultado: um `num_predict` maior, ou proibir no prompt que o modelo copie os trechos.

## Resultados da geração (etapa 6)
Medidos rodando o código, com 5 perguntas escolhidas à mão (MiniLM, 60/10, k=3, `qwen2.5:3b` na GPU). São observações, e não métricas.
- **As 5 respostas terminaram com `done_reason: "stop"`**, nenhuma cortada. Usaram de 10 a 135 tokens de resposta, e o prompt ficou entre 471 e 598 tokens, bem abaixo de `num_ctx` 4096.
- **Tempo:** a primeira pergunta depois de subir a API levou de 12 a 20 s, porque carrega o modelo de embedding e o LLM. As seguintes levaram de 0,3 a 1,9 s.
- **Fora do corpus:** com "Como funciona uma árvore binária de busca?", o modelo respondeu "Não sei responder isso com base nas notas.", que é a frase pedida no prompt.
- **As `fontes` bateram com o `GET /busca`** nas 5 perguntas.
- **Com o Ollama desligado,** a rota devolveu 503 com a mensagem de conexão, e o `/saude` continuou respondendo.
- **Ajuste do prompt (2 rodadas).** Na primeira versão, o modelo:
  - inventou que `strcmp("sim", "SIM")` devolve 0 "independentemente de maiúsculas";
  - deu um exemplo de código longo;
  - respondeu "Não sabe." para a pergunta fora do corpus.

  A segunda versão passou a pedir para não acrescentar nada além dos trechos, limitar o exemplo a 6 linhas e usar uma frase fixa quando não souber. Com ela, esses três problemas não apareceram nas mesmas perguntas.
- **Limitações que continuam, para o README:**
  - o modelo quase não cita o número do trecho (`[1]`), mesmo com o pedido no prompt;
  - às vezes repete a pergunta no começo da resposta;
  - usa termos em inglês, como "undefined behavior";
  - um modelo de 3B pode inventar detalhes mesmo com o contexto certo, como mostrou o caso do `strcmp`.
- **Resposta com RAG para a pergunta do baseline:** foi guardada num JSON, com o modelo, os parâmetros e a data (2026-11-23), e entregue ao usuário para ele salvar em `avaliacao/`.

## Medições registradas (para o README)
Feitas rodando o código. A medição atual do chunking é a da etapa 7, com as 25 notas. A da etapa 5, com as 13 notas da parte 1, fica como histórico.

**Recall@3 da busca (etapa 10).** Rodadas em 2026-11-25, com MiniLM, 60/10, k=3 e 324 chunks no banco. Nenhuma das duas teve aviso: o número de chunks bate com o corpus, e a distância entre o vetor guardado e o recalculado foi 0,000000. São 79 perguntas: 53 principais, 23 variantes com erro de digitação e 3 sem resposta no corpus.

| Rodada | Rótulos | recall@3 das principais | recall@3 das variantes | Arquivo em `avaliacao/resultados/` |
|---|---|---|---|---|
| 1ª | originais | 54,7% (29 de 53) | 34,8% (8 de 23) | `2026-11-25_0945_..._60-10.json` |
| **2ª (referência da etapa 11)** | revisados | **58,5% (31 de 53)** | **34,8% (8 de 23)** | `2026-11-25_0957_..._60-10.json` |

- **A revisão dos rótulos:** depois da 1ª rodada, o usuário viu que o rótulo da pergunta 4 estava errado e revisou os rótulos das 76 perguntas com resposta. Mudaram 2 seções, nenhuma nota e nenhum texto de pergunta:
  - **4** ("quando que eu uso o switch?"): de "Como funciona o switch em C" para "Quando usar switch ou if-else em C";
  - **78** ("o que significa dizer que um algoritmo tem complexidade O(n)?"): de "Exemplos de O(1), O(n) e O(n²) em C" para "O que é a notação Big-O na análise de algoritmos".

  **As 2 mudanças foram em perguntas que tinham errado na 1ª rodada, e as 2 passaram a acertar.** É o viés de revisar depois de ver os erros: um rótulo errado só aparece quando a pergunta erra. Por isso, o README mostra as duas rodadas, com essa explicação. Nenhuma das 2 tem variante, então o recall das variantes não mudou.
- **Os dois recalls não medem o mesmo grupo de perguntas.** Nas duas rodadas, as principais que têm variante acertaram só 8 de 23 (34,8%), o mesmo número das variantes:
  - 6 pares acertaram nas duas versões e 13 erraram nas duas;
  - em 2 pares, só a principal acertou (5 e 16);
  - em 2 pares, só a variante acertou (1 e 35).

  Neste conjunto, o erro de digitação não mudou o recall total. A diferença entre o recall das principais e o das variantes vem das perguntas: as principais que ganharam variante são mais difíceis que a média.
- **Nos 22 erros das principais da 2ª rodada:**
  - 4 trouxeram a nota certa, mas com outra seção: 10, 25, 53 e 76;
  - em 10, a mesma seção ocupou mais de uma das 3 posições, porque o 60/10 divide a seção em vários chunks.
- **Sem resposta no corpus:** nas 3 perguntas, o chunk mais perto ficou a uma distância de 0,47 a 0,53, nas duas rodadas.

**Experimentos (etapa 11): modelo de embedding × tamanho de chunk.** Rodadas em 2026-11-25, com os rótulos revisados, k=3 e as 79 perguntas. Cada combinação foi reindexada com `python -m scripts.reindexar`, passando a configuração por variáveis de ambiente, sem mudar o `.env`. Nenhuma rodada teve aviso, e a distância entre o vetor guardado e o recalculado foi 0,000000 em todas. Antes, reindexar o MiniLM com 60/10 reproduziu a 2ª rodada da etapa 10 exatamente: os mesmos acertos, os mesmos erros e as mesmas distâncias.

| Modelo | Chunking | Chunks | Cortados pelo limite de tokens | Principais (53) | Variantes (23) | Principais com variante (23) |
|---|---|---|---|---|---|---|
| MiniLM | 40/8 | 484 | 2% | 58,5% (31) | 30,4% (7) | 34,8% (8) |
| MiniLM | 60/10 | 324 | 31% | 58,5% (31) | 34,8% (8) | 34,8% (8) |
| MiniLM | sem limite | 107 | 100% | 60,4% (32) | 52,2% (12) | 39,1% (9) |
| e5-small | 40/8 | 484 | 0% | 66,0% (35) | 52,2% (12) | 47,8% (11) |
| e5-small | 60/10 | 324 | 0% | 73,6% (39) | 65,2% (15) | 60,9% (14) |
| e5-small | sem limite | 107 | 0% | **77,4% (41)** | **82,6% (19)** | **69,6% (16)** |

- **O e5 ficou acima do MiniLM nas 3 configurações.** O pior resultado do e5 (35 de 53) tem 3 acertos a mais que o melhor do MiniLM (32 de 53).
- **No MiniLM, as 3 configurações ficaram a no máximo 1 pergunta uma da outra** (31, 31 e 32). Pela amostra pequena, não dá para dizer que uma é melhor. Isso vale mesmo para o "sem limite", em que todos os chunks passam dos 128 tokens e o fim das seções é ignorado no vetor.
- **No e5, o recall subiu com o tamanho do chunk:** 35, 39 e 41 de 53. Entre o 60/10 e o "sem limite", a diferença é de 2 perguntas, dentro do que a amostra não permite separar.
- **Variantes:**

  | Combinação | Pares em que só a principal acertou | Pares em que só a variante acertou |
  |---|---|---|
  | MiniLM 40/8 | 1 (16) | nenhum |
  | MiniLM 60/10 | 2 (5 e 16) | 2 (1 e 35) |
  | MiniLM sem limite | 1 (25) | 4 (1, 10, 35 e 58) |
  | e5, nas 3 configurações | nenhum | de 1 a 3 |

  Neste conjunto, o erro de digitação quase não fez a busca errar uma pergunta que a versão correta acertava. Com 23 pares, é uma observação, e não uma conclusão.
- **Seção repetida no top 3:** foi contada nos erros das principais. Ela aparece em 10 a 14 erros com 40/8 e 60/10, e em nenhum com "sem limite", em que cada seção é um chunk só.
- **Distâncias:** nas perguntas sem resposta, o chunk mais perto ficou a 0,46 a 0,57 no MiniLM e a 0,11 a 0,14 no e5. O e5 dá distâncias bem menores em geral, então **distâncias de modelos diferentes não se comparam**.
- **Tempo de reindexação:** de 20 a 37 s por combinação, contando o carregamento do modelo. O e5 já estava no cache, por causa da contagem de tokens da etapa 7.
- Os arquivos estão em `avaliacao/resultados/`. O `…_1036_…_60-10.json` é a conferência da reindexação.
- **Configuração final, escolhida pelo usuário: e5-small sem limite.** O `.env` e o `.env.example` foram trocados para ela, e o banco `aed` foi reindexado: 25 notas e 107 chunks, com os vetores gerados em 25 s. O `avaliar.py` reproduziu o resultado da tabela, 41, 19 e 16 acertos, sem aviso (`…_1059_…_sem-limite.json`).
- **A API do container foi recriada com `--build`** e leu a configuração nova. A primeira busca levou 37 s, porque baixou o e5 para o volume `modelos`. A segunda levou 0,5 s. Depois da primeira busca, a API usava 1,098 GiB de RAM, e o `db`, 63 MiB. A busca da API devolveu as mesmas seções que a do venv.

**Corpus completo (etapa 7): 25 notas, 107 seções.**
- **Chunks:** 484 com 40/8, 324 com 60/10 e 107 sem limite. Também medidos: 231 com 80/15, 212 com 100/15, 170 com 120/20 e 113 com 150/25. Com a parte 2, o 150/25 voltou a ser diferente de "sem limite".
- **No banco, depois da ingestão completa:** 25 documentos e 324 chunks (60/10). São 285 chunks de 22 notas em C e 39 de 3 notas em C++, todos com vetor de 384 dimensões do MiniLM. `POST /embeddings` dos 324 chunks levou 54 s, incluindo o carregamento do modelo.
- **Tokens por chunk.** O chunk inclui o prefixo `# nota` / `## seção` e, no e5, também `passage: `.

| Config | Chunks | MiniLM: mediana / máx. / acima de 128 | e5-small: mediana / máx. / acima de 512 |
|---|---|---|---|
| 40/8 | 484 | 88 / 145 / 8 (2%) | 90 / 147 / 0 |
| 60/10 | 324 | 118 / 188 / 102 (31%) | 120 / 190 / 0 |
| sem limite | 107 | 266 / 409 / 107 (100%) | 268 / 411 / 0 |

**Histórico (etapa 5): 13 notas da parte 1, 53 seções.**

| Config | Chunks | MiniLM: mediana / máx. / acima de 128 | e5-small: mediana / máx. / acima de 512 |
|---|---|---|---|
| 40/8 | 230 | 88 / 141 / 3 (1%) | 90 / 143 / 0 |
| 60/10 | 155 | 118 / 179 / 54 (35%) | 120 / 181 / 0 |
| sem limite | 53 | 262 / 321 / 53 (100%) | 264 / 323 / 0 |

- **`max_seq_length`:** 128 no MiniLM e 512 no e5-small. **Dimensão 384 nos dois**, conferida ao carregar cada modelo: `get_embedding_dimension()` no código e `vector_dims(embedding)` no banco.
- Os números de tokens vêm do `scripts/contar_tokens.py`, que lê o modelo, o prefixo de documento e o dispositivo do `.env`, como a API. Rode na raiz do projeto com `python -m scripts.contar_tokens`. Para medir o e5 sem mexer no `.env`, defina `EMBEDDING_MODELO` e `EMBEDDING_PREFIXO_DOCUMENTO` como variáveis de ambiente antes de rodar.

## Roteiro (atualize os checkboxes ao concluir cada etapa)
- [x] 1. Ambiente: Docker Compose com Postgres + pgvector, venv, Ollama testado.
- [x] 2. Corpus, parte 1: perguntas de rascunho (feitas manualmente) e depois as 13 notas de básico de C.
- [x] 3. API e banco: FastAPI, `config.py` com `.env`, tabelas `documentos` e `chunks` com `vector(384)` no `init.sql`, `POST /documentos`.
- [x] 4. Chunking: por seção `##`, com tamanho máximo e overlap, e o título da nota no começo de cada chunk. Mais os testes unitários.
- [x] 5. Embeddings e busca: top-k por distância de cosseno (`<=>`) e uma rota de depuração da busca.
- [x] 6. Geração: interface `gerar_resposta`, provedor Ollama, prompt com trechos numerados e citação, `POST /perguntas`.
- [x] 7. Corpus, parte 2: as 12 notas restantes, ingestão completa e teste manual com 10 perguntas.
- [x] 8. Testes e CI: pytest com fakes e GitHub Actions.
- [x] 9. Docker: `Dockerfile` da API (torch só para CPU) e Compose completo.
- [x] 10. Avaliação: `perguntas.jsonl` (feito manualmente) e `avaliar.py` calculando o recall@3.
- [x] 11. Experimentos: modelo de embedding × tamanho de chunk.
- [ ] 12. README final (diagrama, prints, resultados, limitações, comparação com e sem RAG).

## README
- O README deve ser honesto sobre como o projeto foi feito. Por exemplo: "notas escritas com auxílio de IA e revisadas manualmente, a partir das dúvidas recorrentes das monitorias".
- Sem métricas que não foram medidas.