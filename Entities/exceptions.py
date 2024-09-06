class CredentialNotFound(Exception):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)

class LoginPageNotFound(Exception):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)
        
class LoginError(Exception):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)
        
class NotAuthenticated(Exception):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)
        