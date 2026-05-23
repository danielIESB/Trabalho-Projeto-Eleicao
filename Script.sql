DROP SCHEMA IF EXISTS "tse" CASCADE;
CREATE SCHEMA "tse";

CREATE TABLE "tse".municipio (
    id_municipio     VARCHAR(10) PRIMARY KEY,
    cd_municipio_tse VARCHAR(10),
    nm_municipio_tse VARCHAR(100) NOT NULL,
    sg_uf            VARCHAR(2) NOT NULL
);

CREATE TABLE "tse".eleicao (
    id_eleicao   VARCHAR(20) PRIMARY KEY,
    ano          INT NOT NULL,
    tipo_eleicao VARCHAR(100),
    data_eleicao DATE
);

CREATE TABLE "tse".partido (
    numero_partido VARCHAR(10) PRIMARY KEY,
    sigla_partido  VARCHAR(20)
);

CREATE TABLE "tse".vaga (
    id_vaga      SERIAL PRIMARY KEY,
    id_eleicao   VARCHAR(20) NOT NULL,
    sigla_uf     VARCHAR(2),
    id_municipio VARCHAR(10),
    cargo        VARCHAR(100) NOT NULL,
    vagas        INT,
    FOREIGN KEY (id_eleicao)   REFERENCES "tse".eleicao(id_eleicao),
    FOREIGN KEY (id_municipio) REFERENCES "tse".municipio(id_municipio)
);

CREATE TABLE "tse".pessoa (
    titulo_eleitoral VARCHAR(20) PRIMARY KEY,
    cpf              VARCHAR(20),
    nome             VARCHAR(255) NOT NULL,
    data_nascimento  DATE,
    genero           VARCHAR(50),
    raca             VARCHAR(50)
);

CREATE TABLE "tse".candidatura (
    sequencial_candidato VARCHAR(50),
    titulo_eleitoral     VARCHAR(20) NOT NULL,
    id_eleicao           VARCHAR(20) NOT NULL,
    numero_partido       VARCHAR(10) NOT NULL,
    id_municipio         VARCHAR(10),
    sigla_uf             VARCHAR(2),
    cargo                VARCHAR(100) NOT NULL,
    numero_urna          VARCHAR(20),
    nome_urna            VARCHAR(255),
    situacao             VARCHAR(100),
    CONSTRAINT pk_candidatura PRIMARY KEY (titulo_eleitoral, id_eleicao),
    FOREIGN KEY (titulo_eleitoral) REFERENCES "tse".pessoa(titulo_eleitoral),
    FOREIGN KEY (id_eleicao)       REFERENCES "tse".eleicao(id_eleicao),
    FOREIGN KEY (numero_partido)   REFERENCES "tse".partido(numero_partido)
);

CREATE TABLE "tse".bem_patrimonial (
    id_bem           SERIAL PRIMARY KEY,
    titulo_eleitoral VARCHAR(20) NOT NULL,
    id_eleicao       VARCHAR(20) NOT NULL,
    tipo_item        VARCHAR(150),
    descricao_item   TEXT,
    valor_item       DECIMAL(15,2),
    FOREIGN KEY (titulo_eleitoral, id_eleicao)
        REFERENCES "tse".candidatura(titulo_eleitoral, id_eleicao)
);

CREATE TABLE "tse".receita (
    id_receita       SERIAL PRIMARY KEY,
    ano              INT,
    titulo_eleitoral VARCHAR(20) NOT NULL,
    id_eleicao       VARCHAR(20) NOT NULL,
    valor            DECIMAL(15,2),
    FOREIGN KEY (titulo_eleitoral, id_eleicao)
        REFERENCES "tse".candidatura(titulo_eleitoral, id_eleicao)
);

CREATE TABLE "tse".despesa (
    id_despesa       SERIAL PRIMARY KEY,
    ano              INT,
    titulo_eleitoral VARCHAR(20) NOT NULL,
    id_eleicao       VARCHAR(20) NOT NULL,
    cnae_2_subclasse VARCHAR(20) NOT NULL DEFAULT 'nao informado',
    valor            DECIMAL(15,2),
    FOREIGN KEY (titulo_eleitoral, id_eleicao)
        REFERENCES "tse".candidatura(titulo_eleitoral, id_eleicao)
);

CREATE TABLE "tse".resultado_candidatura_uf (
    titulo_eleitoral VARCHAR(20) NOT NULL,
    id_eleicao       VARCHAR(20) NOT NULL,
    sigla_uf         VARCHAR(2)  NOT NULL,
    votos            INT,
    CONSTRAINT pk_resultado PRIMARY KEY (titulo_eleitoral, id_eleicao, sigla_uf),
    FOREIGN KEY (titulo_eleitoral, id_eleicao)
        REFERENCES "tse".candidatura(titulo_eleitoral, id_eleicao)

);