"""
main.py - Aplicativo MySíndice Z
Gestão condominial mobile-first com Flet + SQLite.
"""

import flet as ft
from database import inicializar_banco
from views.moradores import build_moradores
from views.configuracao import build_configuracao


# ========================================================
# Cores e Tema do App
# ========================================================

# Paleta de cores personalizada
CORES = {
    "primaria": "#1B5E20",        # Verde escuro (confiança)
    "primaria_light": "#388E3C",  # Verde médio
    "primaria_surface": "#E8F5E9", # Verde bem claro (fundo de cards)
    "secundaria": "#0D47A1",      # Azul escuro
    "secundaria_light": "#1976D2", # Azul médio
    "fundo": "#F5F5F5",           # Cinza claro (fundo geral)
    "card": "#FFFFFF",            # Branco (cards)
    "texto": "#212121",           # Texto principal
    "texto_secundario": "#757575", # Texto secundário
    "sucesso": "#2E7D32",         # Verde (entradas)
    "erro": "#C62828",            # Vermelho (saídas)
    "aviso": "#F57F17",           # Amarelo (alertas)
    "borda": "#E0E0E0",           # Cinza (bordas)
    "nav_bg": "#FFFFFF",          # Fundo da navbar
}


# ========================================================
# Componentes Reutilizáveis
# ========================================================
def criar_appbar(page: ft.Page, titulo: str) -> ft.AppBar:
    """Cria a AppBar padrão do app com menu lateral dinâmico feito nativamente."""
    return ft.AppBar(
        title=ft.Text(
            titulo,
            size=20,
            weight=ft.FontWeight.BOLD,
            color=ft.Colors.WHITE,
        ),
        center_title=True,
        bgcolor=CORES["primaria"],
        color=ft.Colors.WHITE,
    )

def criar_card(conteudo: ft.Control, padding: int = 16) -> ft.Container:
    """Cria um card estilizado com sombra e bordas arredondadas."""
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


# ========================================================
# Views (Telas)
# ========================================================

from views.home import build_home

def view_home(page: ft.Page) -> ft.Column:
    """Dashboard principal (Home) — Passo 5."""
    # Passamos lambda anonima limpa para não ter conflito de imports
    return build_home(page, on_config_click=lambda: carregar_view_externa(page, "configuracao"))


from views.transacoes import build_transacoes

def view_transacoes(page: ft.Page) -> ft.Column:
    """Tela de Entradas e Saídas (Transações) — Passo 4."""
    return build_transacoes(page)


def view_moradores(page: ft.Page) -> ft.Column:
    """Tela de Moradores — usa a view real do Passo 3."""
    return build_moradores(page)


from views.relatorios import build_relatorios

def view_relatorios(page: ft.Page) -> ft.Column:
    """Tela de Relatórios PDF — Passo 6."""
    return build_relatorios(page)



def view_configuracao(page: ft.Page) -> ft.Column:
    """Tela de Configuração de Saldo Inicial — usa a view real do Passo 3."""
    return build_configuracao(page)


# ========================================================
# App Principal
# ========================================================

# Referência global ao conteúdo e appbar (necessária para o atalho da Home)
_conteudo_ref = None
_appbar_ref = None
_page_ref = None


def carregar_view_externa(page, nome: str):
    """Permite que views internas naveguem para outras telas (ex: Home -> Configuracao)."""
    global _conteudo_ref
    mapa = {
        "configuracao": ("Configuracao", view_configuracao),
    }
    if nome in mapa and _conteudo_ref:
        titulo, view_func = mapa[nome]
        page.appbar = criar_appbar(page, titulo)
        _conteudo_ref.content = view_func(page)
        page.update()

def main(page: ft.Page):
    """Função principal do app Flet."""

    def mostrar_erro_critico(erro: str):
        """Exibe uma tela de erro amigável em caso de falha catastrófica."""
        page.clean()
        page.add(
            ft.Container(
                content=ft.Column(
                    [
                        ft.Icon(ft.Icons.ERROR_OUTLINE, color=CORES["erro"], size=64),
                        ft.Text("Erro ao inicializar o App", size=24, weight=ft.FontWeight.BOLD, color=CORES["texto"]),
                        ft.Text(
                            "Ocorreu um problema ao carregar os dados ou permissões do sistema.",
                            text_align=ft.TextAlign.CENTER,
                            color=CORES["texto_secundario"]
                        ),
                        ft.Container(
                            content=ft.Text(f"Detalhes: {erro}", size=11, color=CORES["erro"], font_family="monospace"),
                            padding=15,
                            bgcolor=ft.Colors.GREY_100,
                            border_radius=8,
                        ),
                        ft.FilledButton(
                            "Tentar Novamente", 
                            icon=ft.Icons.REFRESH,
                            on_click=lambda _: page.window_destroy() if hasattr(page, "window_destroy") else None
                        )
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=20,
                ),
                alignment=ft.Alignment.CENTER,
                expand=True,
                padding=40,
            )
        )
        page.update()

    try:
        # --- Configuração da página (simulação mobile no PC + System UI Android) ---
        page.title = "MySíndice Z"
        
        # Só define tamanho se for desktop para não interferir no mobile
        if page.platform not in [ft.PagePlatform.ANDROID, ft.PagePlatform.IOS]:
            page.window.width = 400
            page.window.height = 800
            page.window.resizable = True
        
        page.bgcolor = CORES["fundo"]
        page.padding = 0
        
        # Configuração para que a NavigationBar do app conviva com a do sistema Android
        page.theme = ft.Theme(
            system_overlay_style=ft.SystemOverlayStyle(
                system_navigation_bar_color=ft.Colors.TRANSPARENT,
                system_navigation_bar_divider_color=ft.Colors.TRANSPARENT,
            ),
        )

        # Inicializa o banco de dados
        global _conteudo_ref
        inicializar_banco()

        # --- Container principal que exibirá a view ativa ---
        conteudo_principal = ft.Container(
            expand=True,
            padding=ft.Padding(left=16, right=16, top=8, bottom=8),
        )
        _conteudo_ref = conteudo_principal

        # --- Mapeamento de índice para views ---
        def carregar_view(indice: int):
            """Carrega a view correspondente ao índice da NavigationBar."""
            views = {
                0: ("Home", view_home),
                1: ("Entradas / Saídas", view_transacoes),
                2: ("Moradores", view_moradores),
                3: ("Relatórios", view_relatorios),
            }
            titulo, view_func = views.get(indice, ("Home", view_home))
            page.appbar = criar_appbar(page, titulo)
            conteudo_principal.content = view_func(page)
            page.update()

        # --- NavigationBar inferior ---
        def on_nav_change(e):
            """Callback de troca de aba na barra de navegação."""
            carregar_view(e.control.selected_index)
            
        nav_bar = ft.NavigationBar(
            selected_index=0,
            on_change=on_nav_change,
            bgcolor=ft.Colors.with_opacity(0.92, CORES["nav_bg"]), 
            indicator_color=CORES["primaria_surface"],
            elevation=0, 
            adaptive=True,
            label_behavior=ft.NavigationBarLabelBehavior.ALWAYS_SHOW,
            destinations=[
                ft.NavigationBarDestination(
                    icon=ft.Icons.HOME_OUTLINED,
                    selected_icon=ft.Icons.HOME,
                    label="Home",
                ),
                ft.NavigationBarDestination(
                    icon=ft.Icons.SWAP_HORIZ_OUTLINED,
                    selected_icon=ft.Icons.SWAP_HORIZ,
                    label="Transações",
                ),
                ft.NavigationBarDestination(
                    icon=ft.Icons.PEOPLE_OUTLINE,
                    selected_icon=ft.Icons.PEOPLE,
                    label="Moradores",
                ),
                ft.NavigationBarDestination(
                    icon=ft.Icons.DESCRIPTION_OUTLINED,
                    selected_icon=ft.Icons.DESCRIPTION,
                    label="Relatórios",
                ),
            ],
        )

        # --- Navigation Drawer Lateral ---
        def on_drawer_change(e):
            e.control.selected_index = None
            carregar_view_externa(page, "configuracao")
            page.drawer.open = False
            page.update()

        page.drawer = ft.NavigationDrawer(
            on_change=on_drawer_change,
            controls=[
                ft.Container(height=12),
                ft.NavigationDrawerDestination(
                    label="Configurações",
                    icon=ft.Icons.SETTINGS_OUTLINED,
                    selected_icon=ft.Icons.SETTINGS,
                ),
            ]
        )

        # --- Layout inicial ---
        page.appbar = criar_appbar(page, "Home")
        conteudo_principal.content = view_home(page)
        page.navigation_bar = nav_bar

        page.add(conteudo_principal)
        page.update()

    except Exception as ex:
        mostrar_erro_critico(str(ex))


# Inicializa o app Flet como Aplicativo Nativo / Web
if __name__ == "__main__":
    ft.app(target=main)
