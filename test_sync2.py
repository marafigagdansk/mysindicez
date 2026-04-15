import os
import sys

# Redireciona stderr
with open("flet_error.log", "w") as f:
    sys.stderr = f
    
    import flet as ft
    import views.transacoes
    import database as db

    db.inicializar_banco()
    
    # Criar 2 transacao dummy pra renderizar o Historico!
    db.inserir_transacao("entrada", 10.0, "teste", "2026-05-05")

    def main(page: ft.Page):
        view = views.transacoes.build_transacoes(page)
        page.add(view)
        page.window_close()

    ft.run(main)
