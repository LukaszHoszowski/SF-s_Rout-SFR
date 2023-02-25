class OutdatedSIDError(Exception):
    """
    Exception raised for errors in the SID value.

    ...

    Attributes
    ----------
    message: str
        explanation of the error
    """

    def __init__(self, message: str = "Your SID is outdate, please provide recent SID"):
        self.message = message
        super().__init__(self.message)


class EnvFileNotPresent(Exception):
    """
    Exception raised if the .env file is not present in main directory.

    ...

    Attributes
    ----------
    message: str
        explanation of the error
    """

    def __init__(self, message: str = ".env file not present in main directory"):
        self.message = message
        super().__init__(self.message)

if __name__ == '__main__':
    pass
