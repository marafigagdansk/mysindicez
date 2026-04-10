"""
views/relatorios.py - Tela de Geração de Relatórios PDF
Permite ao síndico selecionar mês/ano e exportar o relatório financeiro.
"""

import flet as ft
import database as db
import relatorios as rel_gen
import os
from datetime import datetime

# ========================================================
# Cores do Sistema
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

MESES_PT = {
    1: "Janeiro", 2: "Fevereiro", 3: "Março", 4: "Abril",
    5: "Maio", 6: "Junho", 7: "Julho", 8: "Agosto",
    9: "Setembro", 10: "Outubro", 11: "Novembro", 12: "Dezembro",
}


def criar_card(conteudo: ft.Control, padding=16) -> ft.Container:
    """Card padronizado da UI."""
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
    """Exibe feedback rápido ao usuário."""
    snack = ft.SnackBar(
        content=ft.Text(mensagem, color=ft.Colors.WHITE),
        bgcolor=CORES["erro"] if erro else CORES["sucesso"],
    )
    snack.open = True
    page.overlay.append(snack)
    page.update()


def build_relatorios(page: ft.Page) -> ft.Column:
    """Monta a view de geração de relatórios PDF."""

    agora = datetime.now()

    # --- Seletores de Mês e Ano ---
    dd_mes = ft.Dropdown(
        label="Mês",
        options=[ft.dropdown.Option(str(m), MESES_PT[m]) for m in range(1, 13)],
        value=str(agora.month),
        border_radius=10,
        border_color=CORES["borda"],
        focused_border_color=CORES["primaria_light"],
        expand=True,
    )

    dd_ano = ft.Dropdown(
        label="Ano",
        options=[ft.dropdown.Option(str(a)) for a in range(agora.year - 3, agora.year + 1)],
        value=str(agora.year),
        border_radius=10,
        border_color=CORES["borda"],
        focused_border_color=CORES["primaria_light"],
        expand=True,
    )

    # Container do preview de dados (atualizado dinamicamente)
    preview_container = ft.Column(spacing=8)

    # Status da geração
    status_texto = ft.Text("", size=13, color=CORES["texto_secundario"])

    def atualizar_preview(e=None):
        """Atualiza os totais do mês selecionado em realtime."""
        mes = int(dd_mes.value) if dd_mes.value else agora.month
        ano = int(dd_ano.value) if dd_ano.value else agora.year
        resumo = db.resumo_mensal(mes, ano)

        preview_container.controls.clear()

        # Caixas de métricas
        def metrica(label, valor, cor):
            return ft.Container(
                content=ft.Column(
                    [
                        ft.Text(label, size=11, color=CORES["texto_secundario"]),
                        ft.Text(valor, size=17, weight=ft.FontWeight.BOLD, color=cor),
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=2,
                ),
                expand=True,
                bgcolor=CORES["fundo"],
                border_radius=8,
                padding=10,
            )

        def fmt(v):
            return f"R$ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

        preview_container.controls.append(
            ft.Row(
                [
                    metrica("Entradas", fmt(resumo["total_entradas"]), CORES["sucesso"]),
                    metrica("Saídas", fmt(resumo["total_saidas"]), CORES["erro"]),
                    metrica("Saldo do mês", fmt(resumo["saldo_mes"]),
                            CORES["sucesso"] if resumo["saldo_mes"] >= 0 else CORES["erro"]),
                ],
                spacing=8,
            )
        )

        total_lanc = len(resumo["entradas"]) + len(resumo["saidas"])
        preview_container.controls.append(
            ft.Text(
                f"{total_lanc} lançamento{'s' if total_lanc != 1 else ''} registrado{'s' if total_lanc != 1 else ''} neste mês.",
                size=12,
                color=CORES["texto_secundario"],
                italic=True,
            )
        )
        page.update()

    dd_mes.on_change = atualizar_preview
    dd_ano.on_change = atualizar_preview

    # --- Lista de PDFs gerados anteriormente ---
    lista_pdfs = ft.Column(spacing=6)

    def atualizar_lista_pdfs():
        """Varre a pasta de relatórios e lista os PDFs existentes."""
        lista_pdfs.controls.clear()
        pasta = rel_gen.RELATORIOS_DIR

        if not os.path.exists(pasta):
            lista_pdfs.controls.append(
                ft.Text("Nenhum relatório gerado ainda.", size=12, color=CORES["texto_secundario"], italic=True)
            )
            page.update()
            return

        arquivos = sorted(
            [f for f in os.listdir(pasta) if f.endswith(".pdf")],
            reverse=True
        )

        if not arquivos:
            lista_pdfs.controls.append(
                ft.Text("Nenhum relatório gerado ainda.", size=12, color=CORES["texto_secundario"], italic=True)
            )
            page.update()
            return

        for nome_f in arquivos:
            caminho_f = os.path.join(pasta, nome_f)

            def abrir_pdf(e, path=caminho_f):
                try:
                    os.startfile(path)
                except Exception as ex:
                    criar_snackbar(page, f"Não foi possível abrir: {ex}", erro=True)

            # Extrai mês/ano do nome do arquivo: relatorio_MM_YYYY.pdf
            try:
                partes = nome_f.replace("relatorio_", "").replace(".pdf", "").split("_")
                m, a = int(partes[0]), int(partes[1])
                rotulo = f"{MESES_PT[m]}/{a}"
            except Exception:
                rotulo = nome_f

            item = ft.Container(
                content=ft.Row(
                    [
                        ft.Icon(ft.Icons.PICTURE_AS_PDF, color=CORES["erro"], size=22),
                        ft.Text(rotulo, size=14, color=CORES["texto"], expand=True, weight=ft.FontWeight.W_500),
                        ft.IconButton(
                            icon=ft.Icons.OPEN_IN_NEW,
                            icon_color=CORES["secundaria"],
                            tooltip="Abrir PDF",
                            on_click=abrir_pdf,
                        ),
                    ],
                    spacing=8,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                bgcolor=CORES["fundo"],
                border_radius=8,
                padding=ft.Padding(left=12, right=4, top=8, bottom=8),
            )
            lista_pdfs.controls.append(item)

        page.update()

    def gerar_pdf(e):
        """Gera o PDF do mês selecionado."""
        mes = int(dd_mes.value) if dd_mes.value else agora.month
        ano = int(dd_ano.value) if dd_ano.value else agora.year

        try:
            resumo = db.resumo_mensal(mes, ano)
            saldo_inicial = float(db.obter_configuracao("saldo_inicial", "0"))
            nome_cond = db.obter_configuracao("nome_condominio", "Meu Condomínio")

            caminho = rel_gen.gerar_relatorio_mensal(resumo, saldo_inicial, nome_cond)
            status_texto.value = f"✅ PDF gerado: {os.path.basename(caminho)}"
            status_texto.color = CORES["sucesso"]

            # Abre o PDF automaticamente
            try:
                os.startfile(caminho)
            except Exception:
                pass

            atualizar_lista_pdfs()

        except Exception as ex:
            status_texto.value = f"❌ Erro ao gerar PDF: {ex}"
            status_texto.color = CORES["erro"]

        page.update()

    btn_gerar = ft.FilledButton(
        content="Gerar Relatório PDF",
        icon=ft.Icons.PICTURE_AS_PDF,
        on_click=gerar_pdf,
        style=ft.ButtonStyle(
            bgcolor=CORES["primaria"],
            color=ft.Colors.WHITE,
            shape=ft.RoundedRectangleBorder(radius=10),
            padding=ft.Padding(left=20, right=20, top=14, bottom=14),
        ),
        expand=True,
    )

    # Carrega o estado inicial
    atualizar_preview()
    atualizar_lista_pdfs()

    return ft.Column(
        controls=[
            # Cabeçalho
            criar_card(
                ft.Row(
                    [
                        ft.Icon(ft.Icons.DESCRIPTION, size=28, color=CORES["secundaria"]),
                        ft.Column(
                            [
                                ft.Text("Relatórios Mensais", size=16, weight=ft.FontWeight.BOLD, color=CORES["texto"]),
                                ft.Text("Exporte o extrato financeiro em PDF", size=13, color=CORES["texto_secundario"]),
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

            # Seletor de período
            criar_card(
                ft.Column(
                    [
                        ft.Text("Selecione o Período", size=14, weight=ft.FontWeight.W_600, color=CORES["texto"]),
                        ft.Row([dd_mes, dd_ano], spacing=12),
                        ft.Divider(height=12, color=CORES["borda"]),
                        ft.Text("Preview do Período", size=12, color=CORES["texto_secundario"], weight=ft.FontWeight.W_500),
                        preview_container,
                        ft.Container(height=4),
                        btn_gerar,
                        status_texto,
                    ],
                    spacing=10,
                )
            ),

            # Lista dos PDFs gerados
            criar_card(
                ft.Column(
                    [
                        ft.Row(
                            [
                                ft.Icon(ft.Icons.FOLDER_OPEN, color=CORES["texto_secundario"]),
                                ft.Text("Relatórios Gerados", size=14, weight=ft.FontWeight.W_600, color=CORES["texto"]),
                            ],
                            spacing=8,
                        ),
                        ft.Divider(height=8, color=CORES["borda"]),
                        lista_pdfs,
                    ],
                    spacing=8,
                )
            ),

            ft.Container(height=80),
        ],
        spacing=12,
        scroll=ft.ScrollMode.AUTO,
        expand=True,
    )
