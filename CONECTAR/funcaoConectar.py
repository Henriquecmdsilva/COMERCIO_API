import sqlite3

def conectar():
    return sqlite3.connect("appComercio.db")  # banco no mesmo diretório