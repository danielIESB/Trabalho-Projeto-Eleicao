# 🗳️ Projeto TSE — Pipeline de Dados Eleitorais Brasileiros

Pipeline ETL completo para limpeza, modelagem e carga de dados eleitorais do TSE (Tribunal Superior Eleitoral) em banco de dados PostgreSQL, cobrindo as eleições de **2010, 2014, 2018 e 2022**.

---

## 📋 Sobre o Projeto

Este projeto realiza a ingestão e tratamento de dados públicos do TSE, organizando-os em um modelo relacional otimizado para análises e visualizações no Power BI. O pipeline processa candidatos, partidos, receitas, despesas, bens patrimoniais e resultados eleitorais por UF.

---

## 🗂️ Modelo de Dados

```
municipio ──────────────────────────────────────────┐
eleicao  ────────────────────────────────────────┐  │
partido  ──────────────────────────────────────┐ │  │
                                               │ │  │
pessoa ──► candidatura ◄──────────────────────┘─┘──┘
               │
               ├──► despesa
               ├──► receita
               ├──► bem_patrimonial
               ├──► resultado_candidatura_uf
               └──► vaga
```

### Tabelas

| Tabela | Descrição |
|---|---|
| `municipio` | Municípios brasileiros (cruzamento TSE x IBGE) |
| `eleicao` | Eleições por ano e tipo |
| `partido` | Partidos políticos por número e sigla |
| `pessoa` | Dados pessoais dos candidatos (título, CPF, nome, gênero, raça) |
| `candidatura` | Candidaturas deferidas por eleição e cargo |
| `vaga` | Vagas disponíveis por eleição, UF e cargo |
| `resultado_candidatura_uf` | Votos agregados por candidato, eleição e UF |
| `bem_patrimonial` | Bens declarados pelos candidatos |
| `despesa` | Despesas de campanha por candidato |
| `receita` | Receitas de campanha por candidato e doador |

---

## ⚙️ Stack Tecnológica

| Ferramenta | Uso |
|---|---|
| Python 3.x | ETL e limpeza de dados |
| pandas | Manipulação e transformação dos DataFrames |
| SQLAlchemy + psycopg2 | Conexão e inserção no PostgreSQL |
| PostgreSQL (Railway) | Banco de dados relacional em nuvem |
| Power BI | Visualização e dashboards |
| Spyder (Anaconda) | IDE de desenvolvimento |

---

## 📁 Estrutura de Arquivos Fonte

```
tse/
├── Candidatos.csv                  # Base principal de candidatos
├── Bens_Candidatos.csv             # Bens patrimoniais declarados
├── Resultados_Candidato.csv        # Resultados por candidato e município
├── despesas/
│   ├── Despesas_Candidatos_*.csv   # Despesas particionadas por cargo/região
│   └── ...
└── receitas/
    ├── Receita_Candidato_2009a2010.csv
    ├── Receita_Candidato_2011a2024_*.csv
    └── ...
```

Arquivos de referência externos:
- `municipio_tse_ibge.csv` — cruzamento de códigos TSE e IBGE
- `Vagas.csv` — vagas por eleição e cargo

---

## 🚀 Como Executar

### Pré-requisitos

```bash
pip install pandas sqlalchemy psycopg2-binary
```

### Configuração

No script `tse_projeto.py`, ajuste os diretórios:

```python
DIR_DESPESA = r'caminho\para\tse\despesas'
DIR_RECEITA = r'caminho\para\tse\receitas'
```

E as credenciais do banco:

```python
HOST    = 'seu_host'
PORTA   = 0000
BANCO   = 'seu_banco'
USUARIO = 'seu_usuario'
SENHA   = 'sua_senha'
SCHEMA  = 'tse'
```

### Ordem de execução das células

Execute as células na seguinte ordem:

1. Importações e dependências
2. Configurações globais
3. Conexão com o banco
4. Função `importar_para_banco`
5. Leitura dos arquivos fonte
6. Filtro de candidaturas deferidas
7. Tabela: `municipio`
8. Tabela: `eleicao`
9. Tabela: `partido`
10. Tabela: `candidatura` *(limpeza — sem importar)*
11. Tabela: `pessoa` *(filtrada pelos títulos da candidatura)*
12. Tabela: `candidatura` *(importação)*
13. Tabela: `vaga`
14. Tabela: `resultado_candidatura_uf`
15. Tabela: `bem_patrimonial`
16. Tabela: `despesa`
17. Tabela: `receita`

> ⚠️ A ordem é crítica para respeitar as chaves estrangeiras.

---

## 🔧 Decisões Técnicas Relevantes

### Filtro de candidaturas deferidas
Apenas candidatos com situação `deferido` ou `deferido com recurso` são processados, garantindo que somente quem efetivamente participou das eleições entre no banco.

### Pessoa filtrada por candidatura
A tabela `pessoa` no arquivo original contém ~1,75 milhão de registros. O pipeline filtra apenas os títulos eleitorais presentes em `candidatura`, reduzindo para ~127 mil registros e evitando estouro de disco no banco gratuito.

### id_eleicao nulo em 2010
Os arquivos de despesa e receita de 2010 não possuem `id_eleicao` preenchido (limitação do TSE). O pipeline detecta esse caso e preenche automaticamente com o id correto (`37`).

### Encoding misto
Arquivos mais antigos (2010) utilizam `latin1` com aspas mal formatadas nos campos de descrição. O pipeline tenta `utf-8` primeiro e faz fallback para `latin1`, combinado com `on_bad_lines='skip'`.

### Inserção em lote
Toda importação usa `method='multi'` com `chunksize=1000`, otimizando a performance de inserção no PostgreSQL.

---

## 📊 Volume de Dados

| Tabela | Registros (aprox.) |
|---|---|
| municipio | ~5.500 |
| eleicao | ~4 |
| partido | ~35 |
| pessoa | ~127.000 |
| candidatura | ~130.000 |
| vaga | ~1.200 |
| resultado_candidatura_uf | ~200.000 |
| bem_patrimonial | ~500.000 |
| despesa | ~8.400.000 |
| receita | ~1.800.000 |

---

## 📈 Conexão com Power BI

Consulte o arquivo `conexao_powerbi_railway.txt` para o passo a passo completo de conexão do Power BI ao banco PostgreSQL.

---

## 📄 Fonte dos Dados

Dados públicos disponibilizados pelo **Tribunal Superior Eleitoral (TSE)**:
- https://dadosabertos.tse.jus.br/

---

## 👨‍💻 Autor

Desenvolvido como projeto acadêmico no curso de **Ciência de Dados e Inteligência Artificial** — IESB (Instituto de Educação Superior de Brasília).
