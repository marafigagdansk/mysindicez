import flet as ft
import views.transacoes
import database as db
import traceback

def main(page: ft.Page):
    db.inicializar_banco()
    try:
        view = views.transacoes.build_transacoes(page)
        page.add(view)
        print("SUCESSO")
    except Exception as e:
        print("ERRO CAPTURADO:")
        traceback.print_exc()

ft.app(target=main)
