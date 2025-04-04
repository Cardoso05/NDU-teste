import json
import os


def get_games_filepths(base_dir):

    # Lista para armazenar os caminhos dos arquivos
    games_files = []

    # Percorre todos os subdiretórios no diretório base
    for subdir, _, _ in os.walk(base_dir):
        # Verifica se há um arquivo 'games.json' no diretório atual
        game_file = os.path.join(subdir, 'games.json')
        if os.path.exists(game_file):
            # Adiciona o caminho do arquivo à lista
            games_files.append(game_file)

    return games_files


def load_json_data(filepath_json):
    # Carregar o conteúdo do arquivo JSON
    with open(filepath_json, 'r', encoding='utf-8') as file:
        return json.load(file)

def create_json(data, filename):
    # Gravar os dados em um arquivo JSON
    with open(filename, 'w', encoding='utf-8') as outfile:
        json.dump(data, outfile, indent=4, ensure_ascii=False)

def filter_by_day_and_local(day, local):
    data = load_json_data('all_games.json')
    filtered_data = [
        {
            "modality": item["modality"],
            "data": [game for game in item["data"] if game["DIA"] == day and game["LOCAL"] == local]
        }
        for item in data
    ]
    return filtered_data


def generate_all_games(list_files):
    # Carregar os dados de todos os arquivos JSON
    all_data = []
    for file in list_files:
        modality = file.replace('files\\', '').replace('\\games.json', '').replace('\\', '/')
        all_data.append(
            {
                'modality': modality,
                'data': load_json_data(file)
            }
            )

    # Criar um arquivo JSON com todos os dados combinados
    create_json(all_data, 'all_games.json')


games_files = get_games_filepths("files")
generate_all_games(games_files)
