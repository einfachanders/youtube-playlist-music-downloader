# import module configparser to read config/config.conf
import configparser

# function to return google dev key
def getDevKey():
    config = configparser.ConfigParser()
    config.read("config/config.conf")
    return config["GOOGLE-DEV-KEY"]["dev_key"]

if __name__ == "__main__":
    print(getDevKey())