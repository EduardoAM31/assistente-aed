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
tests/      conftest.py (banco aed_teste e fakes), test_*.py
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

## Etapa atual: 9 (Docker)
Objetivo (do roteiro): o `Dockerfile` da API, com o torch só para CPU, e o Compose completo.

**O que a etapa 8 deixou pronto:**
- **170 testes:**
  - 153 rodam sem banco;
  - 17 de integração (marcador `integracao`) rodam no banco **`aed_teste`**, nunca no `aed`. O `tests/conftest.py` troca o banco antes de importar o `app` e recusa limpar qualquer banco cujo nome não termine em `_teste`.
- **Fakes** no `conftest.py`: `ModeloFalso`, com vetores previsíveis por palavra-chave, e `LLMFalso`, que guarda o contexto recebido. As fixtures `fakes`, `banco_limpo` e `cliente` montam os testes.
- **Banco de teste local:** criado uma vez com `docker compose exec db psql -U rag -d aed -c "CREATE DATABASE aed_teste"` e depois `Get-Content sql/init.sql | docker compose exec -T db psql -U rag -d aed_teste`. Sem o banco no ar, os testes de integração são pulados localmente. No CI (`CI=true`), eles falham.
- **503 com mensagem clara**, num tratamento único em `main.py`, quando o banco está fora do ar (`InterfaceError` do pg8000) ou quando o modelo de embedding não pode ser carregado (`ErroModeloEmbedding`, que embrulha o `OSError` do sentence-transformers).
- **A pergunta tem no máximo 500 caracteres** (`TAMANHO_MAXIMO_PERGUNTA`, em `app/schemas.py`), no `POST /perguntas` e no `GET /busca`.
- **`.github/workflows/testes.yml`:** roda em PR e em push na `main`, com Ubuntu, Python 3.14, pgvector como service container, `cp .env.example .env` e o `torch==2.15.0` pelo índice CPU antes do `requirements.txt`.
- **Medido no primeiro run do CI (PR #7):**
  - job de 96 s, dos quais 68 s são a instalação do torch e das dependências;
  - 170 testes passaram em 2,4 s.

  No segundo run, com o cache de pip, o job levou 68 s (37 s de instalação) e os 170 testes, 1,4 s.

  Instalar o torch no CI ficou mantido. A alternativa de não instalar o `torch` e o `sentence-transformers` no CI continua possível, e a escolha é do usuário.
- **Não entrou:** a troca do `SELECT` antes do upsert por `RETURNING (xmax = 0)`, que era opcional.

**O que fazer nesta etapa:** o `Dockerfile` e o `.dockerignore` da API, o serviço `api` no `docker-compose.yml` ao lado do `db`, e o teste de ponta a ponta com tudo em container (a API no Docker, o Ollama no Windows).

**Padrões sugeridos para a etapa 9 (confirme com o usuário antes de implementar):**
- **Imagem:** `python:3.14-slim` (confira que a tag existe; o CI usa o Python 3.14). Não use Alpine, porque o torch precisa de glibc. Instale o `torch==2.15.0` pelo índice CPU antes do `requirements.txt` (`pip install --no-cache-dir`), como no CI. Copie primeiro o `requirements.txt` e instale, para essa camada ficar em cache, e só depois copie o `app/`. **Só o `app/` vai para a imagem:** as notas entram pela API (`POST /documentos`), e o `sql/init.sql` é do serviço `db`.
- **`.dockerignore`:** `.env`, `.venv`, `.git`, `__pycache__`, `tests`, `corpus`, `avaliacao` e `scripts`. O `.env` nunca entra na imagem.
- **Usuário sem privilégios de root**, se não complicar: crie um usuário `app`, defina `HF_HOME=/modelos` e crie `/modelos` na imagem com esse dono, para o volume nomeado herdar a permissão. Se complicar, rode como root e registre isso como limitação.
- **Comando:** `uvicorn app.main:app --host 0.0.0.0 --port 8000`, sem `--reload`.
- **Porta do banco, sem separar variáveis:** o serviço `api` usa `env_file: .env` e, em `environment:`, sobrescreve `POSTGRES_HOST: db` e `POSTGRES_PORT: "5432"`. O `environment` vale mais que o `env_file`, e o `Settings` lê as variáveis de ambiente antes do `.env`. A `POSTGRES_PORT=5433` do `.env` continua servindo só para a porta publicada do `db`.
- **Ollama no Windows:** `OLLAMA_URL: http://host.docker.internal:11434` em `environment:` e `extra_hosts: ["host.docker.internal:host-gateway"]` (necessário no Linux, inofensivo no Docker Desktop). Se der "connection refused", o Ollama pode estar escutando só em `127.0.0.1`. A saída é `OLLAMA_HOST=0.0.0.0`, que expõe o Ollama na rede local: avise o usuário antes de sugerir.
- **Modelos de embedding num volume nomeado** (`modelos`, montado em `HF_HOME`), e não baixados no build. A imagem fica menor, o modelo muda com o `.env` nos experimentos da etapa 11, e o download (cerca de 470 MB no MiniLM) acontece uma vez, na primeira chamada de `POST /embeddings` ou `GET /busca`. O cache do Windows não vale no container, que é Linux.
- **`depends_on` com `condition: service_healthy`** (o `db` já tem healthcheck) e, opcional, um healthcheck da API em `GET /saude`.
- **Porta 8000 publicada.** Se a API também estiver rodando no venv na 8000, pare uma das duas. Para subir só o banco no dia a dia, use `docker compose up -d db`.
- **Opcional no CI:** um job que só faz o `docker build` da imagem, para o `Dockerfile` não quebrar sem ninguém ver. Pergunte ao usuário e registre o tempo medido.
- **RAM:** o WSL2 pode estar limitado a 3 GB no `.wslconfig` (confirme com o usuário), e o banco e a API com torch e o modelo precisam caber nisso. Meça com `docker stats` durante o `POST /embeddings` e registre o valor medido aqui. Não estime.

**Passos sugeridos (pequenos, um commit por passo, explicando as escolhas no fim de cada um):**
1. `.dockerignore` e `Dockerfile`. Rode `docker build` e registre o tamanho (`docker images`) e o tempo.
2. Serviço `api` no Compose, com as variáveis acima. Rode `docker compose up -d` e confira `GET http://localhost:8000/saude`, que usa o banco por `db:5432`.
3. Teste manual no `/docs`: enviar uma nota, rodar `POST /embeddings` (o modelo baixa para o volume) e `GET /busca`.
4. Recriar o container (`docker compose up -d --force-recreate api`) e conferir que o modelo **não** baixa de novo.
5. `POST /perguntas` com o Ollama rodando no Windows.
6. Registrar o tamanho da imagem, o uso de RAM e os tempos nesta seção, só com o que foi medido.
7. Apagar as observações da etapa 9 (porta do banco, Ollama e torch) que ficaram resolvidas.

**Medido nesta etapa (rodando de verdade, Docker Desktop no Windows):**
- **Imagem `assistente-aed-api`: 2,11 GB**, com build de 132 s na primeira vez (sem cache de camadas). Dos 1,5 GB de pacotes Python, 817 MB são do `torch` (CPU), 131 MB do `transformers` e 110 MB do `scipy`.
- **Conferido na imagem:**
  - `/codigo` tem só `app/` e `requirements.txt`, e **o `.env` não está lá**;
  - o processo roda como o usuário `app`, sem root;
  - o Python é o 3.14.10, e o torch é o `2.15.0+cpu`, sem CUDA.
- **Compose:** `db` e `api` sobem *healthy*, e o `GET /saude` responde `{"api":"ok","banco":"ok"}`. Dentro do container, a API usa `db:5432` e `http://host.docker.internal:11434`, e o `.env` continua com 5433 para a porta publicada.
- **Upload, embeddings e busca pelo container:**
  - o reenvio da `indice-zero.md`, com o mesmo conteúdo, deu 200, e o banco continuou com 324 chunks;
  - o `POST /embeddings` gerou os 12 vetores em 36,6 s, contando o **download do MiniLM para o volume `modelos` (458 MB)**;
  - o `GET /busca` deu as mesmas distâncias da API no venv do Windows.
- **Recriar o container** (`docker compose up -d --force-recreate api`): o volume continuou com 458 MB, e o modelo carregou com `HF_HUB_OFFLINE=1`, sem internet. A primeira busca levou 6,6 s, carregando o modelo do volume, contra 36,6 s com o download.
- **Ollama:**
  - `POST /perguntas` pelo container chegou ao Ollama no Windows e devolveu respostas com fontes iguais às do `GET /busca`;
  - **não foi preciso `OLLAMA_HOST=0.0.0.0`**: o Ollama continua escutando só em `127.0.0.1`, e o Docker Desktop encaminha o `host.docker.internal`;
  - com o Ollama desligado, a rota deu 503 com a mensagem de conexão, e o `/saude` continuou ok.
- **RAM** (`docker stats`, numa VM de 2,84 GiB):
  - a API teve **pico de 1.236 MiB** durante o download do modelo, o `POST /embeddings` dos 12 chunks e as buscas, e fica em **840 MiB** parada, com o modelo carregado;
  - o `db` usa cerca de 58 MiB.

  Um `POST /embeddings?refazer=true` dos 324 chunks não foi medido no container, porque recalcularia todos os vetores do banco `aed`.
- **Decisão do usuário:** o tamanho da imagem e o uso de RAM são aceitáveis.
- **CI:** o job `imagem`, no `testes.yml`, roda em paralelo com os testes. Ele monta a imagem, confere que o `.env` não entra nela (cria um `.env` antes do build, para testar o `.dockerignore`) e que `import app.main` funciona dentro da imagem.

**Cuidados:**
- **Nunca rode `docker compose down -v` sem perguntar.** Com o serviço novo, o `-v` apaga também o volume `modelos`, além do `pgdata` (as 25 notas e os vetores).
- Não mexa no banco de desenvolvimento `aed` nem no `aed_teste` fora dos testes.
- O `sql/init.sql` não precisa ser aplicado de novo, porque o volume já existe.

**Pronto quando:**
- [ ] `docker compose build` e `docker compose up -d` sobem o `db` e a `api`, e `GET /saude` responde que o banco está ok.
- [ ] Enviar uma nota, rodar `POST /embeddings` e `GET /busca` pelo container funciona.
- [ ] Depois de recriar o container, o modelo não é baixado de novo.
- [ ] `POST /perguntas` pelo container chega ao Ollama no Windows e devolve resposta com fontes. Com o Ollama desligado, devolve 503.
- [ ] O `.env` não está na imagem (confira com `docker run --rm <imagem> ls -a`).
- [ ] O tamanho da imagem e a RAM do container estão registrados, e o usuário decidiu que estão aceitáveis.
- [ ] `pytest` passa localmente e o CI passa no PR.

Ao terminar, marque a etapa 9 no roteiro e troque esta seção pela etapa 10.

## Pendência: ajustes da geração (PR pequeno e separado, sem misturar com outra etapa)
Vem das 4 respostas com problema do teste manual da etapa 7 (seção abaixo):
- **Resposta cortada pelo `num_predict`:** subir o `LLM_NUM_PREDICT` para 400 a 512 e pedir no prompt só as linhas principais do exemplo, sem `#include` e `main`, e sem copiar o trecho inteiro. Os exemplos das notas são programas completos e passam do limite de 6 linhas que o prompt pede. Opcional: um campo `cortada` na resposta da API quando `done_reason` for `length`.
- **Falso "não sei":** dizer "não sei" só se nenhum trecho tratar do assunto, e responder com o que os trechos dizem quando eles trazem a resposta só em parte. Teste nas duas direções (perguntas fora do corpus e perguntas do corpus), com 1 ou 2 rodadas no máximo.
- Os outros 2 problemas (o detalhe errado sobre a lista encadeada e a resposta vaga sobre laços aninhados) são limitações do modelo de 3B e vão para o README. **Não edite as notas para corrigi-los.**
- **Não troque o `qwen2.5:3b`:** a comparação com e sem RAG do README usa esse modelo.
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
- [x] 8. Testes e CI: pytest com fakes e GitHub Actions.
- [ ] 9. Docker: `Dockerfile` da API (torch só para CPU) e Compose completo.
- [ ] 10. Avaliação: `perguntas.jsonl` (feito manualmente) e `avaliar.py` calculando o recall@3.
- [ ] 11. Experimentos: modelo de embedding × tamanho de chunk.
- [ ] 12. README final (diagrama, prints, resultados, limitações, comparação com e sem RAG).

## README
- O README deve ser honesto sobre como o projeto foi feito. Por exemplo: "notas escritas com auxílio de IA e revisadas manualmente, a partir das dúvidas recorrentes das monitorias".
- Sem métricas que não foram medidas.