import flet as ft
import views.transacoes
import database as db

db.inicializar_banco()

def main(page: ft.Page):
    try:
        print("Montando transacoes...")
        view = views.transacoes.build_transacoes(page)
        page.add(view)
        print("Adicionando...")
        page.update()
        print("SUCESSO ABSOLUTO")
    except Exception as e:
        import traceback
        traceback.print_exc()

import threading
# Termina dps de 3s
threading.Timer(3.0, lambda: print("TERMINOU")).start()

ft.run(main)
