CREATE TABLE dim_eleicao (
    eleicao_sk          BIGSERIAL PRIMARY KEY,
    id_eleicao          VARCHAR(50) UNIQUE NOT NULL,
    ano                 INT NOT NULL,
    turno               INT NULL,
    tipo_eleicao        VARCHAR(100),
    data_eleicao        DATE
);

CREATE TABLE dim_uf (
    uf_sk               SMALLSERIAL PRIMARY KEY,
    sigla_uf            CHAR(2) UNIQUE NOT NULL
);

CREATE TABLE dim_municipio (
    municipio_sk        BIGSERIAL PRIMARY KEY,
    id_municipio_ibge   VARCHAR(7),
    id_municipio_tse    VARCHAR(20),
    uf_sk               SMALLINT NOT NULL REFERENCES dim_uf(uf_sk),
    nome_municipio      VARCHAR(200),
    UNIQUE (id_municipio_ibge, id_municipio_tse, uf_sk)
);

CREATE TABLE dim_cargo (
    cargo_sk            SMALLSERIAL PRIMARY KEY,
    nome_cargo          VARCHAR(100) UNIQUE NOT NULL
);

CREATE TABLE dim_partido (
    partido_sk              BIGSERIAL PRIMARY KEY,
    numero_partido          VARCHAR(10),
    sigla_partido           VARCHAR(30),
    nome_partido            VARCHAR(200),
    tipo_agremiacao         VARCHAR(100),
    situacao_legenda        VARCHAR(100),
    UNIQUE (numero_partido, sigla_partido, nome_partido)
);

CREATE TABLE dim_coligacao (
    coligacao_sk            BIGSERIAL PRIMARY KEY,
    sequencial_coligacao    VARCHAR(50),
    nome_coligacao          VARCHAR(250),
    composicao_coligacao    TEXT,
    UNIQUE (sequencial_coligacao)
);

CREATE TABLE dim_candidato (
    candidato_sk                BIGSERIAL PRIMARY KEY,
    sequencial_candidato        VARCHAR(50),
    titulo_eleitoral            VARCHAR(50),
    cpf                         VARCHAR(14),
    nome_civil                  VARCHAR(250),
    nome_urna                   VARCHAR(250),
    data_nascimento             DATE,
    genero                      VARCHAR(50),
    instrucao                   VARCHAR(100),
    ocupacao                    VARCHAR(150),
    estado_civil                VARCHAR(100),
    nacionalidade               VARCHAR(100),
    raca                        VARCHAR(50),
    email                       VARCHAR(250),
    sigla_uf_nascimento         CHAR(2),
    municipio_nascimento        VARCHAR(200),
    UNIQUE (sequencial_candidato)
);

CREATE TABLE bridge_candidato_partido_eleicao (
    cand_eleicao_sk            BIGSERIAL PRIMARY KEY,
    candidato_sk               BIGINT NOT NULL REFERENCES dim_candidato(candidato_sk),
    eleicao_sk                 BIGINT NOT NULL REFERENCES dim_eleicao(eleicao_sk),
    partido_sk                 BIGINT NULL REFERENCES dim_partido(partido_sk),
    cargo_sk                   SMALLINT NULL REFERENCES dim_cargo(cargo_sk),
    municipio_sk               BIGINT NULL REFERENCES dim_municipio(municipio_sk),
    numero_candidato           VARCHAR(20),
    situacao_candidatura       VARCHAR(100),
    idade_na_eleicao           INT,
    UNIQUE (candidato_sk, eleicao_sk, cargo_sk, municipio_sk)
);

CREATE TABLE dim_zona_eleitoral (
    zona_sk                 BIGSERIAL PRIMARY KEY,
    municipio_sk            BIGINT NOT NULL REFERENCES dim_municipio(municipio_sk),
    numero_zona             VARCHAR(20) NOT NULL,
    UNIQUE (municipio_sk, numero_zona)
);

CREATE TABLE dim_cnae (
    cnae_sk                     BIGSERIAL PRIMARY KEY,
    codigo_cnae                 VARCHAR(20),
    classe_cnae                 VARCHAR(20),
    subclasse_cnae              VARCHAR(20),
    descricao_cnae              VARCHAR(300),
    UNIQUE (codigo_cnae, classe_cnae, subclasse_cnae)
);

CREATE TABLE fato_bens_candidato (
    bem_sk                      BIGSERIAL PRIMARY KEY,
    cand_eleicao_sk             BIGINT NOT NULL REFERENCES bridge_candidato_partido_eleicao(cand_eleicao_sk),
    tipo_item                   VARCHAR(150),
    descricao_item              TEXT,
    valor_item                  NUMERIC(18,2)
);

CREATE TABLE dim_agente_financeiro (
    agente_sk                   BIGSERIAL PRIMARY KEY,
    cpf_cnpj                    VARCHAR(20),
    nome                        VARCHAR(250),
    nome_receita_federal        VARCHAR(250),
    tipo_agente                 VARCHAR(100),
    esfera_partidaria           VARCHAR(100),
    uf_sk                       SMALLINT NULL REFERENCES dim_uf(uf_sk),
    municipio_sk                BIGINT NULL REFERENCES dim_municipio(municipio_sk),
    cnae_sk                     BIGINT NULL REFERENCES dim_cnae(cnae_sk),
    UNIQUE (cpf_cnpj, nome)
);

CREATE TABLE fato_despesa_candidato (
    despesa_sk                      BIGSERIAL PRIMARY KEY,
    cand_eleicao_sk                 BIGINT NOT NULL REFERENCES bridge_candidato_partido_eleicao(cand_eleicao_sk),
    fornecedor_sk                   BIGINT NULL REFERENCES dim_agente_financeiro(agente_sk),
    eleicao_sk                      BIGINT NOT NULL REFERENCES dim_eleicao(eleicao_sk),
    sequencial_despesa              VARCHAR(50),
    data_despesa                    DATE,
    tipo_despesa                    VARCHAR(150),
    descricao_despesa               TEXT,
    origem_despesa                  VARCHAR(150),
    valor_despesa                   NUMERIC(18,2),
    tipo_prestacao_contas           VARCHAR(100),
    data_prestacao_contas           DATE,
    sequencial_prestador_contas     VARCHAR(50),
    cnpj_prestador_contas           VARCHAR(20),
    tipo_documento                  VARCHAR(100),
    numero_documento                VARCHAR(100),
    especie_recurso                 VARCHAR(100),
    fonte_recurso                   VARCHAR(100)
);

CREATE TABLE fato_receita_candidato (
    receita_sk                      BIGSERIAL PRIMARY KEY,
    cand_eleicao_sk                 BIGINT NOT NULL REFERENCES bridge_candidato_partido_eleicao(cand_eleicao_sk),
    doador_sk                       BIGINT NULL REFERENCES dim_agente_financeiro(agente_sk),
    doador_origem_sk                BIGINT NULL REFERENCES dim_agente_financeiro(agente_sk),
    eleicao_sk                      BIGINT NOT NULL REFERENCES dim_eleicao(eleicao_sk),
    sequencial_receita              VARCHAR(50),
    data_receita                    DATE,
    fonte_receita                   VARCHAR(150),
    origem_receita                  VARCHAR(150),
    natureza_receita                VARCHAR(150),
    especie_receita                 VARCHAR(100),
    situacao_receita                VARCHAR(100),
    descricao_receita               TEXT,
    valor_receita                   NUMERIC(18,2),
    numero_recibo_eleitoral         VARCHAR(100),
    numero_documento                VARCHAR(100),
    numero_recibo_doacao            VARCHAR(100),
    numero_documento_doacao         VARCHAR(100),
    tipo_prestacao_contas           VARCHAR(100),
    data_prestacao_contas           DATE,
    sequencial_prestador_contas     VARCHAR(50),
    cnpj_prestador_contas           VARCHAR(20),
    entrega_conjunto                VARCHAR(20)
);

CREATE TABLE dim_comite (
    comite_sk                BIGSERIAL PRIMARY KEY,
    sequencial_comite        VARCHAR(50) UNIQUE,
    tipo_comite              VARCHAR(100),
    partido_sk               BIGINT NULL REFERENCES dim_partido(partido_sk),
    municipio_sk             BIGINT NULL REFERENCES dim_municipio(municipio_sk)
);

CREATE TABLE fato_receita_comite (
    receita_comite_sk            BIGSERIAL PRIMARY KEY,
    comite_sk                    BIGINT NOT NULL REFERENCES dim_comite(comite_sk),
    doador_sk                    BIGINT NULL REFERENCES dim_agente_financeiro(agente_sk),
    doador_origem_sk             BIGINT NULL REFERENCES dim_agente_financeiro(agente_sk),
    data_receita                 DATE,
    origem_receita               VARCHAR(150),
    fonte_receita                VARCHAR(150),
    natureza_receita             VARCHAR(150),
    situacao_receita             VARCHAR(100),
    descricao_receita            TEXT,
    tipo_documento               VARCHAR(100),
    numero_documento             VARCHAR(100),
    nome_membro                  VARCHAR(250),
    cpf_membro                   VARCHAR(20),
    cnpj_prestador_contas        VARCHAR(20),
    valor_receita                NUMERIC(18,2)
);

CREATE TABLE dim_orgao_partidario (
    orgao_sk                     BIGSERIAL PRIMARY KEY,
    sequencial_diretorio         VARCHAR(50) UNIQUE,
    esfera_partidaria            VARCHAR(100),
    tipo_diretorio               VARCHAR(100),
    partido_sk                   BIGINT REFERENCES dim_partido(partido_sk),
    municipio_sk                 BIGINT REFERENCES dim_municipio(municipio_sk)
);
CREATE TABLE fato_receita_orgao_partidario (
    receita_orgao_sk                 BIGSERIAL PRIMARY KEY,
    orgao_sk                         BIGINT NOT NULL REFERENCES dim_orgao_partidario(orgao_sk),
    doador_sk                        BIGINT NULL REFERENCES dim_agente_financeiro(agente_sk),
    doador_origem_sk                 BIGINT NULL REFERENCES dim_agente_financeiro(agente_sk),
    sequencial_receita               VARCHAR(50),
    data_receita                     DATE,
    origem_receita                   VARCHAR(150),
    fonte_receita                    VARCHAR(150),
    natureza_receita                 VARCHAR(150),
    especie_receita                  VARCHAR(100),
    descricao_receita                TEXT,
    numero_recibo_eleitoral          VARCHAR(100),
    tipo_documento                   VARCHAR(100),
    numero_documento                 VARCHAR(100),
    tipo_prestacao_contas            VARCHAR(100),
    data_prestacao_contas            DATE,
    sequencial_prestador_contas      VARCHAR(50),
    cnpj_prestador_contas            VARCHAR(20),
    numero_recibo_doacao             VARCHAR(100),
    numero_documento_doacao          VARCHAR(100),
    valor_receita                    NUMERIC(18,2)
);

CREATE TABLE fato_resultado_candidato (
    resultado_candidato_sk       BIGSERIAL PRIMARY KEY,
    eleicao_sk                   BIGINT NOT NULL REFERENCES dim_eleicao(eleicao_sk),
    cand_eleicao_sk              BIGINT NOT NULL REFERENCES bridge_candidato_partido_eleicao(cand_eleicao_sk),
    resultado                    VARCHAR(100),
    votos                        BIGINT,
    UNIQUE (eleicao_sk, cand_eleicao_sk)
);

CREATE TABLE fato_resultado_candidato_municipio (
    resultado_cand_mun_sk        BIGSERIAL PRIMARY KEY,
    eleicao_sk                   BIGINT NOT NULL REFERENCES dim_eleicao(eleicao_sk),
    cand_eleicao_sk              BIGINT NOT NULL REFERENCES bridge_candidato_partido_eleicao(cand_eleicao_sk),
    municipio_sk                 BIGINT NOT NULL REFERENCES dim_municipio(municipio_sk),
    resultado                    VARCHAR(100),
    votos                        BIGINT,
    UNIQUE (eleicao_sk, cand_eleicao_sk, municipio_sk)
);

CREATE TABLE fato_resultado_partido_municipio (
    resultado_part_mun_sk        BIGSERIAL PRIMARY KEY,
    eleicao_sk                   BIGINT NOT NULL REFERENCES dim_eleicao(eleicao_sk),
    partido_sk                   BIGINT NOT NULL REFERENCES dim_partido(partido_sk),
    municipio_sk                 BIGINT NOT NULL REFERENCES dim_municipio(municipio_sk),
    cargo_sk                     SMALLINT NOT NULL REFERENCES dim_cargo(cargo_sk),
    votos_nominais               BIGINT,
    votos_legenda                BIGINT,
    UNIQUE (eleicao_sk, partido_sk, municipio_sk, cargo_sk)
);

CREATE TABLE fato_vaga (
    vaga_sk                      BIGSERIAL PRIMARY KEY,
    eleicao_sk                   BIGINT NOT NULL REFERENCES dim_eleicao(eleicao_sk),
    municipio_sk                 BIGINT NOT NULL REFERENCES dim_municipio(municipio_sk),
    cargo_sk                     SMALLINT NOT NULL REFERENCES dim_cargo(cargo_sk),
    vagas                        INT NOT NULL,
    UNIQUE (eleicao_sk, municipio_sk, cargo_sk)
);