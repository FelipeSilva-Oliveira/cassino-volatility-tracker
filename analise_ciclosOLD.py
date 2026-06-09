import mysql.connector
from mysql.connector import Error
import time
import os
import platform
from datetime import datetime

# ==========================================
# 1. CONFIGURAÇÕES
# ==========================================
DB_CONFIG = {
    'host': 'localhost',      
    'user': 'root',           
    'password': '123123',           # <--- SUA SENHA DO WORKBENCH AQUI
    'database': 'cassino_analytics'
}

# Cores para o terminal
COR_VERDE = '\033[92m'
COR_AZUL = '\033[96m'
COR_AMARELA = '\033[93m'
COR_BRANCA = '\033[97m'
RESETAR_COR = '\033[0m'

# ==========================================
# 2. FUNÇÕES DE SISTEMA E BANCO
# ==========================================
def limpar_tela():
    if platform.system() == "Windows":
        os.system('cls')
    else:
        os.system('clear')

def analisar_tempo_recuperacao():
    conexao = None
    try:
        conexao = mysql.connector.connect(**DB_CONFIG)
        if conexao.is_connected():
            cursor = conexao.cursor(dictionary=True)
            
            # A "Magia" do SQL: Self Join para encontrar o ciclo Cold -> Hot
            sql_analise = """
                SELECT 
                    frio.nome_jogo,
                    frio.timestamp_coleta AS data_entrou_cold,
                    MIN(quente.timestamp_coleta) AS data_virou_hot,
                    TIMESTAMPDIFF(MINUTE, frio.timestamp_coleta, MIN(quente.timestamp_coleta)) AS minutos_para_recuperar,
                    frio.rtp_momentaneo AS rtp_quando_frio,
                    MIN(quente.rtp_momentaneo) AS rtp_quando_quente
                FROM historico_rtp frio
                
                -- Conecta a tabela com ela mesma procurando o futuro
                JOIN historico_rtp quente 
                    ON frio.id_jogo = quente.id_jogo 
                    AND quente.trend_status = 'Hot' 
                    AND quente.timestamp_coleta > frio.timestamp_coleta
                    
                WHERE frio.trend_status = 'Cold'
                
                -- Agrupa corretamente TODAS as colunas não-agregadas do SELECT
                GROUP BY 
                    frio.nome_jogo, 
                    frio.timestamp_coleta,
                    frio.rtp_momentaneo
                
                -- Ordena pelos jogos que demoraram MAIS tempo para virar Hot
                ORDER BY minutos_para_recuperar DESC;
            """
            
            cursor.execute(sql_analise)
            resultados = cursor.fetchall()
            return resultados
            
    except Error as e:
        print(f"Erro na análise: {e}")
        return []
    finally:
        if conexao and conexao.is_connected():
            cursor.close()
            conexao.close()

# ==========================================
# 3. PAINEL DE MONITORAMENTO (LOOP)
# ==========================================
if __name__ == "__main__":
    print("Iniciando Monitoramento Contínuo de Ciclos...")
    time.sleep(2)
    
    intervalo_segundos = 60 # Atualiza a tela a cada 1 minuto
    
    try:
        while True:
            dados_ciclo = analisar_tempo_recuperacao()
            limpar_tela()
            
            print(f"{COR_BRANCA}================================================================================{RESETAR_COR}")
            print(f"{COR_BRANCA}                 ANALISADOR DE CICLOS DE VOLATILIDADE (COLD -> HOT)             {RESETAR_COR}")
            print(f"{COR_BRANCA}================================================================================{RESETAR_COR}")
            print(f"Última atualização do painel: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n")
            
            if not dados_ciclo:
                print("Monitorando a base de dados... Nenhum ciclo completo mapeado ainda.")
            else:
                print(f"{'JOGO':<25} | {'TEMPO DE CICLO':<15} | {'RTP NO FUNDO'} -> {'RTP NO PICO'}")
                print("-" * 80)
                
                # Mostra os 15 ciclos mais relevantes
                for linha in dados_ciclo[:15]:
                    jogo = linha['nome_jogo']
                    tempo_min = linha['minutos_para_recuperar']
                    rtp_frio = float(linha['rtp_quando_frio'])
                    rtp_quente = float(linha['rtp_quando_quente'])
                    
                    # Formatação de tempo amigável
                    if tempo_min > 60:
                        horas = tempo_min // 60
                        minutos = tempo_min % 60
                        tempo_str = f"{horas}h {minutos}m"
                    else:
                        tempo_str = f"{tempo_min} min"
                        
                    print(f"{jogo:<25} | {COR_AZUL}{tempo_str:<15}{RESETAR_COR} | {rtp_frio:5.2f}% -> {COR_VERDE}{rtp_quente:7.2f}%{RESETAR_COR}")
                    
                print("-" * 80)
                print(f"Total de ciclos históricos mapeados: {len(dados_ciclo)}")
            
            print(f"\nAtualizando novamente em {intervalo_segundos} segundos. Pressione Ctrl+C para sair.")
            time.sleep(intervalo_segundos)
            
    except KeyboardInterrupt:
        limpar_tela()
        print("Analisador de ciclos desligado com segurança.")