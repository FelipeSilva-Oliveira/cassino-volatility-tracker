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

COR_VERDE = '\033[92m'
COR_AZUL = '\033[96m'
COR_AMARELA = '\033[93m'
COR_BRANCA = '\033[97m'
RESETAR_COR = '\033[0m'

def limpar_tela():
    if platform.system() == "Windows":
        os.system('cls')
    else:
        os.system('clear')

# ==========================================
# 2. MOTOR DE ANÁLISE E GRAVAÇÃO (ETL GOLD)
# ==========================================
def processar_ciclos():
    conexao = None
    try:
        conexao = mysql.connector.connect(**DB_CONFIG)
        if conexao.is_connected():
            cursor = conexao.cursor(dictionary=True)
            
            # PASSO 1: Extrair os ciclos da tabela bruta
            # PASSO 1: Extrair apenas o ciclo mais recente (Cold imediato antes do último Hot)
            sql_analise = """
                SELECT 
                    h.nome_jogo,
                    c.timestamp_coleta AS data_entrou_cold,
                    h.timestamp_coleta AS data_virou_hot,
                    TIMESTAMPDIFF(MINUTE, c.timestamp_coleta, h.timestamp_coleta) AS minutos_para_recuperar,
                    c.rtp_momentaneo AS rtp_quando_frio,
                    h.rtp_momentaneo AS rtp_quando_quente
                FROM historico_rtp h
                
                -- JOIN para conectar com a tabela no estado COLD
                JOIN historico_rtp c ON c.id_jogo = h.id_jogo
                
                WHERE h.trend_status = 'Hot'
                  -- Regra 1: Pega apenas a linha do "Hot" MAIS RECENTE daquele jogo
                  AND h.timestamp_coleta = (
                      SELECT MAX(timestamp_coleta) 
                      FROM historico_rtp 
                      WHERE id_jogo = h.id_jogo AND trend_status = 'Hot'
                  )
                  
                  AND c.trend_status = 'Cold'
                  -- Regra 2: Pega apenas o "Cold" MAIS RECENTE que aconteceu ANTES desse Hot
                  AND c.timestamp_coleta = (
                      SELECT MAX(timestamp_coleta)
                      FROM historico_rtp
                      WHERE id_jogo = h.id_jogo 
                        AND trend_status = 'Cold'
                        AND timestamp_coleta < h.timestamp_coleta
                  )
                
                -- Opcional: Ignora bizarrices de servidor (ex: pulos de mais de 12 horas / 720 minutos)
                AND TIMESTAMPDIFF(MINUTE, c.timestamp_coleta, h.timestamp_coleta) < 720
                
                -- Mostra os ciclos mais recentes primeiro no topo do painel
                ORDER BY minutos_para_recuperar DESC, data_virou_hot DESC;
            """
            cursor.execute(sql_analise)
            resultados = cursor.fetchall()
            
            # PASSO 2: Salvar na tabela de Ouro (ignorando duplicatas)
            if resultados:
                sql_insert = """
                    INSERT IGNORE INTO ciclos_volatilidade (
                        nome_jogo, data_entrou_cold, data_virou_hot, 
                        minutos_para_recuperar, rtp_quando_frio, rtp_quando_quente
                    ) VALUES (
                        %(nome_jogo)s, %(data_entrou_cold)s, %(data_virou_hot)s, 
                        %(minutos_para_recuperar)s, %(rtp_quando_frio)s, %(rtp_quando_quente)s
                    )
                """
                cursor.executemany(sql_insert, resultados)
                conexao.commit()
                # Opcional: print(f"Salvos/Atualizados {cursor.rowcount} novos ciclos.")

            return resultados
            
    except Error as e:
        print(f"Erro no processamento de ciclos: {e}")
        return []
    finally:
        if conexao and conexao.is_connected():
            cursor.close()
            conexao.close()

# ==========================================
# 3. PAINEL DE MONITORAMENTO (LOOP)
# ==========================================
if __name__ == "__main__":
    print("Iniciando Pipeline da Camada Ouro (Extração e Armazenamento)...")
    time.sleep(2)
    
    intervalo_segundos = 60 
    
    try:
        while True:
            dados_ciclo = processar_ciclos()
            limpar_tela()
            
            print(f"{COR_BRANCA}================================================================================{RESETAR_COR}")
            print(f"{COR_BRANCA}           PIPELINE GOLD: CICLOS DE VOLATILIDADE ARMAZENADOS COM SUCESSO        {RESETAR_COR}")
            print(f"{COR_BRANCA}================================================================================{RESETAR_COR}")
            print(f"Última varredura e sincronização no banco: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n")
            
            if not dados_ciclo:
                print("Monitorando a base de dados... Nenhum ciclo completo mapeado ainda.")
            else:
                print(f"{'JOGO':<25} | {'TEMPO DE CICLO':<15} | {'RTP NO FUNDO'} -> {'RTP NO PICO'}")
                print("-" * 80)
                
                for linha in dados_ciclo[:100]:
                    jogo = linha['nome_jogo']
                    tempo_min = linha['minutos_para_recuperar']
                    rtp_frio = float(linha['rtp_quando_frio'])
                    rtp_quente = float(linha['rtp_quando_quente'])
                    
                    if tempo_min > 60:
                        horas = tempo_min // 60
                        minutos = tempo_min % 60
                        tempo_str = f"{horas}h {minutos}m"
                    else:
                        tempo_str = f"{tempo_min} min"
                        
                    print(f"{jogo:<25} | {COR_AZUL}{tempo_str:<15}{RESETAR_COR} | {rtp_frio:5.2f}% -> {COR_VERDE}{rtp_quente:7.2f}%{RESETAR_COR}")
                    
                print("-" * 80)
                print(f"Total de ciclos mapeados e salvos em 'ciclos_volatilidade': {len(dados_ciclo)}")
            
            print(f"\nAtualizando novamente em {intervalo_segundos} segundos. Pressione Ctrl+C para sair.")
            time.sleep(intervalo_segundos)
            
    except KeyboardInterrupt:
        limpar_tela()
        print("Pipeline Gold desligado com segurança.")