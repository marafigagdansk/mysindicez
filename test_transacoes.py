import flet as ft
import views.transacoes
import database as db
import traceback

class MockPage:
    def __init__(self):
        self.overlay = []
    def update(self):
        pass

db.inicializar_banco()
page = MockPage()

try:
    print("Iniciando build_transacoes")
    v = views.transacoes.build_transacoes(page)
    print("SUCESSO")
except Exception as e:
    print("ERRO CAPTURADO:")
    traceback.print_exc()

