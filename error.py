class ApiException(Exception):
    status_code = None
    text: str = None
    json: dict = None

    def __init__(self, status_code=None, text=None, json=None):
        self.status_code = status_code
        self.text = text
        self.json = json

        reason = text or json

        super().__init__(f'{self.status_code}: {reason}')
