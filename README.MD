# 🎰 Radar de Volatilidade: Data Pipeline end-to-end (Nolimit City)

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?logo=streamlit&logoColor=white)](https://streamlit.io/)
[![MySQL](https://img.shields.io/badge/MySQL-00000F?logo=mysql&logoColor=white)](https://www.mysql.com/)
[![Selenium](https://img.shields.io/badge/Selenium-43B02A?logo=selenium&logoColor=white)](https://www.selenium.dev/)

## 1. Visão Geral do Projeto
Este projeto consiste no desenvolvimento de uma aplicação de dados (Data App) em tempo real que captura, processa e analisa flutuações de RTP (*Return to Player*) instantâneas em jogos de slots de alta volatilidade da provedora Nolimit City. 

O objetivo central é mapear o tempo médio que um jogo leva para sair de uma janela de retenção de prêmios (*Cold*) e entrar em uma janela de pico de distribuição (*Hot*), fornecendo análises preditivas básicas através de uma interface web interativa.

## 2. Arquitetura da Solução (Medallion Architecture)
O projeto foi estruturado seguindo as melhores práticas de Engenharia de Dados, separando a ingestão, o armazenamento e a visualização:

* **Camada de Ingestão:** Web Scraper desenvolvido em Python com Selenium para extração contínua e assíncrona de dados estruturados do painel ao vivo da provedora.
* **Camada Bronze (Armazenamento Bruto):** Banco de dados relacional (MariaDB/MySQL) armazenando o histórico minuto a minuto das flutuações de mercado.
* **Camada Ouro (ETL e Agregação):** Script automatizado em Python que limpa ruídos de dados e consolida ciclos fechados de volatilidade em uma tabela exclusiva otimizada para queries analíticas e modelos preditivos.
* **Camada de Visualização:** Dashboard interativo em tempo real construído com Streamlit e Plotly, utilizando fragmentos (`@st.fragment`) para atualização assíncrona sem recarregamento da página.

## 3. Como Executar o Projeto Localmente

### Pré-requisitos
* Python 3.8+
* Servidor MySQL/MariaDB rodando localmente.

### Instalação
1. Clone este repositório:
   ```bash
   git clone [https://github.com/FelipeSilva-Oliveira/NOME_DO_SEU_REPOSITORIO.git](https://github.com/FelipeSilva-Oliveira/NOME_DO_SEU_REPOSITORIO.git)
   cd NOME_DO_SEU_REPOSITORIO