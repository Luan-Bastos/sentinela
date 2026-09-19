# Sentinela — reconstrução

Reconstrução em Python/Flask do sistema interno **Sentinela** (escala de
serviço), a partir de uma página real capturada em HTML.

## O que é fiel ao original e o que foi desenhado do zero

Eu só tinha uma tela real de referência: **Previsão Diária**
(`Principal > Pessoal > Serviços > Previsão Diária`). Dela vieram:

- A separação em **Serviço Externo**, **Serviço Interno** e **Missão**
- Os campos de cada escala: posto (com contingente), militar escalado
  (posto/graduação + número + nome de guerra + unidade), responsável,
  indicadores de status com horário no formato GDH
- O calendário de navegação por dia e os filtros por Unidade (SU),
  Pelotão/Seção e Responsável
- A trilha de navegação (breadcrumb) e a existência dos menus Principal,
  Pessoal, Utilitário, OS e Sobre

O resto — os módulos **Militares**, **Unidades/Pelotões/Postos**
(Utilitário) e **Ordens de Serviço** (OS) — só existiam como itens de
menu na captura, sem tela por trás. Eu desenhei esses módulos do zero,
de um jeito que faz sentido para o domínio (CRUD de pessoal, tabelas de
apoio, um mural de OS). Se na prática eles funcionam diferente no
sistema real, é só me falar o que muda que eu ajusto.

O botão **"Gerar Previsão"** também é uma interpretação minha: preenche
automaticamente os postos do dia que ainda não têm ninguém escalado,
priorizando quem está há mais tempo sem ser escalado. O algoritmo real
pode ser outro — dá pra refinar depois.

Os dados de exemplo (`seed.py`) são **100% fictícios** — nenhum nome ou
número do arquivo original foi reaproveitado.

## Como rodar

```bash
python3 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt

python3 seed.py                   # cria o banco com dados de demonstração
python3 run.py                    # inicia em http://127.0.0.1:5000
```

Login de demonstração: **usuário** `bastos` · **senha** `123456`
(demais usuários no `seed.py`, todos com a mesma senha).

Rodar `python3 seed.py` de novo **apaga e recria o banco do zero** —
use só para resetar os dados de demonstração.

## Estrutura

```
sentinela/
  app/
    __init__.py      # app factory (cria e configura o Flask)
    models.py         # modelo de dados (SQLAlchemy)
    auth.py            # login / logoff
    principal.py       # painel inicial + Sobre
    pessoal.py         # CRUD de militares
    servicos.py         # Previsão Diária: escalas e missões (módulo principal)
    utilitario.py        # unidades, pelotões/seções, postos de serviço
    ordens.py             # Ordens de Serviço (OS)
    templates/             # HTML (Jinja2)
    static/css/style.css    # design (paleta, tipografia, componentes)
  seed.py                    # popula o banco com dados fictícios
  run.py                      # ponto de entrada
  requirements.txt
  render.yaml                  # Blueprint de deploy (Render)
```

Banco: por padrão, SQLite local (`instance/sentinela.db`), criado e
populado automaticamente na primeira execução. Se existir uma variável
de ambiente `DATABASE_URL` (é o caso em produção no Render — veja
abaixo), o app usa ela no lugar, com Postgres.

## Deploy no Render (grátis)

O projeto já vem com `render.yaml`, que descreve tanto o serviço web
quanto o banco Postgres — a Render lê esse arquivo e cria os dois de
uma vez, já conectados.

1. Crie um repositório no GitHub e suba este projeto:
   ```bash
   git init
   git add .
   git commit -m "Sentinela"
   git branch -M main
   git remote add origin https://github.com/SEU-USUARIO/sentinela.git
   git push -u origin main
   ```
2. Crie uma conta em [render.com](https://render.com) (dá pra entrar
   direto com o GitHub).
3. No painel, clique em **New** → **Blueprint** e conecte o
   repositório que você acabou de criar.
4. A Render vai detectar o `render.yaml` e mostrar o que vai criar: o
   serviço web `sentinela` e o banco `sentinela-db`, ambos no plano
   Free. Clique em **Apply**.
5. O primeiro deploy demora alguns minutos (instala as dependências e
   sobe o app). Quando terminar, a URL pública aparece no topo da
   página do serviço, no formato `https://sentinela-xxxx.onrender.com`.
6. Na primeira vez que alguém acessa, o app percebe que o banco está
   vazio e já popula com os mesmos dados fictícios do `seed.py` — não
   precisa rodar nada manualmente.

Duas coisas do plano Free vale saber: o serviço "dorme" depois de 15
minutos sem acesso (a próxima visita demora uns 30-60s pra acordar), e
o banco Postgres gratuito da Render expira depois de um tempo — pra um
link de portfólio isso raramente é problema, mas se quiser manter para
sempre, o plano pago remove os dois limites.

Pra atualizar o site depois de mexer no código, é só repetir
`git add . && git commit -m "..." && git push` — a Render reimplanta
sozinha a cada push.

## Próximos passos possíveis

- Ajustar os módulos "inventados" (Utilitário, OS) pra bater com a tela
  real, se você tiver mais capturas ou acesso ao sistema original
  pra comparar
- Trocar o algoritmo de "Gerar Previsão" por um mais fiel ao original
- Adicionar permissões por posto/graduação (hoje todo usuário logado
  pode tudo)
