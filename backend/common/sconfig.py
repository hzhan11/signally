from pydantic_settings import BaseSettings

class Settings(BaseSettings):

    MODE            :   str = "rel"

    DB_PORT         :   int = 8001
    API_PORT        :   int = 8000
    INFO_COL_PORT   :   int = 9000
    SIGN_PRE_PORT   :   int = 9001
    LOG_PORT        :   int = 9020

    INFO_SRC_SINA   :   str = "sina"
    INFO_SRC_AKS    :   str = "aks"

settings = Settings()
