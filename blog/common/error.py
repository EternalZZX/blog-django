from blog.common.result import Dictable, NoneObject


class AccountError(Exception, Dictable):
    def __init__(self, error=NoneObject(), code=500, title="", message=""):
        self.code = code or error.code
        self.title = title or error.title
        self.message = message or error.message
