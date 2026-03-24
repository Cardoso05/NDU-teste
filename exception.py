class GameAlreadyExistsException(Exception):
    def __init__(self, message="Não é possível substituir um jogo que já existe."):
        self.message = message
        self.errorCode = 400
        super().__init__(self.message)

class FileNotFoundErrorException(Exception):
    def __init__(self, message="O arquivo de dados não foi encontrado."):
        self.message = message
        self.errorCode = 404
        super().__init__(self.message)

class MissingParameterError(Exception):
    def __init__(self, message="Parâmetro obrigatório não informado."):
        self.message = message
        self.errorCode = 400
        super().__init__(self.message)