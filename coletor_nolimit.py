import mysql.connector
from mysql.connector import Error
from datetime import datetime
import time

# Bibliotecas do Selenium
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# ==========================================
# 1. CONFIGURAÇÕES
# ==========================================
DB_CONFIG = {
    'host': 'localhost',      
    'user': 'root',           
    'password': '123123',  # Insira a senha definida na instalação do MySQL
    'database': 'cassino_analytics'
}

URL_NOLIMIT = "https://www.nolimitcity.com/" # Ou a URL exata onde fica a lista

# ==========================================
# 2. INICIALIZAÇÃO DO NAVEGADOR
# ==========================================
def iniciar_navegador():
    chrome_options = Options()
    # Deixando o navegador visível para você ver a mágica acontecer. 
    # Depois, você pode descomentar a linha abaixo para rodar em modo "fantasma".
    # chrome_options.add_argument("--headless") 
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

    servico = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=servico, options=chrome_options)
    return driver

# ==========================================
# 3. MOTOR DE EXTRAÇÃO CIRÚRGICA
# ==========================================
def processar_jogos(elementos, status, agora):
    """Função auxiliar para ler os dados limpos de cada card"""
    dados = []
    for item in elementos:
        try:
            # Busca as tags baseadas na sua investigação
            nome = item.find_element(By.TAG_NAME, "p").text
            porcentagem_texto = item.find_element(By.CSS_SELECTOR, "div.font-semibold").text 
            
            # Limpeza do dado ("1487%" -> 1487.0)
            rtp_limpo = float(porcentagem_texto.replace('%', '').replace(',', '.').strip())
            
            registro = {
                "timestamp_coleta": agora.strftime('%Y-%m-%d %H:%M:%S'),
                "data_coleta": agora.strftime('%Y-%m-%d'),
                "hora_coleta": agora.strftime('%H:%M:%S'),
                "dia_da_semana": agora.isoweekday(),
                "minuto_do_dia": (agora.hour * 60) + agora.minute,
                
                "id_jogo": nome.lower().replace(" ", "_").strip(),
                "nome_jogo": nome.strip(),
                "provedora": "Nolimit City",
                "categoria_jogo": "Slots",
                
                "rtp_momentaneo": rtp_limpo,
                "multiplicador_maximo_recente": 0.00, 
                "volume_jogadores": None, 
                "trend_status": status,
                "site_origem": URL_NOLIMIT
            }
            dados.append(registro)
            
        except Exception as e_item:
            # Ignora erros silenciosamente (ex: elemento não visível na tela) e pula para o próximo
            continue
            
    return dados

def extrair_dados_nolimit(driver):
    try:
        driver.get(URL_NOLIMIT)
        
        # Espera inteligente: Aguarda até o primeiro jogo "Hot" aparecer na tela
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div.bg-gradient-playin-hot"))
        )
        
        agora = datetime.now()
        dados_totais = []
        
        # 1. Coleta os jogos QUENTES
        elementos_hot = driver.find_elements(By.CSS_SELECTOR, "div.bg-gradient-playin-hot")
        dados_totais.extend(processar_jogos(elementos_hot, "Hot", agora))
        
        # 2. Coleta os jogos FRIOS
        # Assumindo a mesma lógica de nomenclatura da Nolimit City para o painel azul
        try:
            elementos_cold = driver.find_elements(By.CSS_SELECTOR, "div.bg-gradient-playin-cold")
            dados_totais.extend(processar_jogos(elementos_cold, "Cold", agora))
        except:
            print("Aviso: Contêineres 'Cold' não encontrados ou usam classe diferente.")
            
        return dados_totais

    except Exception as e:
        print(f"Erro ao acessar a página. O site pode estar lento ou ter mudado: {e}")
        return []

# ==========================================
# 4. SALVAMENTO (DATA LOAD)
# ==========================================
def salvar_no_banco_local(dados):
    if not dados:
        print("Nenhum dado extraído nesta rodada.")
        return
        
    conexao = None
    try:
        conexao = mysql.connector.connect(**DB_CONFIG)
        if conexao.is_connected():
            cursor = conexao.cursor()
            
            sql_insert = """
                INSERT INTO historico_rtp (
                    timestamp_coleta, data_coleta, hora_coleta, dia_da_semana, minuto_do_dia,
                    id_jogo, nome_jogo, provedora, categoria_jogo,
                    rtp_momentaneo, multiplicador_maximo_recente, volume_jogadores,
                    trend_status, site_origem
                ) VALUES (
                    %(timestamp_coleta)s, %(data_coleta)s, %(hora_coleta)s, %(dia_da_semana)s, %(minuto_do_dia)s,
                    %(id_jogo)s, %(nome_jogo)s, %(provedora)s, %(categoria_jogo)s,
                    %(rtp_momentaneo)s, %(multiplicador_maximo_recente)s, %(volume_jogadores)s,
                    %(trend_status)s, %(site_origem)s
                )
            """
            cursor.executemany(sql_insert, dados)
            conexao.commit()
            print(f"[{datetime.now().strftime('%H:%M:%S')}] OK: {cursor.rowcount} registros atualizados no banco de dados.")
            
    except Error as e:
        print(f"Erro Crítico no Banco de Dados: {e}")
    finally:
        if conexao and conexao.is_connected():
            cursor.close()
            conexao.close()

# ==========================================
# 5. EXECUÇÃO EM LOOP (PIPELINE)
# ==========================================
if __name__ == "__main__":
    print("==================================================")
    print("  INICIANDO PIPELINE DE DADOS: NOLIMIT CITY")
    print("==================================================")
    
    driver_principal = iniciar_navegador()
    
    # Executa a cada 5 minutos (300 segundos)
    # Recomendação: Não diminua muito este tempo para evitar banimento por IP do site alvo.
    intervalo_tempo = 60 
    
    try:
        while True:
            print(f"\nExtraindo dados em: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
            
            novos_dados = extrair_dados_nolimit(driver_principal)
            salvar_no_banco_local(novos_dados)
            
            print(f"Dormindo por {intervalo_tempo // 60} minutos...")
            time.sleep(intervalo_tempo)
            
    except KeyboardInterrupt:
        print("\nPipeline interrompido pelo usuário.")
    finally:
        driver_principal.quit()
        print("Sessão do navegador encerrada.")