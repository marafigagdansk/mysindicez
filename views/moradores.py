"""
views/moradores.py - Tela de Cadastro e Listagem de Moradores
"""

import flet as ft
import database as db


# ========================================================
# Cores (importadas do tema central)
# ========================================================
CORES = {
    "primaria": "#1B5E20",
    "primaria_light": "#388E3C",
    "primaria_surface": "#E8F5E9",
    "secundaria": "#0D47A1",
    "fundo": "#F5F5F5",
    "card": "#FFFFFF",
    "texto": "#212121",
    "texto_secundario": "#757575",
    "sucesso": "#2E7D32",
    "erro": "#C62828",
    "aviso": "#F57F17",
    "borda": "#E0E0E0",
}


# ========================================================
# Componentes auxiliares
# ========================================================

def criar_card(conteudo: ft.Control, padding: int = 16) -> ft.Container:
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


def criar_snackbar(page: ft.Page, mensagem: str, erro: bool = False):
    """Exibe um SnackBar de feedback ao usuário."""
    snack = ft.SnackBar(
        content=ft.Text(mensagem, color=ft.Colors.WHITE),
        bgcolor=CORES["erro"] if erro else CORES["sucesso"],
        duration=3000,
    )
    snack.open = True
    page.overlay.append(snack)
    page.update()


# ========================================================
# View Principal de Moradores
# ========================================================

def build_moradores(page: ft.Page) -> ft.Column:
    """
    Constrói a view completa de Moradores:
    - Formulário de cadastro (expansível)
    - Lista de moradores cadastrados
    - Ações de editar e desativar
    """

    # --- Referências dos campos do formulário ---
    campo_nome = ft.TextField(
        label="Nome completo",
        prefix_icon=ft.Icons.PERSON,
        border_radius=10,
        border_color=CORES["borda"],
        focused_border_color=CORES["primaria_light"],
        expand=True,
        capitalization=ft.TextCapitalization.WORDS,
    )

    campo_unidade = ft.TextField(
        label="Apartamento / Unidade",
        prefix_icon=ft.Icons.DOOR_BACK_DOOR,
        hint_text="Ex: 101, Bloco A - 203",
        border_radius=10,
        border_color=CORES["borda"],
        focused_border_color=CORES["primaria_light"],
        expand=True,
        capitalization=ft.TextCapitalization.CHARACTERS,
    )

    # Controla se estamos em modo de edição
    modo_edicao = {"ativo": False, "id": None}

    # Container da lista de moradores (atualizado dinamicamente)
    lista_moradores = ft.Column(spacing=8)

    # --- Função para carregar/recarregar a lista ---
    def carregar_lista():
        """Busca os moradores no banco e reconstrói a lista visual."""
        lista_moradores.controls.clear()
        moradores = db.listar_moradores()

        if not moradores:
            lista_moradores.controls.append(
                ft.Container(
                    content=ft.Column([
                        ft.Icon(ft.Icons.PEOPLE_OUTLINE, size=48, color=CORES["borda"]),
                        ft.Text(
                            "Nenhum morador cadastrado.",
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

        for m in moradores:
            def on_editar(e, morador=m):
                """Preenche o formulário para editar o morador."""
                campo_nome.value = morador["nome"]
                campo_unidade.value = morador["unidade"]
                modo_edicao["ativo"] = True
                modo_edicao["id"] = morador["id"]
                btn_salvar.text = "Salvar Alteracoes"
                btn_salvar.icon = ft.Icons.SAVE
                abrir_painel()

            def on_desativar(e, morador=m):
                """Solicita confirmação antes de desativar o morador."""
                def confirmar(e):
                    db.desativar_morador(morador["id"])
                    dlg.open = False
                    carregar_lista()
                    criar_snackbar(page, f"Morador '{morador['nome']}' removido.")
                    page.update()

                def cancelar(e):
                    dlg.open = False
                    page.update()

                dlg = ft.AlertDialog(
                    modal=True,
                    title=ft.Text("Remover Morador"),
                    content=ft.Text(
                        f"Deseja remover '{morador['nome']}' (Unidade {morador['unidade']})?\n"
                        "O histórico de pagamentos será mantido."
                    ),
                    actions=[
                        ft.TextButton(text="Cancelar", on_click=cancelar),
                        ft.FilledButton(
                            text="Remover",
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

            # Card individual do morador
            card = criar_card(
                ft.Row(
                    [
                        # Avatar com inicial do nome
                        ft.Container(
                            content=ft.Text(
                                m["nome"][0].upper(),
                                size=18,
                                weight=ft.FontWeight.BOLD,
                                color=ft.Colors.WHITE,
                            ),
                            width=44,
                            height=44,
                            border_radius=22,
                            bgcolor=CORES["primaria_light"],
                            alignment=ft.Alignment.CENTER,
                        ),
                        # Nome e unidade
                        ft.Column(
                            [
                                ft.Text(
                                    m["nome"],
                                    size=15,
                                    weight=ft.FontWeight.W_600,
                                    color=CORES["texto"],
                                    overflow=ft.TextOverflow.ELLIPSIS,
                                ),
                                ft.Text(
                                    f"Unidade: {m['unidade']}",
                                    size=13,
                                    color=CORES["texto_secundario"],
                                ),
                            ],
                            spacing=2,
                            expand=True,
                        ),
                        # Botões de ação
                        ft.IconButton(
                            icon=ft.Icons.EDIT_OUTLINED,
                            icon_color=CORES["secundaria"],
                            tooltip="Editar",
                            on_click=on_editar,
                        ),
                        ft.IconButton(
                            icon=ft.Icons.DELETE_OUTLINE,
                            icon_color=CORES["erro"],
                            tooltip="Remover",
                            on_click=on_desativar,
                        ),
                    ],
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=8,
                ),
                padding=ft.Padding(left=12, right=4, top=10, bottom=10),
            )
            lista_moradores.controls.append(card)

    # --- Ação do botão Salvar ---
    def salvar_morador(e):
        """Valida e salva (inserção ou edição) o morador."""
        nome = (campo_nome.value or "").strip()
        unidade = (campo_unidade.value or "").strip()

        # Validação básica
        campo_nome.error_text = None
        campo_unidade.error_text = None
        tem_erro = False

        if not nome:
            campo_nome.error_text = "Informe o nome do morador."
            tem_erro = True
        if not unidade:
            campo_unidade.error_text = "Informe a unidade."
            tem_erro = True

        if tem_erro:
            page.update()
            return

        if modo_edicao["ativo"]:
            db.atualizar_morador(modo_edicao["id"], nome, unidade)
            criar_snackbar(page, "Morador atualizado com sucesso!")
        else:
            db.inserir_morador(nome, unidade)
            criar_snackbar(page, "Morador cadastrado com sucesso!")

        # Limpa o formulário e recarrega lista
        campo_nome.value = ""
        campo_unidade.value = ""
        modo_edicao["ativo"] = False
        modo_edicao["id"] = None
        btn_salvar.text = "Cadastrar Morador"
        btn_salvar.icon = ft.Icons.PERSON_ADD
        fechar_painel()

        carregar_lista()

    def cancelar_edicao(e):
        """Cancela o modo de edição e limpa o formulário."""
        campo_nome.value = ""
        campo_unidade.value = ""
        campo_nome.error_text = None
        campo_unidade.error_text = None
        modo_edicao["ativo"] = False
        modo_edicao["id"] = None
        btn_salvar.text = "Cadastrar Morador"
        btn_salvar.icon = ft.Icons.PERSON_ADD
        fechar_painel()

    # --- Botões do formulário ---
    btn_salvar = ft.FilledButton(
        text="Cadastrar Morador",
        icon=ft.Icons.PERSON_ADD,
        on_click=salvar_morador,
        style=ft.ButtonStyle(
            bgcolor=CORES["primaria"],
            color=ft.Colors.WHITE,
            shape=ft.RoundedRectangleBorder(radius=10),
            padding=ft.Padding(left=20, right=20, top=14, bottom=14),
        ),
        expand=True,
    )

    btn_cancelar = ft.OutlinedButton(
        text="Cancelar",
        icon=ft.Icons.CLOSE,
        on_click=cancelar_edicao,
        style=ft.ButtonStyle(
            side=ft.BorderSide(color=CORES["borda"], width=1),
            shape=ft.RoundedRectangleBorder(radius=10),
            padding=ft.Padding(left=16, right=16, top=14, bottom=14),
        ),
    )

    # --- Painel manual expansível do formulário ---
    icone_expansao = ft.Icon(ft.Icons.KEYBOARD_ARROW_DOWN, color=CORES["secundaria"])

    container_campos = ft.Container(
        content=ft.Column(
            [
                campo_nome,
                campo_unidade,
                ft.Container(height=4),
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

    def abrir_painel():
        container_campos.visible = True
        icone_expansao.name = ft.Icons.KEYBOARD_ARROW_UP
        page.update()

    def fechar_painel():
        container_campos.visible = False
        icone_expansao.name = ft.Icons.KEYBOARD_ARROW_DOWN
        page.update()

    painel_formulario = criar_card(
        ft.Column(
            [
                ft.ListTile(
                    leading=ft.Icon(ft.Icons.PERSON_ADD, color=CORES["primaria"]),
                    title=ft.Text("Novo Morador", weight=ft.FontWeight.W_600, color=CORES["texto"]),
                    subtitle=ft.Text("Toque para expandir e cadastrar", color=CORES["texto_secundario"], size=12),
                    trailing=icone_expansao,
                    on_click=toggle_painel,
                ),
                container_campos,
            ],
            spacing=0,
        ),
        padding=0
    )

    # Carrega a lista inicial
    carregar_lista()

    # --- Contador de moradores ---
    def get_contador():
        qtd = len(db.listar_moradores())
        return ft.Text(
            f"{qtd} morador{'es' if qtd != 1 else ''} cadastrado{'s' if qtd != 1 else ''}",
            size=13,
            color=CORES["texto_secundario"],
            weight=ft.FontWeight.W_500,
        )

    texto_contador = get_contador()

    # Agrupa tudo na view final
    return ft.Column(
        controls=[
            # Cabeçalho da seção
            criar_card(
                ft.Row(
                    [
                        ft.Icon(ft.Icons.PEOPLE, size=28, color=CORES["primaria"]),
                        ft.Column(
                            [
                                ft.Text("Moradores", size=16, weight=ft.FontWeight.BOLD, color=CORES["texto"]),
                                texto_contador,
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

            # Painel de cadastro (manual)
            painel_formulario,

            ft.Container(height=4),

            # Título da lista
            ft.Text("Moradores Cadastrados", size=14, weight=ft.FontWeight.W_600, color=CORES["texto"]),

            # Lista dinâmica
            lista_moradores,

            ft.Container(height=80),  # Espaço para a NavigationBar não cobrir o conteúdo
        ],
        spacing=8,
        scroll=ft.ScrollMode.AUTO,
        expand=True,
    )
