import pandas as pd
import uuid
import csv
import json
import os
import logging
import inspect
import zipfile
import PyPDF2
import re
import locale
from datetime import datetime
from typing import List, Dict
from types import SimpleNamespace
from colorama import init, Fore, Style

data_hora_atual = datetime.now()

dia_atual = data_hora_atual.date()

logging.basicConfig(filename='logs/debug_ndu_' + data_hora_atual.strftime("%Y-%m-%d_%H-%M-%S") + '.log', level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

def log_function_entry():
    function_name = inspect.currentframe().f_back.f_code.co_name
    logging.debug(f"Function: {function_name}")

def generate_game_id():
    return str(uuid.uuid4())

def load_json_data(filepath):
    log_function_entry()
    """
    Carrega os dados de um arquivo JSON.

    :param filepath: O caminho para o arquivo JSON.
    :return: Os dados carregados do arquivo JSON.
    """
    with open(filepath, 'r', encoding='utf-8') as file:
        data = json.load(file)
    return data

def create_json(data, json_file):
    log_function_entry()
    with open(json_file, 'w', encoding='utf-8') as file:  # Certifique-se de especificar a codificação correta
        json.dump(data, file, indent=4, ensure_ascii=False)  # Especifica ensure_ascii=False para lidar com acentos
    
    logging.info('criado JSON em ' + json_file)

def csv_to_json(csv_file, json_file):
    log_function_entry()
    """
    Converte um arquivo CSV em um arquivo JSON.

    :param csv_file: Caminho para o arquivo CSV.
    :param json_file: Caminho para o arquivo JSON de saída.
    """
    # Lista para armazenar os dados do CSV
    data = []

    # Lendo o arquivo CSV e populando a lista de dados
    with open(csv_file, 'r', encoding='utf-8') as file:  # Certifique-se de especificar a codificação correta
        csv_reader = csv.DictReader(file)
        for row in csv_reader:
            data.append(row)

    # Escrevendo os dados em um arquivo JSON
    create_json(data, json_file)

def convert_to_json_serializable(value):
    """
    Converte um valor para um tipo que pode ser serializado em JSON.
    
    :param value: Valor a ser convertido.
    :return: Valor convertido para um tipo serializável em JSON.
    """
    if isinstance(value, pd.Timestamp):
        return value.strftime('%Y-%m-%d')  # Formato YYYY-MM-DD
    elif pd.isna(value):  # Lida com NaN, NaT e None
        return None
    elif isinstance(value, (list, dict, str, int, float, bool)):
        return value
    else:
        # Converte outros tipos para string, se necessário
        return str(value)

def create_json_from_df(df, json_file):
    """
    Converte um DataFrame em um arquivo JSON.

    :param df: DataFrame a ser convertido.
    :param json_file: Caminho para o arquivo JSON de saída.
    """
    log_function_entry()

    # Aplicar a conversão para cada valor do DataFrame
    df = df.map(convert_to_json_serializable)

    # Converter DataFrame para lista de dicionários
    data = df.to_dict(orient='records')
    create_json(data, json_file)

def save_json_data(data, file_path):
    log_function_entry()
    with open(file_path, 'w', encoding='utf-8') as file:
        json.dump(data, file, ensure_ascii=False, indent=4)

def create_files(df_games, filepath, filename='games'):
    log_function_entry()
    full_filepath=f'{filepath}/{filename}'
    json_file = f"{full_filepath}.json"
    create_json_from_df(df_games, json_file)

def create_backup_zipped(source_folder='files', backup_folder='backup'):
    # Certifique-se de que o diretório de backup existe
    if not os.path.exists(backup_folder):
        os.makedirs(backup_folder)

    # Obter a data e hora atuais
    data_hora_atual = datetime.now()
    timestamp = data_hora_atual.strftime("%Y-%m-%d_%H-%M-%S")

    # Criar o nome do arquivo zip
    zip_filename = f"backup_{timestamp}.zip"
    zip_filepath = os.path.join(backup_folder, zip_filename)

    # Criar o arquivo zip
    with zipfile.ZipFile(zip_filepath, 'w') as zipf:
        for root, dirs, files in os.walk(source_folder):
            for file in files:
                file_path = os.path.join(root, file)
                # Adicionar o arquivo ao zip
                zipf.write(file_path, os.path.relpath(file_path, source_folder))

    logging.info(f"Arquivo zip criado: {zip_filepath}")

def extrair_data_boletim(caminho_arquivo: str, numero_pagina: int) -> str:
    with open(caminho_arquivo, 'rb') as arquivo:
        leitor_pdf = PyPDF2.PdfReader(arquivo)
        
        if numero_pagina > len(leitor_pdf.pages):
            logging.info("Página não existe no documento.")
            return "Página não existe no documento."
        
        pagina = leitor_pdf.pages[numero_pagina - 1]  # Ajuste para indexação começando em 0
        texto_pagina = pagina.extract_text()
        
        # Usando expressão regular para encontrar o texto após "São Paulo, "
        padrao = r"São Paulo,\s*(.+)"
        match = re.search(padrao, texto_pagina)
        
        if match:
            return match.group(1).strip()
        else:
            logging.info("Não foi encontrado 'São Paulo, ' na página especificada.")
            return "Não foi encontrado 'São Paulo, ' na página especificada."

def converter_data_br_para_iso(data_str: str) -> str:
    # Configura o locale para português do Brasil
    locale.setlocale(locale.LC_TIME, 'pt_BR.UTF-8')

    # Converte a string para um objeto datetime
    data_obj = datetime.strptime(data_str, '%d de %B de %Y')

    # Formata a data no formato ISO (YYYY-MM-DD)
    return data_obj.strftime('%Y-%m-%d')

def buscar_strings_em_pdf(strings_procuradas: List[str], pagina_inicial: int = 1, pagina_final: int = None) -> Dict[str, int]:
    resultados = {}
    ultima_pagina_encontrada = pagina_inicial - 1
    caminho_arquivo  = 'files/Boletim.pdf'
    
    with open(caminho_arquivo, 'rb') as arquivo:
        leitor_pdf = PyPDF2.PdfReader(arquivo)
        numero_paginas = len(leitor_pdf.pages)
        
        # Ajusta o intervalo de páginas
        pagina_inicial = max(1, min(pagina_inicial, numero_paginas))
        if pagina_final is None or pagina_final > numero_paginas:
            pagina_final = numero_paginas
        else:
            pagina_final = max(pagina_inicial, min(pagina_final, numero_paginas))

        logging.info(f"Analisando páginas de {pagina_inicial} a {pagina_final} em um total de {numero_paginas} página(s).")

        for string in strings_procuradas:
            encontrado = False
            for i in range(ultima_pagina_encontrada, pagina_final):
                texto_pagina = leitor_pdf.pages[i].extract_text()
                
                if string and ' '.join(string.split()).lower() in ' '.join(texto_pagina.split()).lower():
                    resultados[string] = i + 1  # Adiciona o número da página (começando de 1)
                    ultima_pagina_encontrada = i
                    encontrado = True
                    break
            
            if not encontrado:
                resultados[string] = None
                logging.info(f"Não encontrado: {string}")

    return resultados

def create_obj_modalities(dic_modalities_page):
    return [
    {
        f"{('FF' if 'Feminino' in k else 'FM')}/{k.split('(')[1].split(')')[0].split()[-1]}": {
            'desc': k,
            'group_page_range': f"{v}-{v+1}",
            'playoff_page_range': f"{v+3}"
        }
    }
    for k, v in dic_modalities_page.items()
]

def generate_dic_modalities_page(update_file=False):
    desc_modalidades = [
        "Futsal Feminino (Série A)",
        "Futsal Feminino (Série B)",
        "Futsal Feminino (Série C)",
        "Futsal Feminino (Série D)",
        "Futsal Feminino (Série E)",
        "Futsal Masculino (Série A)",
        "Futsal Masculino (Série B)",
        "Futsal Masculino (Série C)",
        "Futsal Masculino (Série D)",
        "Futsal Masculino (Série E)",
        "Futsal Masculino (Série F)",
    ]

    page_range = SimpleNamespace(initial=40, final=115)
    resultados = buscar_strings_em_pdf(desc_modalidades, page_range.initial, page_range.final)
    obj_modalities = create_obj_modalities(resultados)
    if update_file: 
        create_json(obj_modalities, 'files/futsal_series_info.json')
    return obj_modalities

def get_current_dic_modalities_page():
    filename='files/futsal_series_info.json'
    if not os.path.exists(filename):
        logging.info(f"O arquivo {filename} não existe. Criando novo arquivo...")
        return generate_dic_modalities_page(True)
    else:
        return load_json_data(filename)

# Inicializa o colorama
init(autoreset=True)

def print_colored(text, color=Fore.CYAN, style=Style.BRIGHT):
    print(f"{style}{color}{text}{Style.RESET_ALL}")

def print_magenta(text):
    print_colored(text, Fore.MAGENTA)


def extract_and_save_team_names(dic_modalities_page):
    all_teams = set()

    for item in dic_modalities_page:
        modality = next(iter(item.keys()))
        for letter in ['A', 'B', 'C']:
            ranking_file_path = f'files/{modality}/group/ranking_zero_{letter}.json'
            
            # Verifica se o arquivo ranking_zero_{letter}.json existe
            if os.path.exists(ranking_file_path):
                ranking_file = load_json_data(ranking_file_path)
                for team_data in ranking_file:
                    all_teams.add(team_data['Time'])
            else:
                # Se o arquivo não existe, pula para a próxima letra ou modalidade
                continue

    # Converte o conjunto para uma lista e ordena
    all_teams_list = sorted(list(all_teams))

    create_json(all_teams_list, 'files/all_teams_name.json')