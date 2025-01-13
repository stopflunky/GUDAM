# Modelli relativi al Query

class LoginUserQuery:
    def __init__(self, email, password):
        self.email = email
        self.password = password

class GetTickerQuery:
    def __init__(self, email):
        self.email = email

class GetAveragePriceQuery:
    def __init__(self, email, days):
        self.email = email
        self.days = days

class GetThresholdsQuery:
    def __init__(self, email):
        self.email = email