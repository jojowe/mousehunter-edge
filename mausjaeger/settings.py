import yaml

with open("mausjaeger/settings.yaml", "r", encoding="UTF-8") as ymlfile:
    CFG = yaml.safe_load(ymlfile)


def get_config_parameter(param: list = None) -> str:
    cfg = CFG
    for node in param:
        cfg = cfg[node]
    return cfg


def get_bot_token() -> str:
    param = ["telegram", "bot_token"]
    return get_config_parameter(param)


def get_chat_id() -> str:
    param = ["telegram", "chat_id"]
    return get_config_parameter(param)


def get_aws_access_key_id() -> str:
    param = ["aws", "access_key_id"]
    return get_config_parameter(param)


def get_aws_secret_access_key() -> str:
    param = ["aws", "secret_access_key"]
    return get_config_parameter(param)
