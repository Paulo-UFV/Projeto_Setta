import os

templates_path = os.path.join(os.path.dirname(__file__), 'templates')
print("Caminho para a pasta 'templates':", templates_path)

try:
    files = os.listdir(templates_path)
    print("Arquivos na pasta 'templates':", files)
except FileNotFoundError:
    print("Pasta 'templates' não encontrada.")
except Exception as e:
    print("Ocorreu um erro:", e)
