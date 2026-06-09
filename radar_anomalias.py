import mysql.connector
from mysql.connector import Error
import time
import os
import platform

# ==========================================
# 1. CONFIGURAÇÕES
# ==========================================
DB_CONFIG = {
    'host': 'localhost',      
    'user': 'root',           
    'password': '123123',           # <--- COLOQUE SUA SENHA AQUI NOVAMENTE
    'database': 'cassino_analytics'
}

# Gatilhos de Anomalia
RTP_PICO_ALTA = 1000.00 
RTP_PICO_BAIXA = 5.00 # Se pagar menos de 5%, está praticamente "congelado"

# Paleta de Cores do Terminal (ANSI)
COR_VERMELHA = '\033[91m'
COR_VERDE = '\033[92m'
COR_AMARELA = '\033[93m'
COR_AZUL_CLARO = '\033[96m'
COR_AZUL_ESCURO = '\033[94m'
COR_BRANCA = '\033[97m'
RESETAR_COR = '\033[0m'

# ==========================================
# 2. FUNÇÕES DO SISTEMA
# ==========================================
def limpar_tela():
    if platform.system() == "Windows":
        os.system('cls')
    else:
        os.system('clear')

def emitir_bipe():
    try:
        if platform.system() == "Windows":
            import winsound
            winsound.Beep(1000, 500) 
        else:
            print('\a') 
    except:
        pass 

def buscar_radar_completo():
    """Busca o lote exato de dados mais recente e divide entre Quentes e Frios."""
    conexao = None
    try:
        conexao = mysql.connector.connect(**DB_CONFIG)
        if conexao.is_connected():
            cursor = conexao.cursor(dictionary=True)
            
            # 1. Encontra o momento exato da última extração para evitar misturar dados
            cursor.execute("SELECT MAX(timestamp_coleta) as ultima_coleta FROM historico_rtp")
            resultado_tempo = cursor.fetchone()
            ultima_coleta = resultado_tempo['ultima_coleta'] if resultado_tempo else None
            
            if not ultima_coleta:
                return None, [], []

            # 2. Puxa os 5 mais QUENTES dessa coleta (Do maior RTP para o menor)
            sql_hot = """
                SELECT nome_jogo, rtp_momentaneo 
                FROM historico_rtp 
                WHERE trend_status = 'Hot' AND timestamp_coleta = %s
                ORDER BY rtp_momentaneo DESC LIMIT 5;
            """
            cursor.execute(sql_hot, (ultima_coleta,))
            jogos_hot = cursor.fetchall()
            
            # 3. Puxa os 5 mais FRIOS dessa coleta (Do MENOR RTP para o maior)
            sql_cold = """
                SELECT nome_jogo, rtp_momentaneo 
                FROM historico_rtp 
                WHERE trend_status = 'Cold' AND timestamp_coleta = %s
                ORDER BY rtp_momentaneo ASC LIMIT 5;
            """
            cursor.execute(sql_cold, (ultima_coleta,))
            jogos_cold = cursor.fetchall()
            
            return ultima_coleta, jogos_hot, jogos_cold
            
    except Error as e:
        print(f"{COR_VERMELHA}Erro de Banco de Dados: {e}{RESETAR_COR}")
        return None, [], []
    finally:
        if conexao and conexao.is_connected():
            cursor.close()
            conexao.close()

# ==========================================
# 3. PAINEL DE MONITORAMENTO (LOOP)
# ==========================================
if __name__ == "__main__":
    print("Iniciando Radar Duplo de Volatilidade...")
    time.sleep(2)
    intervalo_radar = 10 
    
    try:
        while True:
            ultima_atualizacao, hot_data, cold_data = buscar_radar_completo()
            limpar_tela()
            
            print(f"{COR_BRANCA}===================================================={RESETAR_COR}")
            print(f"{COR_BRANCA}       RADAR DE VOLATILIDADE - NOLIMIT CITY         {RESETAR_COR}")
            print(f"{COR_BRANCA}===================================================={RESETAR_COR}\n")
            
            if not ultima_atualizacao:
                print("Aguardando dados... (Verifique se o coletor principal está rodando)")
            else:
                print(f"Última varredura sincronizada: {ultima_atualizacao}\n")
                anomalia_detectada = False
                
                # --- SESSÃO HOT ---
                print(f"{COR_VERMELHA}🔥 TOP 5 - HOT AS HELL (Maior Pagamento){RESETAR_COR}")
                print(f"{COR_VERMELHA}-{RESETAR_COR}" * 52)
                for idx, jogo in enumerate(hot_data, 1):
                    nome = jogo['nome_jogo']
                    rtp = float(jogo['rtp_momentaneo'])
                    
                    if rtp >= RTP_PICO_ALTA:
                        cor = COR_VERDE
                        alerta = "💰 ANOMALIA DE ALTA"
                        anomalia_detectada = True
                    elif rtp >= 500:
                        cor = COR_AMARELA
                        alerta = "⚠️ Superaquecendo"
                    else:
                        cor = RESETAR_COR
                        alerta = ""
                        
                    print(f"{idx}. {cor}{nome.ljust(25)} | RTP: {rtp:7.2f}% | {alerta}{RESETAR_COR}")
                
                print("\n")
                
                # --- SESSÃO COLD ---
                print(f"{COR_AZUL_CLARO}❄️ TOP 5 - COLD AS ICE (Maior Retenção){RESETAR_COR}")
                print(f"{COR_AZUL_CLARO}-{RESETAR_COR}" * 52)
                for idx, jogo in enumerate(cold_data, 1):
                    nome = jogo['nome_jogo']
                    rtp = float(jogo['rtp_momentaneo'])
                    
                    # Logica invertida: quanto MENOR, mais anômalo
                    if rtp <= RTP_PICO_BAIXA:
                        cor = COR_VERMELHA
                        alerta = "🧊 ANOMALIA DE BAIXA (Congelado)"
                        anomalia_detectada = True
                    elif rtp <= 20:
                        cor = COR_AZUL_ESCURO
                        alerta = "Resfriando rápido"
                    else:
                        cor = RESETAR_COR
                        alerta = ""
                        
                    print(f"{idx}. {cor}{nome.ljust(25)} | RTP: {rtp:7.2f}% | {alerta}{RESETAR_COR}")

                # Toca o som apenas uma vez por atualização de tela, se houver qualquer anomalia
                    
            print(f"\n{COR_BRANCA}----------------------------------------------------{RESETAR_COR}")
            print(f"Atualizando em {intervalo_radar} segundos... Pressione Ctrl+C para sair.")
            
            time.sleep(intervalo_radar)
            
    except KeyboardInterrupt:
        limpar_tela()
        print("Radar desligado pelo usuário. Sistema encerrado.")