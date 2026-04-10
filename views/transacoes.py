"""
views/transacoes.py - Tela de Entradas e Saídas
Gerencia os registros financeiros, associação a moradores e anexo de comprovantes.
"""

import flet as ft
import database as db
import os
import shutil
import time
from datetime import datetime


# ========================================================
# Cores
# ========================================================
CORES = {
    "primaria": "#1B5E20",
    "primaria_light": "#388E3C",
    "primaria_surface": "#E8F5E9",
    "secundaria": "#0D47A1",
    "secundaria_surface": "#E3F2FD",
    "fundo": "#F5F5F5",
    "card": "#FFFFFF",
    "texto": "#212121",
    "texto_secundario": "#757575",
    "sucesso": "#2E7D32",
    "erro": "#C62828",
    "erro_surface": "#FFEBEE",
    "aviso": "#F57F17",
    "borda": "#E0E0E0",
}


def criar_card(conteudo: ft.Control, padding=16) -> ft.Container:
    """Card estilizado com sombra."""
    return ft.Container(
        content=conteudo,
        padding=padding,
        border_radius=12,
        bgcolor=CORES["card"],
        shadow=ft.BoxShadow(
            spread_radius=0,
            blur_radius=8,
            color=ft.Colors.with_opacity(0.08, ft.Colors.BLACK),
            offset=ft.Offset(0, 2),
        ),
        border=ft.Border.all(1, CORES["borda"]),
    )


# Dir base
DB_DIR = os.path.dirname(os.path.abspath(db.__file__))
COMPROVANTES_DIR = os.path.join(DB_DIR, "comprovantes")


def formatar_brl(valor: float) -> str:
    """Formata um float para o padrão brasileiro R$ 1.234,56"""
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def limpar_valor(texto: str) -> float:
    """Converte string em float aceito pelo banco."""
    limpo = texto.replace("R$", "").replace(".", "").replace(",", ".").strip()
    return float(limpo) if limpo else 0.0


def build_transacoes(page: ft.Page) -> ft.Column:
    # Garante que a pasta existe
    if not os.path.exists(COMPROVANTES_DIR):
        os.makedirs(COMPROVANTES_DIR)

    # --- Controles do Formulário ---
    campo_tipo = ft.Dropdown(
        label="Sinal / Tipo",
        options=[
            ft.dropdown.Option("entrada_mensalidade", "Mensalidade (Receita)"),
            ft.dropdown.Option("entrada", "Outras Entradas (Receitas)"),
            ft.dropdown.Option("saida", "Saída (Despesas)"),
        ],
        border_radius=10,
        border_color=CORES["borda"],
        focused_border_color=CORES["primaria_light"],
        expand=True,
    )

    campo_valor = ft.TextField(
        label="Valor",
        prefix=ft.Text("R$ "),
        hint_text="0,00",
        keyboard_type=ft.KeyboardType.NUMBER,
        border_radius=10,
        border_color=CORES["borda"],
        focused_border_color=CORES["primaria_light"],
        expand=True,
    )

    campo_descricao = ft.TextField(
        label="Descrição",
        hint_text="Ex: Mensalidade, Manutenção",
        border_radius=10,
        border_color=CORES["borda"],
        focused_border_color=CORES["primaria_light"],
        expand=True,
    )

    def formatar_mascara_data(e):
        texto = e.control.value
        # Filtra deixando apenas os dígitos numéricos
        somente_numeros = "".join(filter(str.isdigit, texto))
        
        if len(somente_numeros) > 8:
            somente_numeros = somente_numeros[:8]
            
        mascarado = ""
        if len(somente_numeros) > 0:
            mascarado = somente_numeros[:2]
        if len(somente_numeros) > 2:
            mascarado += "/" + somente_numeros[2:4]
        if len(somente_numeros) > 4:
            mascarado += "/" + somente_numeros[4:]
            
        e.control.value = mascarado
        page.update()

    # Hoje por padrão formatado no padrão brasileiro
    hoje_str = datetime.now().strftime("%d/%m/%Y")
    
    campo_data = ft.TextField(
        label="Data (DD/MM/AAAA)",
        value=hoje_str,
        keyboard_type=ft.KeyboardType.NUMBER,
        on_change=formatar_mascara_data,
        border_radius=10,
        border_color=CORES["borda"],
        focused_border_color=CORES["primaria_light"],
        expand=True,
    )

    # Dropdown de Moradores (preenchido na carga local)
    campo_morador = ft.Dropdown(
        label="Vincular a um Morador (Opcional)",
        options=[],
        border_radius=10,
        border_color=CORES["borda"],
        focused_border_color=CORES["primaria_light"],
        expand=True,
        visible=False,
    )

    # Variável interna para guardar o caminho original do arquivo SE selecionado
    caminho_comprovante_selecionado = [None]  # Usamos uma lista para mutabilidade interna

    texto_comprovante = ft.Text("Nenhum arquivo selecionado.", size=12, color=CORES["texto_secundario"], expand=True)

    def on_pick_click(e):
        import tkinter as tk
        from tkinter import filedialog
        
        root = tk.Tk()
        root.attributes("-topmost", True)
        root.withdraw()
        
        caminho = filedialog.askopenfilename(
            title="Selecione o Comprovante",
            filetypes=[("Arquivos Permitidos", "*.pdf *.png *.jpg *.jpeg")]
        )
        root.destroy()

        if caminho:
            caminho_comprovante_selecionado[0] = caminho
            texto_comprovante.value = f"Anexado: {os.path.basename(caminho)}"
            texto_comprovante.color = CORES["sucesso"]
        else:
            caminho_comprovante_selecionado[0] = None
            texto_comprovante.value = "Nenhum arquivo selecionado."
            texto_comprovante.color = CORES["texto_secundario"]
        
        page.update()

    btn_anexar = ft.OutlinedButton(
        content="Anexar Comprovante",
        icon=ft.Icons.ATTACH_FILE,
        on_click=on_pick_click,
        style=ft.ButtonStyle(
            shape=ft.RoundedRectangleBorder(radius=10),
            padding=ft.Padding(left=12, right=12, top=10, bottom=10),
        ),
    )

    lista_transacoes = ft.Column(spacing=8)

    # Função para adaptar a UI de acordo com o tipo
    def on_tipo_change(e):
        if campo_tipo.value == "entrada_mensalidade":
            campo_morador.visible = True
            campo_morador.label = "Vincular a um Morador (Obrigatório)"
            if not campo_descricao.value:
                campo_descricao.value = "Mensalidade"
        elif campo_tipo.value == "entrada":
            campo_morador.visible = True
            campo_morador.label = "Vincular a um Morador (Opcional)"
        else:
            campo_morador.visible = False
            
        page.update()
    
    campo_tipo.on_change = on_tipo_change

    def carregar_dropdown_moradores():
        campo_morador.options.clear()
        campo_morador.options.append(ft.dropdown.Option("", "Sem vínculo"))
        for m in db.listar_moradores():
            campo_morador.options.append(ft.dropdown.Option(str(m["id"]), f"{m['nome']} ({m['unidade']})"))

    def carregar_lista():
        lista_transacoes.controls.clear()
        transacoes = db.listar_transacoes()

        if not transacoes:
            lista_transacoes.controls.append(
                ft.Container(
                    content=ft.Column([
                        ft.Icon(ft.Icons.RECEIPT_LONG_OUTLINED, size=48, color=CORES["borda"]),
                        ft.Text(
                            "Nenhuma transação encontrada.",
                            size=14,
                            color=CORES["texto_secundario"],
                            text_align=ft.TextAlign.CENTER,
                        ),
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=8),
                    alignment=ft.Alignment.CENTER,
                    padding=32,
                )
            )
            return

        for t in transacoes:
            eh_entrada = t["tipo"] == "entrada"
            cor_card = CORES["primaria_surface"] if eh_entrada else CORES["erro_surface"]
            cor_icon = CORES["primaria"] if eh_entrada else CORES["erro"]
            icone = ft.Icons.ARROW_CIRCLE_UP if eh_entrada else ft.Icons.ARROW_CIRCLE_DOWN

            def excluir_click(e, tid=t["id"]):
                def confirmar(ex):
                    db.excluir_transacao(tid)
                    dlg.open = False
                    snack = ft.SnackBar(content=ft.Text("Transação excluída."), bgcolor=CORES["sucesso"])
                    snack.open = True
                    page.overlay.append(snack)
                    carregar_lista()
                    page.update()

                def cancelar(cx):
                    dlg.open = False
                    page.update()

                dlg = ft.AlertDialog(
                    modal=True,
                    title=ft.Text("Excluir Transação"),
                    content=ft.Text("Tem certeza que deseja excluir esta transação?"),
                    actions=[
                        ft.TextButton(content="Cancelar", on_click=cancelar),
                        ft.FilledButton(
                            content="Excluir",
                            on_click=confirmar,
                            bgcolor=CORES["erro"],
                            color=ft.Colors.WHITE,
                        ),
                    ],
                    actions_alignment=ft.MainAxisAlignment.END,
                )
                dlg.open = True
                page.overlay.append(dlg)
                page.update()

            def abrir_comprovante(e, path=t["comprovante_path"]):
                if path and os.path.exists(path):
                    # Tenta abrir o arquivo usando o sistema operacional
                    try:
                        os.startfile(path)
                    except AttributeError:
                        # Em sistemas diferentes de Windows
                        import subprocess
                        subprocess.call(["open", path] if os.name == "mac" else ["xdg-open", path])
                else:
                    snack = ft.SnackBar(content=ft.Text("Arquivo não encontrado no diretório."), bgcolor=CORES["erro"])
                    snack.open = True
                    page.overlay.append(snack)
                    page.update()

            botoes_acao = []
            if t["comprovante_path"]:
                botoes_acao.append(
                    ft.IconButton(
                        icon=ft.Icons.ATTACH_FILE,
                        icon_color=CORES["secundaria"],
                        tooltip="Ver Comprovante",
                        on_click=abrir_comprovante,
                    )
                )
            
            botoes_acao.append(
                ft.IconButton(
                    icon=ft.Icons.DELETE_OUTLINE,
                    icon_color=CORES["erro"],
                    tooltip="Excluir",
                    on_click=excluir_click,
                )
            )

            # Converte YYYY-MM-DD para DD/MM/YYYY para exibição
            try:
                a, m, d = t["data"].split("-")
                data_exibicao = f"{d}/{m}/{a}"
            except:
                data_exibicao = t["data"]

            # Subtítulo (Data e Morador se houver)
            sub_partes = [data_exibicao]
            if t["morador_nome"]:
                sub_partes.append(f"{t['morador_nome']} (Un. {t['morador_unidade']})")

            card = ft.Container(
                content=ft.Row(
                    [
                        ft.Icon(icone, color=cor_icon, size=32),
                        ft.Column(
                            [
                                ft.Text(
                                    t["descricao"] or "Sem descrição",
                                    size=15,
                                    weight=ft.FontWeight.W_600,
                                    color=CORES["texto"],
                                    overflow=ft.TextOverflow.ELLIPSIS,
                                ),
                                ft.Text(
                                    " | ".join(sub_partes),
                                    size=12,
                                    color=CORES["texto_secundario"],
                                ),
                            ],
                            spacing=2,
                            expand=True,
                        ),
                        ft.Text(
                            formatar_brl(t["valor"]),
                            size=15,
                            weight=ft.FontWeight.BOLD,
                            color=cor_icon,
                        ),
                        ft.Row(botoes_acao, spacing=0),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=8,
                ),
                padding=ft.Padding(left=12, right=4, top=10, bottom=10),
                border_radius=10,
                bgcolor=CORES["card"],
                border=ft.Border(left=ft.BorderSide(6, cor_icon)),
                shadow=ft.BoxShadow(blur_radius=4, color=ft.Colors.with_opacity(0.04, ft.Colors.BLACK), offset=ft.Offset(0, 1)),
            )
            lista_transacoes.controls.append(card)

    def salvar_transacao(e):
        tipo_raw = campo_tipo.value
        tipo_banco = "entrada" if tipo_raw and tipo_raw.startswith("entrada") else "saida"

        texto_valor = (campo_valor.value or "").strip()
        descricao = (campo_descricao.value or "").strip()
        data_str = (campo_data.value or "").strip()
        morador_id = None

        if tipo_banco == "entrada" and campo_morador.value:
            morador_id = int(campo_morador.value)

        tem_erro = False
        campo_tipo.error_text = None
        campo_valor.error_text = None
        campo_morador.error_text = None

        if not tipo_raw:
            campo_tipo.error_text = "Selecione o tipo."
            tem_erro = True
            
        if tipo_raw == "entrada_mensalidade" and not campo_morador.value:
            campo_morador.error_text = "Morador obrigatório."
            campo_morador.visible = True
            tem_erro = True
        
        try:
            valor = limpar_valor(texto_valor)
            if valor <= 0:
                raise ValueError("Valor inválido")
        except ValueError:
            campo_valor.error_text = "Digite um valor válido."
            tem_erro = True
        
        if tem_erro:
            page.update()
            return

        # Converte de DD/MM/YYYY para YYYY-MM-DD antes de botar no banco
        import re
        if re.match(r"^\d{2}/\d{2}/\d{4}$", data_str):
            dia, mes, ano = data_str.split("/")
            data_db = f"{ano}-{mes}-{dia}"
        else:
            campo_data.error_text = "Data inválida. Use DD/MM/AAAA."
            page.update()
            return

        # Lidando com a cópia do comprovante
        caminho_final = None
        if caminho_comprovante_selecionado[0]:
            caminho_origem = caminho_comprovante_selecionado[0]
            if os.path.exists(caminho_origem):
                ext = os.path.splitext(caminho_origem)[1]
                bname = os.path.splitext(os.path.basename(caminho_origem))[0]
                nome_novo = f"{int(time.time())}_{bname[:10]}{ext}"
                caminho_final = os.path.join(COMPROVANTES_DIR, nome_novo)
                try:
                    shutil.copy2(caminho_origem, caminho_final)
                except Exception as ex:
                    snack = ft.SnackBar(content=ft.Text(f"Erro ao copiar anexo: {ex}"), bgcolor=CORES["erro"])
                    snack.open = True
                    page.overlay.append(snack)
                    caminho_final = None  # Reseta para salvar a transacao sem path quebrado em caso de erro no shutil

        db.inserir_transacao(
            tipo=tipo_banco,
            valor=valor,
            descricao=descricao,
            data=data_db,
            morador_id=morador_id,
            comprovante_path=caminho_final
        )

        snack = ft.SnackBar(content=ft.Text("Transação salva com sucesso!"), bgcolor=CORES["sucesso"])
        snack.open = True
        page.overlay.append(snack)

        # Limpa form
        campo_valor.value = ""
        campo_descricao.value = ""
        campo_morador.value = None
        caminho_comprovante_selecionado[0] = None
        texto_comprovante.value = "Nenhum arquivo selecionado."
        texto_comprovante.color = CORES["texto_secundario"]
        fechar_painel()
        carregar_lista()
        page.update()


    # Botões e Painel expansível (estilo manual como em moradores)
    btn_salvar = ft.FilledButton(
        content="Salvar Registro",
        icon=ft.Icons.SAVE,
        on_click=salvar_transacao,
        style=ft.ButtonStyle(
            bgcolor=CORES["primaria"],
            color=ft.Colors.WHITE,
            shape=ft.RoundedRectangleBorder(radius=10),
            padding=ft.Padding(left=20, right=20, top=14, bottom=14),
        ),
        expand=True,
    )

    def cancelar_form(e):    
        campo_valor.value = ""
        campo_descricao.value = ""
        campo_valor.error_text = None
        fechar_painel()

    btn_cancelar = ft.OutlinedButton(
        content="Cancelar",
        icon=ft.Icons.CLOSE,
        on_click=cancelar_form,
        style=ft.ButtonStyle(
            side=ft.BorderSide(color=CORES["borda"], width=1),
            shape=ft.RoundedRectangleBorder(radius=10),
            padding=ft.Padding(left=16, right=16, top=14, bottom=14),
        ),
    )

    icone_expansao = ft.Icon(ft.Icons.KEYBOARD_ARROW_DOWN, color=CORES["secundaria"])

    container_campos = ft.Container(
        content=ft.Column(
            [
                ft.Row([campo_tipo, campo_valor], spacing=8),
                campo_descricao,
                campo_data,
                campo_morador,
                ft.Container(height=4),
                # Bloco do comprovante
                ft.Container(
                    content=ft.Row(
                        [btn_anexar, texto_comprovante],
                        spacing=12,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    padding=ft.Padding(top=8, bottom=8, left=0, right=0),
                ),
                ft.Container(height=8),
                ft.Row([btn_cancelar, btn_salvar], spacing=8),
            ],
            spacing=12,
        ),
        padding=ft.Padding(left=16, right=16, top=8, bottom=16),
        visible=False,
    )

    def toggle_painel(e=None):
        container_campos.visible = not container_campos.visible
        icone_expansao.name = ft.Icons.KEYBOARD_ARROW_UP if container_campos.visible else ft.Icons.KEYBOARD_ARROW_DOWN
        page.update()

    def fechar_painel():
        container_campos.visible = False
        icone_expansao.name = ft.Icons.KEYBOARD_ARROW_DOWN
        page.update()

    painel_formulario = criar_card(
        ft.Column(
            [
                ft.ListTile(
                    leading=ft.Icon(ft.Icons.ADD_CIRCLE_OUTLINE, color=CORES["secundaria"]),
                    title=ft.Text("Novo Lançamento", weight=ft.FontWeight.W_600, color=CORES["texto"]),
                    subtitle=ft.Text("Toque para registrar uma entrada ou saída", color=CORES["texto_secundario"], size=12),
                    trailing=icone_expansao,
                    on_click=toggle_painel,
                ),
                container_campos,
            ],
            spacing=0,
        ),
        padding=0
    )

    carregar_dropdown_moradores()
    carregar_lista()

    # View final
    return ft.Column(
        controls=[
            # Resumo Card (pega do DB o saldo/total)
            criar_card(
                ft.Row(
                    [
                        ft.Icon(ft.Icons.SWAP_HORIZ, size=28, color=CORES["primaria"]),
                        ft.Column(
                            [
                                ft.Text("Gestão Financeira", size=16, weight=ft.FontWeight.BOLD, color=CORES["texto"]),
                                ft.Text("Controle de entradas e saídas", size=13, color=CORES["texto_secundario"], weight=ft.FontWeight.W_500),
                            ],
                            spacing=2,
                            expand=True,
                        ),
                    ],
                    spacing=12,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                padding=ft.Padding(left=16, right=16, top=12, bottom=12),
            ),

            painel_formulario,

            ft.Container(height=4),
            ft.Text("Histórico Recente", size=14, weight=ft.FontWeight.W_600, color=CORES["texto"]),

            lista_transacoes,
            ft.Container(height=80),
        ],
        spacing=8,
        scroll=ft.ScrollMode.AUTO,
        expand=True,
    )
