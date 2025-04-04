
import tabula
import pandas as pd
from datetime import datetime
import logging
import inspect
import modules.utils as utils
import modules.fixes as fixes
import modules.main as main

data_hora_atual = datetime.now()

dia_atual = data_hora_atual.date()

# Configuração básica de logging
# logging.basicConfig(filename='logs/log_ndu_' + data_hora_atual.strftime("%Y-%m-%d_%H-%M-%S") + '.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logging.basicConfig(filename='logs/debug_ndu_' + data_hora_atual.strftime("%Y-%m-%d_%H-%M-%S") + '.log', level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

def log_function_entry():
    function_name = inspect.currentframe().f_back.f_code.co_name
    logging.debug(f"Function: {function_name}")

def create_zero_ranking_group(table_groups, filepath):
    log_function_entry()
    dataframes = []
    
    header_zero = table_groups.columns[0]
    if 'grupo' not in header_zero.lower():
        logging.warning(f"header_zero inválido: {header_zero}")
        logging.info(f"Colocando o header atual na última linha")
        # Adicionar os cabeçalhos atuais à última linha de valores de cada coluna
        table_groups.loc[len(table_groups)+1] = table_groups.columns

        num_cols = table_groups.shape[1]
        new_headers = [f'Grupo {chr(65 + i)}' for i in range(num_cols)]

        logging.info(f"Atualizando headers")
        # Atualizar os cabeçalhos do DataFrame
        table_groups.columns = new_headers

    for group in ['Grupo A', 'Grupo B', 'Grupo C']:
        if group in table_groups:
            teams = table_groups[group].tolist()
            # Criar DataFrame vazio com as colunas necessárias
            columns = ['Time', 'Pontos', 'Jogos', 'V', 'E', 'D', 'Gols_Pro', 'Gols_Contra', 'Saldo']
            df_group = pd.DataFrame(columns=columns)
            
            # Adicionar nomes dos grupos
            df_group['Time'] = teams

            # Inicializar outras colunas com zeros
            for col in columns[1:]:
                df_group[col] = 0

            # Define o tipo de dados para as colunas
            dtypes = {'Pontos': int, 'Jogos': int, 'V': int, 'E': int, 'D': int, 'Gols_Pro': int, 'Gols_Contra': int, 'Saldo': int}
            df_group = df_group.astype(dtypes)
            df_group['ID'] = [utils.generate_game_id() for _ in range(len(df_group))]

            # Adicionar DataFrame à lista
            dataframes.append((group, df_group))

            # Salvar em JSON
            group_letter = group.split()[-1]
            json_data = df_group.to_dict(orient='records')
            utils.create_json(json_data, f"{filepath}/ranking_zero_{group_letter}.json")
        
    return dataframes

def execute_zero_ranking(dic_modalities_page):
    log_function_entry()
    for item in dic_modalities_page:
        # Cada item é um dicionário com uma única chave-valor
        modality, details = next(iter(item.items()))
        group_page_range = details['group_page_range']
        logging.info(f"modalidade: {modality} | group_page: {group_page_range}")
        tables = tabula.read_pdf("files/Boletim.pdf", pages=group_page_range)
        tb_group = fixes.format_tb_group(tables)
        print('Grupo página:', group_page_range)
        print(tb_group)
        tb_games = [tables[1], tables[2]]

        filepath = 'files/' + modality
        filepath_group = filepath + '/group'
        create_zero_ranking_group(tb_group, filepath_group)
        rankings_zero_group = main.get_rankings_zero_group(modality)
        teams = main.get_all_teams_by_rankings(rankings_zero_group)
        df_games = main.generate_table_games(tb_games)
        df_games = fixes.corrigir_local(df_games)
        df_games = fixes.corrigir_times(teams, df_games)
        utils.create_files(df_games, filepath)
        main.gerar_confronto_direto(df_games, filepath)

# dic_modalities_page = utils.get_current_dic_modalities_page()

# execute_zero_ranking(dic_modalities_page)