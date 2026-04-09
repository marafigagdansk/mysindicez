"""
views/home.py - Painel principal do MySíndice Z
Exibe o balanço financeiro, atalhos rápidos e transações recentes.
"""

import flet as ft
import database as db

# ========================================================
# Cores do Sistema
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
    "erro_surface": "#FFEBEE",
    "aviso": "#F57F17",
    "borda": "#E0E0E0",
}

def criar_card(conteudo: ft.Control, padding=16) -> ft.Container:
    """Card padronizado para manter a consistência da UI."""
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

def formatar_brl(valor: float) -> str:
    """Formata float para R$"""
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def build_home(page: ft.Page) -> ft.Column:
    """Monta a view principal do Dashboard."""
    
    # 1. Busca os dados atuais no banco de dados SQLite
    dados_saldo = db.calcular_saldo_atual()
    saldo_atual = dados_saldo["saldo_atual"]
    total_entradas = dados_saldo["total_entradas"]
    total_saidas = dados_saldo["total_saidas"]
    saldo_inicial = dados_saldo["saldo_inicial"]

    # --- Renderização Condicional de Cor do Saldo ---
    cor_saldo = CORES["primaria"] if saldo_atual >= 0 else CORES["erro"]

    # 2. Painel Principal de Balanço Financeiro
    card_balanco = criar_card(
        ft.Column(
            [
                # Título Principal
                ft.Row(
                    [
                        ft.Icon(ft.Icons.ACCOUNT_BALANCE_WALLET, size=28, color=CORES["primaria_light"]),
                        ft.Text("Saldo Atual", size=16, color=CORES["texto_secundario"], weight=ft.FontWeight.W_500),
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                    spacing=8,
                ),
                # Valor Central
                ft.Text(
                    formatar_brl(saldo_atual),
                    size=36,
                    weight=ft.FontWeight.BOLD,
                    color=cor_saldo,
                ),
                
                ft.Divider(height=20, color=CORES["borda"]),
                
                # Totalizadores de Entradas e Saidas Lado a Lado
                ft.Row(
                    [
                        ft.Column(
                            [
                                ft.Row([
                                    ft.Icon(ft.Icons.ARROW_CIRCLE_UP, color=CORES["sucesso"], size=16),
                                    ft.Text("Receitas (Mês)", size=12, color=CORES["texto_secundario"]),
                                ], spacing=4),
                                ft.Text(formatar_brl(total_entradas), size=16, weight=ft.FontWeight.W_600, color=CORES["sucesso"]),
                            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, expand=True
                        ),
                        ft.Container(width=1, height=40, bgcolor=CORES["borda"]),
                        ft.Column(
                            [
                                ft.Row([
                                    ft.Icon(ft.Icons.ARROW_CIRCLE_DOWN, color=CORES["erro"], size=16),
                                    ft.Text("Despesas (Mês)", size=12, color=CORES["texto_secundario"]),
                                ], spacing=4),
                                ft.Text(formatar_brl(total_saidas), size=16, weight=ft.FontWeight.W_600, color=CORES["erro"]),
                            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, expand=True
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_EVENLY,
                ),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=8,
        ),
        padding=24,
    )

    # 3. Alerta sobre a Configuração Inicial
    alerta_config = ft.Container()
    if saldo_inicial == 0 and total_entradas == 0 and total_saidas == 0:
        def ir_para_configuracao(e):
            from main import carregar_view_externa
            carregar_view_externa(page, "configuracao")
            
        alerta_config = criar_card(
            ft.Column(
                [
                    ft.Icon(ft.Icons.NEW_RELEASES, color=CORES["aviso"], size=32),
                    ft.Text(
                        "Configure o Saldo Inicial do condomínio para relatórios precisos.",
                        size=13, color=CORES["texto_secundario"], text_align=ft.TextAlign.CENTER
                    ),
                    ft.FilledButton(
                        content="Configurar Agora",
                        icon=ft.Icons.SETTINGS,
                        on_click=ir_para_configuracao,
                        bgcolor=CORES["primaria_surface"],
                        color=CORES["primaria"],
                    )
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=8
            )
        )

    # 4. Micro-Histórico de Transações Recentes
    todas_transacoes = db.listar_transacoes()
    ultimas_transacoes = todas_transacoes[:5]  # Pega até os 5 últimos

    conteudo_historico = ft.Column(spacing=8)

    if not ultimas_transacoes:
        conteudo_historico.controls.append(
            ft.Container(
                content=ft.Column(
                    [
                        ft.Icon(ft.Icons.RECEIPT_LONG_OUTLINED, size=40, color=CORES["borda"]),
                        ft.Text("Nenhuma movimentação registrada.", size=13, color=CORES["texto_secundario"]),
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=6
                ),
                padding=24,
                alignment=ft.Alignment.CENTER
            )
        )
    else:
        for t in ultimas_transacoes:
            eh_entrada = t["tipo"] == "entrada"
            cor_icon = CORES["sucesso"] if eh_entrada else CORES["erro"]
            icone = ft.Icons.ARROW_CIRCLE_UP if eh_entrada else ft.Icons.ARROW_CIRCLE_DOWN

            # Subtítulo (Data e Descrição)
            descricao = t["descricao"] or "Transferência genérica"
            
            card_mini = ft.Container(
                content=ft.Row(
                    [
                        ft.Icon(icone, color=cor_icon, size=24),
                        ft.Column(
                            [
                                ft.Text(descricao, size=14, weight=ft.FontWeight.W_600, color=CORES["texto"], overflow=ft.TextOverflow.ELLIPSIS),
                                ft.Text(t["data"], size=11, color=CORES["texto_secundario"]),
                            ],
                            spacing=1,
                            expand=True,
                        ),
                        ft.Text(
                            ("+" if eh_entrada else "-") + " " + formatar_brl(t["valor"]),
                            size=14,
                            weight=ft.FontWeight.BOLD,
                            color=cor_icon,
                        ),
                    ],
                    spacing=8,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                padding=12,
                border_radius=8,
                bgcolor=CORES["fundo"],
            )
            conteudo_historico.controls.append(card_mini)

    sessao_historico = criar_card(
        ft.Column(
            [
                ft.Row(
                    [
                        ft.Icon(ft.Icons.HISTORY, color=CORES["secundaria"]),
                        ft.Text("Atividade Recente", size=15, weight=ft.FontWeight.W_600, color=CORES["texto"]),
                    ],
                    spacing=8,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                ft.Divider(height=8, color=CORES["borda"]),
                conteudo_historico
            ],
            spacing=8
        ),
        padding=16
    )

    # 5. Agrupamento Final para a Página
    layout_final = ft.Column(
        controls=[
            card_balanco,
            alerta_config if alerta_config.content else ft.Container(height=0),
            ft.Container(height=8),
            sessao_historico,
            ft.Container(height=80),  # Padding pro botton nav limit
        ],
        spacing=12,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        scroll=ft.ScrollMode.AUTO,
        expand=True,
    )

    return layout_final
