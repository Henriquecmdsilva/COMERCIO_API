import sqlite3

def conectar():
    caminho_do_banco = r"C:\Users\994155\Documents\GitHub\APP_SQLITE\SQLiteDatabaseBrowserPortable\appComercio.db"
    return sqlite3.connect("caminho_do_banco")