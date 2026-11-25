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
scripts/    contar_tokens.py
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

## Etapa atual: 11 (experimentos)
Objetivo (do roteiro): medir o recall@3 das 6 combinações de modelo de embedding × tamanho de chunk, para escolher a configuração final e montar a tabela do README.

**O que já existe:**
- O `avaliacao/avaliar.py` e o `perguntas.jsonl`, que está congelado (veja a seção "Avaliação").
- **A referência da etapa 10:** a 2ª rodada, com os rótulos revisados. MiniLM com 60/10, com recall@3 de 58,5% nas principais e 34,8% nas variantes (veja "Medições registradas").
- A contagem de chunks e de tokens das 3 configurações, nos 2 modelos, também está em "Medições registradas". Dela sai a porcentagem de chunks cortados pelo limite de tokens.
- Hoje, a ingestão das notas só é feita pelo `POST /documentos`, uma nota por vez (pelo `/docs`), e depois pelo `POST /embeddings?refazer=true`.

**As 6 combinações:**
- **Modelos** (o valor de `EMBEDDING_MODELO`): `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` (sem prefixo) e `intfloat/multilingual-e5-small` (com `passage: ` e `query: `, entre aspas no `.env`).
- **Tamanhos de chunk:** 40/8, 60/10 e sem limite (`CHUNK_MAX_PALAVRAS=0`).
- **O MiniLM com 60/10 já foi medido na etapa 10:** não precisa repetir, mas repetir serve para conferir que o processo de reindexar não muda o número.

**O que fazer nesta etapa:**
- **Um script para reindexar o banco** com a configuração do `.env`: reenviar as 25 notas, com o chunking do `.env`, e refazer os vetores com o modelo do `.env`. Depois, o `avaliar.py` confere que o banco bate com o `.env`.
- **Para cada combinação:** trocar o modelo, os prefixos e o chunking no `.env`, reindexar e rodar o `avaliar.py`. Só valem as rodadas sem aviso.
- **A tabela do README:** uma linha por combinação, com o número de chunks, a porcentagem de chunks cortados pelo limite de tokens e o recall@3 das principais e das variantes.
- **No fim:** a escolha manual da configuração final, feita pelo usuário. O `.env` e o banco voltam para essa configuração.

**Padrões sugeridos** (o usuário confirma antes de codar):
- **`scripts/reindexar.py`,** que roda com `python -m scripts.reindexar`, sem a API. Ele chama as mesmas funções que as rotas usam: `ler_nota`, `dividir_em_chunks` e `db.salvar_documento` para cada nota, e depois `busca.gerar_embeddings_dos_chunks(refazer=True)`. Escreve no banco do `.env`, então só roda no `aed`, e mostra antes o modelo e o chunking que vai usar.
- **A tabela** é montada a partir dos JSONs de `avaliacao/resultados/`, à mão ou com um script pequeno.
- **Comparação justa das variantes:** a tabela mostra também o recall das principais que têm variante. Na etapa 10, as duas versões dessas 23 perguntas acertaram o mesmo número (8). Isso pode entrar no `avaliar.py` como um terceiro número.

**Cuidados:**
- **Reindexar troca todo o conteúdo do banco `aed`.** Nada se perde: as notas estão no `corpus/`. Mas uma API que já estava no ar continua com o modelo e os prefixos que leu do `.env` quando subiu (o container `api` lê o `.env` ao ser criado, e a API do venv, ao iniciar). Com o banco reindexado para outro modelo, ela compara vetores de espaços diferentes, sem erro nenhum. **Pare a API durante a etapa** (`docker compose stop api` e feche o `uvicorn` do venv) e, depois de voltar para a configuração final, suba de novo (`docker compose up -d --force-recreate api`). Rode os experimentos no venv, não no container. **Nunca use `docker compose down -v`** para limpar o banco.
- **O `.env` precisa mudar inteiro de uma vez:** o modelo, os 2 prefixos e o chunking. O e5 sem os prefixos dá um recall errado, sem erro nenhum. O `avaliar.py` avisa sobre vetores do banco de outro modelo, mas não percebe um prefixo de pergunta esquecido.
- **RAM:** o e5-small também gera vetores de 384 dimensões, mas o uso de RAM dele ainda não foi medido. Na primeira vez, ele é baixado do Hugging Face.
- **Amostra pequena:** são 53 perguntas principais, então 1 pergunta vale 1,9 ponto de recall (4,3 pontos nas 23 variantes). Uma diferença de 1 ou 2 perguntas entre duas combinações não permite dizer que uma é melhor. No README, mostre os acertos (por exemplo, 31 de 53) junto com a porcentagem.
- **Não ajuste notas, perguntas, rótulos nem a busca** olhando os erros. Só o que foi medido entra no README.
- **Observação da etapa 10, sem promessa de resultado:** com 60/10, em 10 dos 22 erros das principais (2ª rodada) a mesma seção ocupou mais de uma das 3 posições. Sem limite, cada seção é um chunk só, mas no MiniLM todos esses chunks passam dos 128 tokens.

**A decidir (é do usuário):**
- se o `avaliar.py` ganha o recall das principais que têm variante;
- se uma pergunta que duas seções respondem passa a aceitar uma lista de seções. **Decidir isso olhando os erros da etapa 10 infla o recall.** Se mudar, todas as combinações são medidas de novo, com a mesma regra;
- a configuração final, escolhida à mão.

**Fora desta etapa:** a correção de erros de digitação (depois da etapa 11) e o PR dos ajustes da geração.

**Pronto quando:**
- [ ] As 6 combinações têm um JSON em `avaliacao/resultados/`, sem aviso.
- [ ] A tabela com chunks, % cortados e recall@3 das principais e das variantes está em "Medições registradas".
- [ ] A configuração final foi escolhida pelo usuário, o `.env` e o banco voltaram para ela e a API foi recriada com ela.
- [ ] `pytest` passa.

Ao terminar, marque a etapa 11 no roteiro e troque esta seção pela etapa 12.

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
- [ ] 11. Experimentos: modelo de embedding × tamanho de chunk.
- [ ] 12. README final (diagrama, prints, resultados, limitações, comparação com e sem RAG).

## README
- O README deve ser honesto sobre como o projeto foi feito. Por exemplo: "notas escritas com auxílio de IA e revisadas manualmente, a partir das dúvidas recorrentes das monitorias".
- Sem métricas que não foram medidas.