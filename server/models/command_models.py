# Modelli relativi al Command

class CreateUserCommand:
    def __init__(self, email, password, ticker, lowValue, highValue, requestID):
        self.email = email
        self.password = password
        self.ticker = ticker
        self.lowValue = lowValue
        self.highValue = highValue
        self.requestID= requestID

class UpdateUserCommand:
    def __init__(self, email, ticker, requestID):
        self.email = email
        self.ticker = ticker
        self.requestID = requestID

class UpdateThresholdsCommand:
    def __init__(self, email, lowValue, highValue, requestID):
        self.email = email
        self.lowValue = lowValue
        self.highValue = highValue
        self.requestID = requestID

class DeleteUserCommand:
    def __init__(self, email):
        self.email = email