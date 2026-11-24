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
  - **Nunca rode `docker compose down -v` sem perguntar:** isso apaga o banco.
  - O `sql/init.sql` só roda quando o volume está vazio. Como o volume já existe, mudanças no `init.sql` são aplicadas à mão, sem apagar nada (o script é idempotente por causa do `IF NOT EXISTS`): `Get-Content sql/init.sql | docker compose exec -T db psql -U rag -d aed`. O PowerShell não aceita `<` para redirecionar a entrada, por isso o `Get-Content` com pipe.
  - **Porta 5433:** neste computador, um PostgreSQL 18 instalado no Windows (serviço `postgresql-x64-18`) já ocupa a porta 5432. Por isso o `.env` usa `POSTGRES_PORT=5433`, e o Compose publica o banco do Docker em `5433:5432`. O `.env.example` continua com 5432, o padrão.
- **Smart App Control ligado:** o Windows bloqueia DLLs nativas sem reputação. Já aconteceu com o `psycopg[binary]` e com executáveis de teste do gcc (esses rodam no WSL). Ao instalar uma dependência com código nativo, teste o `import` no venv logo em seguida. Na etapa 5, `torch` 2.15.0 (CPU) e `sentence-transformers` 6.3.0 foram instalados no venv (Python 3.14.0) e importam normalmente.
- **Ollama** roda direto no Windows, fora do Docker, para usar a GPU. Modelo: `qwen2.5:3b`, que roda 100% na GPU, com contexto de 4096 tokens. API em `http://localhost:11434`.
- Durante o desenvolvimento, a API roda no venv. Ela só entra num container na etapa 9.
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
avaliacao/  perguntas_rascunho.md, perguntas.jsonl, baseline_sem_rag.md, avaliar.py
sql/        init.sql
scripts/    contar_tokens.py
tests/       (com conftest.py a partir da etapa 8)
.github/workflows/testes.yml
docker-compose.yml, Dockerfile, requirements.txt, .env.example, .gitattributes, README.md
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
- **Experimentos:** 2 modelos de embedding (`paraphrase-multilingual-MiniLM-L12-v2` e `multilingual-e5-small`) × 3 tamanhos de chunk (máximo de palavras/overlap): **40/8, 60/10 e sem limite**. A tabela de resultados vai no README, com a porcentagem de chunks cortados pelo limite de tokens em cada combinação. Os tamanhos foram escolhidos com a contagem de tokens da etapa 5, feita só nas 13 notas da parte 1. Depois da parte 2 do corpus (etapa 7), refaça a contagem, e outras configurações podem ser testadas. A escolha final é manual.
- **Prefixos dos modelos de embedding:** o `multilingual-e5-small` exige `passage: ` no começo de cada chunk e `query: ` no começo de cada pergunta. O `paraphrase-multilingual-MiniLM-L12-v2` não usa prefixo. Esses prefixos e o prefixo com os títulos que o chunking coloca em todo chunk (`# <nota>` e `## <seção>`) contam no limite de tokens do modelo, mesmo não contando no limite de palavras do chunking.
- **Limites de tokens (medidos):** o MiniLM tem `max_seq_length` = 128 e o e5-small tem 512. Texto além do limite é ignorado no cálculo do vetor, sem erro. Só o vetor é afetado: o texto do chunk continua inteiro no banco e vai inteiro para o LLM.
- **Baseline sem RAG:** o `qwen2.5:3b` respondeu sozinho, sem contexto, à pergunta "Por que o índice de vetores em C começa em 0?". A resposta foi longa e com erros factuais: disse que os arrays de C são "tipados dinamicamente", que C++ conta a partir de 1 e que C deixa escolher o índice inicial. A resposta será colocada manualmente em `avaliacao/baseline_sem_rag.md`, para comparar com a resposta com RAG no README.

## Estilo das respostas do assistente
As respostas devem ser **curtas e diretas**, para iniciantes. Para isso:
- O prompt manda responder em poucas frases, com no máximo um exemplo curto de código, usando só os trechos recebidos e citando a fonte (nota e seção).
- Se os trechos não respondem a pergunta, o modelo deve dizer que não sabe.
- No Ollama: `num_predict` para limitar o tamanho da resposta e `temperature` baixa.

## Etapa atual: 8 (testes e CI)
Objetivo (do roteiro): pytest com fakes e GitHub Actions.

**O que já existe:**
- **144 testes** em `tests/`, que rodam sem banco, sem Ollama e sem baixar modelos:
  - `test_notas.py` e `test_chunking.py`, que também passam as 25 notas do corpus pelo leitor e pelo chunker;
  - `test_embeddings.py`, com modelo falso;
  - `test_geracao_base.py`, `test_geracao_ollama.py` (com `httpx.MockTransport`) e `test_geracao_provedor.py`.
- O `pytest.ini` coloca a raiz do projeto no caminho de importação.
- Os módulos `app/chunking.py`, `app/notas.py`, `app/embeddings.py` e `app/geracao/` não leem o `.env`, e por isso os testes deles rodam no CI sem configuração. `app/config.py`, `app/db.py`, `app/busca.py` e `app/main.py` leem o `.env` ao serem importados.

**O que fazer nesta etapa:**
- **Testes de integração das rotas** (`POST /documentos`, `POST /embeddings`, `GET /busca`, `POST /perguntas`, `GET /saude`) com o `TestClient` do FastAPI e o Postgres de verdade. O embedder e o LLM continuam falsos. Os pontos para trocar por fakes são `busca.modelo_configurado` e `main.provedor_configurado`.
- **`.github/workflows/testes.yml`** (Ubuntu):
  - Postgres com pgvector como service container;
  - instalar o `torch` pelo índice CPU antes do `requirements.txt` (veja a observação das etapas 8 e 9);
  - definir as variáveis do `.env` no próprio workflow, porque o `.env` não é versionado;
  - aplicar o `sql/init.sql` antes dos testes.
- **Nenhum teste pode baixar modelo nem depender do Ollama.**

**Padrões sugeridos para a etapa 8 (confirme com o usuário antes de implementar):**
- **Banco de teste separado: `aed_teste`.** Os testes de integração apagam as tabelas, então nunca podem rodar no banco de desenvolvimento (`aed`), que tem as 25 notas e os vetores. O `tests/conftest.py` define `POSTGRES_DB=aed_teste` **antes de qualquer import de `app`** (o `settings` é criado na importação, e a variável de ambiente vale mais que o `.env`). A fixture que limpa as tabelas só roda se `settings.postgres_db` terminar em `_teste`, e levanta erro se não terminar.
  - Criação única no ambiente local (PowerShell): `docker compose exec db psql -U rag -d aed -c "CREATE DATABASE aed_teste"` e depois `Get-Content sql/init.sql | docker compose exec -T db psql -U rag -d aed_teste`.
  - No CI, o service container já nasce com `POSTGRES_DB=aed_teste`.
- **Marcador `integracao`**, registrado no `pytest.ini`. Localmente, se o banco não responde, esses testes são **pulados** com uma mensagem clara, e `pytest -m "not integracao"` roda só os que não precisam de banco. No CI (a variável `CI=true`, que o GitHub Actions define), eles **falham em vez de pular**, para um problema de banco não passar despercebido.
- **Fakes.** Troque `busca.modelo_configurado` e `main.provedor_configurado` com `monkeypatch`.
  - Modelo falso com `encode` que devolve vetores determinísticos de 384 dimensões, escolhidos para a ordem da busca ser previsível (por exemplo, uma palavra-chave decide o eixo do vetor).
  - LLM falso que guarda o contexto recebido, para o teste conferir que os chunks certos chegaram, e outro que levanta `ErroProvedorLLM`, para o caso do 503.
- **Workflow em `pull_request` e em `push` na `main`.** Cada etapa entra por PR, e o push na `main` confere o resultado depois do merge.
- **Python no CI igual ao local (3.14).** Confira que o `actions/setup-python` oferece essa versão. Use o cache de pip.
- **Dependências no CI:** o `torch` pelo índice CPU primeiro e depois o `requirements.txt`, mesmo que os testes não usem o torch: assim o CI confere que as versões fixadas instalam no Linux, o que o Dockerfile da etapa 9 também vai precisar. Se o tempo ou o espaço pesar, a alternativa é pular `torch` e `sentence-transformers` no CI, já que os testes usam fakes. Diga ao usuário o tempo medido e deixe a escolha com ele.
- **Variáveis do `.env` no workflow:** `cp .env.example .env`, com `POSTGRES_DB: aed_teste` em `env:` do job. Isso também confere que o `.env.example` está completo, porque o `Settings` exige todas as variáveis. O `psql` vem instalado nos runners Ubuntu (confira) e aplica o `sql/init.sql`.

**Passos sugeridos (pequenos, um commit por passo, explicando as escolhas no fim de cada um):**
1. `pytest.ini` com o marcador e `tests/conftest.py` com o banco de teste, a proteção do nome e as fixtures (cliente, tabelas limpas, fakes).
2. Testes de integração:
   - `GET /saude`;
   - `POST /documentos`: 201 na primeira vez, 200 no reenvio sem duplicar, 422 para extensão errada, UTF-8 inválido e nota sem frontmatter, e `quantidade_chunks` correto;
   - o reenvio de uma nota apaga os vetores dela;
   - `POST /embeddings`: gera os vetores, devolve 0 na segunda chamada, e `?refazer=true` recalcula todos;
   - `GET /busca`: a ordem pela distância, o `k` respeitado, e 422 para `k=0` e pergunta vazia;
   - `POST /perguntas`: 409 sem embeddings, 200 com as fontes certas e o contexto certo no LLM falso, 503 quando o provedor falha e 422 para pergunta vazia ou só com espaços.
3. Correções pequenas que os testes de integração vão expor (pendências de revisões anteriores), cada uma com teste:
   - **banco fora do ar** vira **503 com mensagem clara** nas rotas que usam o banco. O erro do pg8000 nesse caso é `pg8000.exceptions.InterfaceError` (o `db.banco_responde` já o trata). Prefira um único tratamento em `main.py` a repetir `try/except` em cada rota. Faça o mesmo para o modelo de embedding que não pôde ser baixado.
   - **tamanho máximo da pergunta** em `PerguntaEntrada` (500 a 1000 caracteres). Com um prompt maior que `OLLAMA_NUM_CTX`, o Ollama corta o começo do texto sem avisar, e as instruções do `system` podem se perder.
   - `test_importar_embeddings_nao_carrega_o_torch` confere `sys.modules` e depende da ordem dos testes: se outro teste importar o torch, ele falha. Faça a checagem num subprocesso (`python -c`).
   - o aviso de `httpx` obsoleto no `TestClient`: conferir ao rodar os testes de integração. Num teste simples feito na revisão do PR #6 (fastapi 0.165.0, httpx 0.28.1), nenhum aviso apareceu.
   - opcional: no upsert de `db.salvar_documento`, trocar o `SELECT` antes do `INSERT` por `RETURNING (xmax = 0) AS criado`, que diz se a linha foi criada ou atualizada numa consulta só.
4. `.github/workflows/testes.yml`.
5. Abrir o PR e conferir no GitHub que o workflow passa. Registre o tempo do job.

**Pronto quando:**
- [ ] `pytest` passa no ambiente local com o banco de teste, e `pytest -m "not integracao"` passa sem banco.
- [ ] Rodar a suíte inteira não muda nada no banco `aed` (confira `SELECT count(*) FROM chunks;` antes e depois).
- [ ] Com o banco parado, as rotas respondem 503 com mensagem clara (testado).
- [ ] O workflow passa no GitHub, num PR.
- [ ] Nenhum teste baixa modelo nem chama o Ollama.

Ao terminar, marque a etapa 8 no roteiro e troque esta seção pela etapa 9.

**Pendência fora desta etapa: ajustes da geração (PR pequeno e separado, antes ou depois da etapa 8, sem misturar com o CI).** Vêm das 4 respostas com problema do teste manual da etapa 7 (seção abaixo):
- Resposta cortada pelo `num_predict`: subir `LLM_NUM_PREDICT` para 400 a 512 e pedir no prompt só as linhas principais do exemplo, sem `#include` e `main`, e sem copiar o trecho inteiro. Os exemplos das notas são programas completos e passam do limite de 6 linhas que o prompt pede. Opcional: um campo `cortada` na resposta da API quando `done_reason` for `length`.
- Falso "não sei": dizer "não sei" só se nenhum trecho tratar do assunto, e responder com o que os trechos dizem quando trazem a resposta só em parte. Teste nas duas direções (perguntas fora do corpus e perguntas do corpus), com 1 ou 2 rodadas no máximo.
- Os outros 2 problemas (detalhe errado sobre a lista encadeada e resposta vaga sobre laços aninhados) são limitações do modelo de 3B e vão para o README. **Não edite as notas para corrigi-los.**
- Não troque o `qwen2.5:3b`: a comparação com e sem RAG do README usa esse modelo.
- Depois do ajuste, repita as mesmas perguntas e outras que não foram usadas no ajuste, e registre o que melhorou e o que não melhorou. A qualidade das respostas é avaliada só por observação, e a única métrica do projeto é o recall@3 da busca.

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
Feitas rodando o código. A medição atual é a da etapa 7, com as 25 notas. A da etapa 5, com as 13 notas da parte 1, fica como histórico.

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

## Observação para a etapa 9 (Docker)
O `POSTGRES_PORT` do `.env` serve para duas coisas: a porta publicada pelo Compose e a porta que a API usa para conectar. Dentro do Docker, a API conecta em `db:5432`, então essas duas configurações vão precisar ser separadas.

## Observação para a etapa 9 (Ollama)
O Ollama roda no Windows, fora do Docker. Dentro do container, `localhost` é o próprio container, então a API precisa de `OLLAMA_URL=http://host.docker.internal:11434` (Docker Desktop no Windows). No Linux e no CI não há Ollama: os testes usam o LLM falso.

## Observação para as etapas 8 e 9 (torch)
No `requirements.txt` fica `torch==2.15.0`. No Ubuntu, o PyPI instala a versão com CUDA, que é muito maior. No CI e no `Dockerfile`, instale antes o torch pelo índice CPU do PyTorch (`pip install torch==2.15.0 --index-url https://download.pytorch.org/whl/cpu`, conferindo que essa versão existe lá) e só depois o `requirements.txt`. Os testes usam embedder falso, então o CI não deve baixar nenhum modelo.

## Observação para a etapa 10 (não altera as notas)
Algumas perguntas do rascunho tratam de assuntos que nenhuma nota cobre. Na hora de rotular, elas recebem o rótulo "sem resposta no corpus" e ficam fora do cálculo do recall@3. Elas servem para testar se o assistente admite que não sabe, em vez de inventar. Não escreva notas novas para cobrir essas perguntas: decidir isso é uma escolha manual.

## Roteiro (atualize os checkboxes ao concluir cada etapa)
- [x] 1. Ambiente: Docker Compose com Postgres + pgvector, venv, Ollama testado.
- [x] 2. Corpus, parte 1: perguntas de rascunho (feitas manualmente) e depois as 13 notas de básico de C.
- [x] 3. API e banco: FastAPI, `config.py` com `.env`, tabelas `documentos` e `chunks` com `vector(384)` no `init.sql`, `POST /documentos`.
- [x] 4. Chunking: por seção `##`, com tamanho máximo e overlap, e o título da nota no começo de cada chunk. Mais os testes unitários.
- [x] 5. Embeddings e busca: top-k por distância de cosseno (`<=>`) e uma rota de depuração da busca.
- [x] 6. Geração: interface `gerar_resposta`, provedor Ollama, prompt com trechos numerados e citação, `POST /perguntas`.
- [x] 7. Corpus, parte 2: as 12 notas restantes, ingestão completa e teste manual com 10 perguntas.
- [ ] 8. Testes e CI: pytest com fakes e GitHub Actions.
- [ ] 9. Docker: `Dockerfile` da API (torch só para CPU) e Compose completo.
- [ ] 10. Avaliação: `perguntas.jsonl` (feito manualmente) e `avaliar.py` calculando o recall@3.
- [ ] 11. Experimentos: modelo de embedding × tamanho de chunk.
- [ ] 12. README final (diagrama, prints, resultados, limitações, comparação com e sem RAG).

## README
- O README deve ser honesto sobre como o projeto foi feito. Por exemplo: "notas escritas com auxílio de IA e revisadas manualmente, a partir das dúvidas recorrentes das monitorias".
- Sem métricas que não foram medidas.