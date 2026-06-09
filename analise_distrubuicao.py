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
# 2. MOTOR ESTATÍSTICO (DISTRIBUIÇÃO)
# ==========================================
def calcular_distribuicao_frequencia():
    conexao = None
    try:
        conexao = mysql.connector.connect(**DB_CONFIG)
        if conexao.is_connected():
            cursor = conexao.cursor(dictionary=True)
            
            # Query Avançada: Agregação condicional para criar os grupos de tempo
            sql_distribuicao = """
                SELECT 
                    nome_jogo,
                    AVG(minutos_para_recuperar) AS tempo_medio_geral,
                    COUNT(*) AS total_ciclos,
                    
                    -- Contagem por faixas de tempo (Bins)
                    SUM(CASE WHEN minutos_para_recuperar BETWEEN 1 AND 5 THEN 1 ELSE 0 END) AS faixa_1_5,
                    SUM(CASE WHEN minutos_para_recuperar > 5 AND minutos_para_recuperar <= 10 THEN 1 ELSE 0 END) AS faixa_5_10,
                    SUM(CASE WHEN minutos_para_recuperar > 10 AND minutos_para_recuperar <= 20 THEN 1 ELSE 0 END) AS faixa_10_20,
                    SUM(CASE WHEN minutos_para_recuperar > 20 THEN 1 ELSE 0 END) AS faixa_acima_20
                FROM ciclos_volatilidade
                GROUP BY nome_jogo
                ORDER BY tempo_medio_geral ASC;
            """
            
            cursor.execute(sql_distribuicao)
            resultados = cursor.fetchall()
            return resultados
            
    except Error as e:
        print(f"Erro no cálculo estatístico: {e}")
        return []
    finally:
        if conexao and conexao.is_connected():
            cursor.close()
            conexao.close()

# ==========================================
# 3. EXIBIÇÃO NO FORMATO DE PORTFÓLIO
# ==========================================
if __name__ == "__main__":
    intervalo_segundos = 60
    
    try:
        while True:
            dados = calcular_distribuicao_frequencia()
            limpar_tela()
            
            print(f"{COR_BRANCA}================================================================================{RESETAR_COR}")
            print(f"{COR_BRANCA}             DISTRIBUIÇÃO DE FREQUÊNCIA E TEMPO MÉDIO DE RECUPERAÇÃO            {RESETAR_COR}")
            print(f"{COR_BRANCA}================================================================================{RESETAR_COR}")
            print(f"Sincronizado em: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n")
            
            if not dados:
                print("Aguardando acúmulo de ciclos na tabela 'ciclos_volatilidade' para processar...")
            else:
                print(f"{'JOGO':<25} | {'MÉDIA GERAL':<12} | {'FAIXA DE TEMPO':<15} | {'FREQ. ABSOLUTA'}")
                print("-" * 80)
                
                for jogo in dados:
                    nome = jogo['nome_jogo']
                    media = float(jogo['tempo_medio_geral'])
                    
                    # Exibe os dados exatamente no formato de linhas por faixa que você pediu
                    # Se a faixa tiver 0 ocorrências, o script mostra para manter o rigor estatístico
                    print(f"{nome:<25} | {COR_AMARELA}{media:6.1f} min{RESETAR_COR} | {'1 a 5 min':<15} | {COR_VERDE}{jogo['faixa_1_5']}{RESETAR_COR} vezes")
                    print(f"{nome:<25} | {'':<12} | {'5 a 10 min':<15} | {COR_VERDE}{jogo['faixa_5_10']}{RESETAR_COR} vezes")
                    print(f"{nome:<25} | {'':<12} | {'10 a 20 min':<15} | {COR_VERDE}{jogo['faixa_10_20']}{RESETAR_COR} vezes")
                    print(f"{nome:<25} | {'':<12} | {'Acima de 20 min':<15} | {COR_VERDE}{jogo['faixa_acima_20']}{RESETAR_COR} vezes")
                    print("-" * 80)
                    
            print(f"\nAtualizando análise estatística em {intervalo_segundos} segundos. Ctrl+C para fechar.")
            time.sleep(intervalo_segundos)
            
    except KeyboardInterrupt:
        limpar_tela()
        print("Análise de distribuição encerrada.")