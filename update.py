from modules.main import execute_update_games, execute_update_data, update_ranking_by_games
from modules.utils import get_current_dic_modalities_page, print_colored, print_magenta
from modules.zero import execute_zero_ranking
from modules.playoff import execute_update_data_playoff
from colorama import Fore, Style

dic_modalities_page = get_current_dic_modalities_page()

def menu():
    
    print_colored("O que deseja atualizar?", Fore.YELLOW)
    print_colored("G - Tudo da fase de grupos")
    print_colored("J - Apenas Jogos")
    print_colored("P - Tudo do playoff")
    print_colored("R - Ranking por modalidade")
    print_colored("Z - do zero")
    
    choice = input(Fore.GREEN + "Escolha uma opção: " + Style.RESET_ALL).capitalize()
    
    if choice == "G":
        update_all_group()
    elif choice == "R":
        update_ranking_by_modality()
    elif choice == "J":
        update_games()
    elif choice == "P":
        update_playoff()
    elif choice == "Z":
        update_data_from_zero()
    else:
        print("Opção inválida.")

def update_all_group():
    print_magenta("Atualizando tudo...")
    execute_update_data(dic_modalities_page)

def update_data_from_zero():
    print_magenta("Atualizando do zero...")
    execute_zero_ranking(dic_modalities_page)

def update_ranking_by_modality():
    modality = input(Fore.GREEN + "Informe a modalidade (ex: FM/A): " + Style.RESET_ALL)
    print_magenta(f"Atualizando ranking para a modalidade {modality}...")
    update_ranking_by_games(modality)

def update_playoff():
    execute_update_data_playoff(dic_modalities_page)
    # modality = input(Fore.GREEN + "Informe a modalidade (ex: FM/A): " + Style.RESET_ALL)
    # if modality:
    #     print_magenta(f"Atualizando playoff para a modalidade {modality}...")
    #     playoff.execute_update_data_playoff_by_modality(modality)
    # else:
    #   playoff.execute_update_data_playoff(dic_modalities_page)

def update_games():
    print_magenta("Atualizando apenas jogos...")
    execute_update_games(dic_modalities_page)

if __name__ == "__main__":
    menu()