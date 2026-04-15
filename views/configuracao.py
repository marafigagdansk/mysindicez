"""
views/configuracao.py - Tela de Configuração de Saldo Inicial
Acessada a partir do Dashboard quando o saldo ainda não foi definido,
ou pelo menu de configurações.
"""

import flet as ft
import database as db


# ========================================================
# Cores
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


def criar_snackbar(page: ft.Page, mensagem: str, erro: bool = False):
    """Exibe um SnackBar de feedback."""
    snack = ft.SnackBar(
        content=ft.Text(mensagem, color=ft.Colors.WHITE),
        bgcolor=CORES["erro"] if erro else CORES["sucesso"],
        duration=3000,
    )
    snack.open = True
    page.overlay.append(snack)
    page.update()


# ========================================================
# Helpers de formatação
# ========================================================

def formatar_brl(valor: float) -> str:
    """Formata um float para o padrão brasileiro R$ 1.234,56"""
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def limpar_valor(texto: str) -> float:
    """Converte string em float aceito pelo banco (ex: '1.500,00' → 1500.0)."""
    limpo = texto.replace("R$", "").replace(".", "").replace(",", ".").strip()
    return float(limpo) if limpo else 0.0


# ========================================================
# View Principal
# ========================================================

def build_configuracao(page: ft.Page, on_salvo=None) -> ft.Column:
    """
    Constrói a tela de configuração de saldo inicial.
    on_salvo: callback chamado após o saldo ser salvo (para atualizar o Dashboard).
    """

    # Valor atual salvo no banco
    saldo_atual_str = db.obter_configuracao("saldo_inicial", "0")
    saldo_atual = float(saldo_atual_str)

    # Campo de saldo
    campo_saldo = ft.TextField(
        label="Saldo Inicial em Caixa",
        prefix=ft.Text("R$ "),
        hint_text="Ex: 1500,00",
        value=f"{saldo_atual:.2f}".replace(".", ",") if saldo_atual > 0 else "",
        keyboard_type=ft.KeyboardType.NUMBER,
        border_radius=12,
        border_color=CORES["borda"],
        focused_border_color=CORES["primaria_light"],
        text_size=18,
    )

    # Texto que mostra o valor atual formatado (updated ao salvar)
    texto_saldo_atual = ft.Text(
        formatar_brl(saldo_atual),
        size=28,
        weight=ft.FontWeight.BOLD,
        color=CORES["primaria"],
        text_align=ft.TextAlign.CENTER,
    )

    status_text = ft.Text(
        "Saldo configurado" if saldo_atual > 0 else "Nenhum saldo definido",
        size=13,
        color=CORES["sucesso"] if saldo_atual > 0 else CORES["aviso"],
        text_align=ft.TextAlign.CENTER,
        weight=ft.FontWeight.W_500,
    )

    def salvar_saldo(e):
        """Valida e salva o saldo inicial no banco de dados."""
        campo_saldo.error_text = None

        texto = (campo_saldo.value or "").strip()
        if not texto:
            campo_saldo.error_text = "Informe o valor do saldo inicial."
            page.update()
            return

        try:
            valor = limpar_valor(texto)
            if valor < 0:
                raise ValueError("Valor negativo")
        except (ValueError, Exception):
            campo_saldo.error_text = "Digite um valor válido. Ex: 1500,00"
            page.update()
            return

        # Salva no banco
        db.salvar_configuracao("saldo_inicial", str(valor))

        # Atualiza os textos de exibição
        texto_saldo_atual.value = formatar_brl(valor)
        status_text.value = "Saldo configurado"
        status_text.color = CORES["sucesso"]

        criar_snackbar(page, "Saldo inicial salvo com sucesso!")

        # Chama callback externo (ex: atualizar Dashboard)
        if on_salvo:
            on_salvo(valor)

        page.update()

    btn_salvar = ft.FilledButton(
        text="Salvar Saldo",
        icon=ft.Icons.SAVE,
        on_click=salvar_saldo,
        style=ft.ButtonStyle(
            bgcolor=CORES["primaria"],
            color=ft.Colors.WHITE,
            shape=ft.RoundedRectangleBorder(radius=10),
            padding=ft.Padding(left=24, right=24, top=14, bottom=14),
        ),
        expand=True,
    )

    # Card informativo
    card_dica = criar_card(
        ft.Column(
            [
                ft.Row(
                    [
                        ft.Icon(ft.Icons.INFO_OUTLINE, color=CORES["secundaria"], size=20),
                        ft.Text("O que é o Saldo Inicial?", weight=ft.FontWeight.W_600, color=CORES["texto"], size=14),
                    ],
                    spacing=8,
                ),
                ft.Text(
                    "É o valor que já estava em caixa antes de você começar a usar o app. "
                    "Pode ser o saldo da conta bancária do condomínio ou o dinheiro em espécie.\n\n"
                    "O Saldo Atual será calculado como:\n"
                    "Saldo Inicial + Entradas − Saídas",
                    size=13,
                    color=CORES["texto_secundario"],
                ),
            ],
            spacing=8,
        ),
        padding=16,
    )

    # --------------------------------------------------------
    # Histórico de alterações (última atualização)
    # --------------------------------------------------------
    import sqlite3
    import os
    db_path = os.path.join(os.path.dirname(os.path.abspath(db.__file__)), "condominio.db")
    ultima_atualizacao = ""
    try:
        conn = sqlite3.connect(db_path)
        row = conn.execute(
            "SELECT atualizado_em FROM configuracoes WHERE chave='saldo_inicial'"
        ).fetchone()
        conn.close()
        if row:
            from datetime import datetime
            dt = datetime.fromisoformat(row[0])
            ultima_atualizacao = f"Última atualização: {dt.strftime('%d/%m/%Y às %H:%M')}"
    except Exception:
        pass

    # --------------------------------------------------------
    # Lógica estruturada para o Desbloqueio e Edição
    # --------------------------------------------------------
    campo_senha = ft.TextField(
        label="Senha",
        password=True,
        can_reveal_password=True,
        border_radius=12,
        border_color=CORES["borda"],
        focused_border_color=CORES["primaria_light"],
    )

    area_edicao = ft.Column(
        [
            ft.Text("Definir / Atualizar Saldo", size=15, weight=ft.FontWeight.W_600, color=CORES["texto"]),
            ft.Text("Digite o valor em reais (ex: 1500,00)", size=12, color=CORES["texto_secundario"]),
            ft.Container(height=4),
            campo_saldo,
            ft.Container(height=4),
            btn_salvar,
        ],
        spacing=10,
        visible=False,
    )

    area_senha = ft.Column(
        [
            ft.Text("Acesso Restrito", size=15, weight=ft.FontWeight.W_600, color=CORES["texto"]),
            ft.Text("Insira a senha mestra para modificar o saldo base.", size=12, color=CORES["texto_secundario"]),
            ft.Container(height=4),
            campo_senha,
            ft.Container(height=4),
        ],
        spacing=10
    )

    def limpar_erro_senha(e):
        campo_senha.error_text = None
        page.update()

    campo_senha.on_change = limpar_erro_senha

    def on_desbloquear(e):
        if campo_senha.value != "vini1612hjv":
            campo_senha.error_text = "Senha incorreta"
        else:
            area_senha.visible = False
            area_edicao.visible = True
        page.update()

    area_senha.controls.append(
        ft.Row([
            ft.FilledButton(
                "Desbloquear",
                icon=ft.Icons.LOCK_OPEN,
                on_click=on_desbloquear,
                style=ft.ButtonStyle(
                    bgcolor=CORES["secundaria"],
                    color=ft.Colors.WHITE,
                    shape=ft.RoundedRectangleBorder(radius=10),
                ),
                expand=True
            )
        ])
    )

    return ft.Column(
        controls=[
            # Card de saldo atual
            criar_card(
                ft.Column(
                    [
                        ft.Icon(
                            ft.Icons.ACCOUNT_BALANCE,
                            size=48,
                            color=CORES["primaria"],
                        ),
                        ft.Text(
                            "Saldo Inicial do Caixa",
                            size=14,
                            color=CORES["texto_secundario"],
                            text_align=ft.TextAlign.CENTER,
                        ),
                        texto_saldo_atual,
                        status_text,
                        ft.Text(
                            ultima_atualizacao,
                            size=11,
                            color=CORES["texto_secundario"],
                            text_align=ft.TextAlign.CENTER,
                        ) if ultima_atualizacao else ft.Container(),
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=6,
                ),
                padding=24,
            ),

            ft.Container(height=8),

            # Card do formulário de edição (Protegido por senha)
            criar_card(
                ft.Column(
                    [
                        area_senha,
                        area_edicao
                    ]
                ),
                padding=20,
            ),

            ft.Container(height=8),

            # Card informativo
            card_dica,

            ft.Container(height=80),
        ],
        spacing=8,
        scroll=ft.ScrollMode.AUTO,
        expand=True,
    )
