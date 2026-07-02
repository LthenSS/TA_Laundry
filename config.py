class Config:
    SECRET_KEY = "smartwash123"

    SQLALCHEMY_DATABASE_URI = \
        "mysql+pymysql://root:@localhost/smartwash"
    
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    WHATSAPP_API_URL = "https://api.fonnte.com/send"
    WHATSAPP_API_KEY = "RDMnrgiUFpWKxNqPwUgc"
    WHATSAPP_SENDER = "Smart Wash Laundry"