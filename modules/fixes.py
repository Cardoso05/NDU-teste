import logging
import pandas as pd
from fuzzywuzzy import process
import re
from modules.utils import log_function_entry

LOCATIONS = {
    'Mackenzie', 'SENAC', 'Medicina USP', 'Palestra', 'USCS', 'Idalina', 'Pinheiros', 'Poliesportivo',
    'SEMEF', 'GETA', 'EDA', 'CESPRO', 'Mané Garrincha', 'Mauro Pinheiro', 'Baby Barione', 'CERET',
    'Lavínia', 'Sesi Cubatão', 'Mauá', 'Cidade Dutra'
}

def format_tb_group(tb_group_array):
    log_function_entry()
    for tb_group in tb_group_array:
        header_zero = tb_group.columns[0]
        if 'futsal' in header_zero.lower():
                logging.info(f"Tabela de Futsal encontrada. Passando para a próxima tabela.")
                continue
        
        if 'grupo' not in header_zero.lower():
            print('tb_group')
            print(tb_group)
            logging.warning(f"header_zero inválido: {header_zero}")
            logging.info(f"Colocando o header atual na última linha")
            # Adicionar os cabeçalhos atuais à última linha de valores de cada coluna
            tb_group.loc[len(tb_group)+1] = tb_group.columns

            num_cols = tb_group.shape[1]
            new_headers = [f'Grupo {chr(65 + i)}' for i in range(num_cols)]

            logging.info(f"Atualizando headers")
            # Atualizar os cabeçalhos do DataFrame
            tb_group.columns = new_headers
        return tb_group

def verificar_listagem(set_output, set_default):
    log_function_entry()
    elementos_ausentes = set(set_output) - set(set_default)
    if len(elementos_ausentes) > 0:
        logging.critical("Os seguintes elementos não estão listados:")
        logging.critical(elementos_ausentes)

from functools import lru_cache

@lru_cache(maxsize=None)
def correct_local(local):
    correction_local = {
        'Pale stra': 'Palestra',
        'Idal ina': 'Idalina',
        'SEM EF': 'SEMEF',
        'GE TA': 'GETA',
        'Mané Ga rrincha': 'Mané Garrincha',
        'US CS': 'USCS',
        'Baby B arione': 'Baby Barione',
        'Baby B arioni': 'Baby Barione',
        'SEN AC': 'SENAC',
        'CER ET': 'CERET',
        'Mack enzie': 'Mackenzie',
        'Mauro P inheiro': 'Mauro Pinheiro',
        'Medicin a USP': 'Medicina USP',
        'CDC Ip asure': 'CDC Ipasure',
        'APC EF': 'APCEF',
        'Poliesp ortivo': 'Poliesportivo',
        'Laví nia': 'Lavínia',
        'Lavínia': 'Lavínia',
        'Sesi Cu batão': 'Sesi Cubatão',
        'Ma uá': 'Mauá',
        'Cidade  Dutra': 'Cidade Dutra',
        'Cidade Dutra': 'Cidade Dutra',
    }
    return local if local in LOCATIONS else correction_local.get(local, local)

def corrigir_local(df_games):
    logging.info("Iniciando correção de locais")
    df_games['LOCAL'] = df_games['LOCAL'].map(correct_local)
    verificar_listagem(df_games['LOCAL'].unique(), LOCATIONS)
    return df_games

# correct_teams = utils.load_json_data('files/all_teams_name.json')

# Lista de palavras comuns em nomes de equipes
COMMON_WORDS = ['Comunicação', 'Direito', 'Engenharia', 'Medicina', 'Odontologia', 'Veterinária', 
                'Arquitetura', 'Economia', 'Psicologia', 'Farmácia', 'Educação', 'Física', 'Mackenzie',
                'UFABC', 'CAAP', 'Cásper', 'Líbero', 'Anhembi', 'USP', 'São', 'Bernardo', 
                'FMU', 'UNICAMP', 'ESEG', 'ESPM', 'FAAP', 'PUC', 'Palmares', 'ICBIÓ', 'USP']

def preprocess_team_name(name):
    # Remover espaços extras e caracteres especiais
    name = re.sub(r'\s+', ' ', name)
    name = re.sub(r'[^\w\s]', '', name)
    return name.strip()

def find_best_match(name, correct_teams, threshold=80):
    # Primeiro, tenta encontrar uma correspondência exata
    if name in correct_teams:
        return name
    
    # Se não encontrar, usa a comparação fuzzy
    best_match = process.extractOne(name, correct_teams)
    if best_match and best_match[1] >= threshold:
        return best_match[0]
    
    # Se ainda não encontrou uma correspondência, retorna o nome original
    return name

def corrigir_times(correct_teams, df_games):
    correct_teams_set = set(correct_teams)
    
    def correct_team(name):
        name = preprocess_team_name(name)
        return find_best_match(name, correct_teams_set)
    
    df_games['Mandante'] = df_games['Mandante'].apply(correct_team)
    df_games['Visitante'] = df_games['Visitante'].apply(correct_team)
    
    return df_games

def corrigir_horario(df):
    log_function_entry()
    # Corrigir o campo 'HORARIO' para cada jogo no DataFrame
    for index, row in df.iterrows():
        horario = str(row['HORARIO']).replace(" ", "")  # Remover espaços em branco
        horario = horario[-8:]  # Pegar os últimos 8 caracteres
        df.at[index, 'HORARIO'] = horario  # Atualizar o valor do campo 'HORARIO'
    
    return df

def corrigir_dia(games_data):
    log_function_entry()
    # Corrigir a coluna 'DIA' se estiver no formato de data e hora completa
    games_data['DIA'] = games_data['DIA'].apply(lambda x: str(x)[:10] if pd.notnull(x) else x)
    
    return games_data