"""
relatorios.py - Gerador de Relatórios PDF mensais
Utiliza fpdf2 para criar um relatório financeiro profissional.
"""

import os
from datetime import datetime
from fpdf import FPDF

# Pasta onde os PDFs serão salvos
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RELATORIOS_DIR = os.path.join(BASE_DIR, "relatorios")

# Mapeamento de meses em português
MESES_PT = {
    1: "Janeiro", 2: "Fevereiro", 3: "Março", 4: "Abril",
    5: "Maio", 6: "Junho", 7: "Julho", 8: "Agosto",
    9: "Setembro", 10: "Outubro", 11: "Novembro", 12: "Dezembro",
}


def formatar_brl(valor: float) -> str:
    """Formata float para padrão R$ brasileiro."""
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


class RelatorioPDF(FPDF):
    """Classe customizada com cabeçalho e rodapé padronizados."""

    def __init__(self, mes: int, ano: int, nome_condominio: str = "Condomínio"):
        super().__init__(orientation="P", unit="mm", format="A4")
        self.mes = mes
        self.ano = ano
        self.nome_condominio = nome_condominio
        self.set_auto_page_break(auto=True, margin=20)
        # Usa Arial do Windows com suporte a Unicode (pt-BR)
        FONTS_W = "C:/Windows/Fonts"
        self.add_font("Arial", style="", fname=f"{FONTS_W}/arial.ttf", uni=True)
        self.add_font("Arial", style="B", fname=f"{FONTS_W}/arialbd.ttf", uni=True)
        self.add_font("Arial", style="I", fname=f"{FONTS_W}/ariali.ttf", uni=True)
        self.add_page()

    def header(self):
        """Cabeçalho de cada página."""
        # Barra verde de topo
        self.set_fill_color(27, 94, 32)  # Verde escuro (#1B5E20)
        self.rect(0, 0, 210, 18, "F")

        # Título do condomínio
        self.set_text_color(255, 255, 255)
        self.set_font("Arial", "B", 13)
        self.set_y(4)
        self.cell(0, 6, self.nome_condominio, align="L", new_x="LMARGIN", new_y="NEXT")

        # Subtítulo do relatório
        self.set_font("Arial", "", 9)
        self.cell(0, 4, f"Relatorio Financeiro - {MESES_PT[self.mes]}/{self.ano}", align="L")

        # Restaura cores
        self.set_text_color(33, 33, 33)
        self.ln(12)

    def footer(self):
        """Rodapé com número de página e data de emissão."""
        self.set_y(-12)
        self.set_font("Arial", "I", 8)
        self.set_text_color(117, 117, 117)
        gerado_em = datetime.now().strftime("%d/%m/%Y às %H:%M")
        self.cell(0, 5, f"Gerado em {gerado_em}  |  Página {self.page_no()}", align="C")

    def _linha_horizontal(self, cor=(224, 224, 224)):
        """Desenha uma linha horizontal separadora."""
        self.set_draw_color(*cor)
        self.line(self.get_x(), self.get_y(), 200, self.get_y())
        self.ln(2)

    def secao_resumo(self, saldo_inicial: float, total_entradas: float,
                      total_saidas: float, saldo_mes: float):
        """Seção de resumo financeiro do mês com cards de métricas."""
        self.set_font("Arial", "B", 12)
        self.set_text_color(27, 94, 32)
        self.cell(0, 8, "Resumo Financeiro do Mês", new_x="LMARGIN", new_y="NEXT")
        self._linha_horizontal((27, 94, 32))
        self.ln(2)

        # 4 colunas de métricas
        col_w = 45
        itens = [
            ("Saldo Inicial", saldo_inicial, (13, 71, 161)),    # Azul
            ("Total Entradas", total_entradas, (46, 125, 50)),  # Verde
            ("Total Saídas", total_saidas, (198, 40, 40)),      # Vermelho
            ("Saldo do Mês", saldo_mes, (46, 125, 50) if saldo_mes >= 0 else (198, 40, 40)),
        ]

        y_start = self.get_y()
        for i, (label, valor, cor_rgb) in enumerate(itens):
            x = 10 + i * (col_w + 2)
            # Caixa cinza-clara
            self.set_fill_color(245, 245, 245)
            self.set_draw_color(224, 224, 224)
            self.rect(x, y_start, col_w, 20, "FD")
            # Label
            self.set_xy(x + 2, y_start + 2)
            self.set_font("Arial", "", 8)
            self.set_text_color(117, 117, 117)
            self.cell(col_w - 4, 5, label, align="C")
            # Valor
            self.set_xy(x + 2, y_start + 8)
            self.set_font("Arial", "B", 10)
            self.set_text_color(*cor_rgb)
            self.cell(col_w - 4, 7, formatar_brl(valor), align="C")

        self.set_y(y_start + 25)
        self.set_text_color(33, 33, 33)
        self.ln(4)

    def secao_transacoes(self, titulo: str, transacoes: list, cor_header: tuple):
        """Renderiza uma tabela de transações (entradas ou saidas)."""
        if not transacoes:
            return

        self.set_font("Arial", "B", 11)
        self.set_text_color(*cor_header)
        self.cell(0, 8, titulo, new_x="LMARGIN", new_y="NEXT")
        self._linha_horizontal(cor_header)
        self.ln(1)

        # Cabeçalho da tabela
        col_widths = [28, 77, 55, 30]  # Data | Descrição | Morador | Valor
        headers = ["Data", "Descrição", "Morador / Unidade", "Valor"]

        self.set_fill_color(238, 238, 238)
        self.set_text_color(33, 33, 33)
        self.set_font("Arial", "B", 9)

        self.cell(col_widths[0], 7, headers[0], border=0, fill=True, align="L")
        self.cell(col_widths[1], 7, headers[1], border=0, fill=True, align="L")
        self.cell(col_widths[2], 7, headers[2], border=0, fill=True, align="L")
        self.cell(col_widths[3], 7, headers[3], border=0, fill=True, align="R")
        self.ln()
        self._linha_horizontal()

        self.set_font("Arial", "", 9)
        fill = False
        for t in transacoes:
            # Converte YYYY-MM-DD para DD/MM/YYYY
            try:
                a, m, d = t["data"].split("-")
                data_fmt = f"{d}/{m}/{a}"
            except:
                data_fmt = t["data"]
            descricao = (t["descricao"] or "-")[:40]
            morador = ""
            if t.get("morador_nome"):
                morador = f"{t['morador_nome']} (Un.{t['morador_unidade']})"
            morador = morador[:30] if morador else "-"
            valor_fmt = formatar_brl(t["valor"])

            # Backgroud alternado
            self.set_fill_color(249, 249, 249) if fill else self.set_fill_color(255, 255, 255)
            self.set_text_color(33, 33, 33)

            self.cell(col_widths[0], 7, data_fmt, border=0, fill=fill, align="L")
            self.cell(col_widths[1], 7, descricao, border=0, fill=fill, align="L")
            self.cell(col_widths[2], 7, morador, border=0, fill=fill, align="L")
            self.set_text_color(*cor_header)
            self.cell(col_widths[3], 7, valor_fmt, border=0, fill=fill, align="R")
            self.set_text_color(33, 33, 33)
            self.ln()
            fill = not fill

        # Linha total
        self.set_font("Arial", "B", 9)
        self.set_fill_color(238, 238, 238)
        total = sum(t["valor"] for t in transacoes)
        total_label_w = col_widths[0] + col_widths[1] + col_widths[2]
        self.cell(total_label_w, 7, f"Total ({len(transacoes)} lançamento{'s' if len(transacoes) != 1 else ''})", fill=True, align="R")
        self.set_text_color(*cor_header)
        self.cell(col_widths[3], 7, formatar_brl(total), fill=True, align="R")
        self.set_text_color(33, 33, 33)
        self.ln(10)


def gerar_relatorio_mensal(resumo: dict, saldo_inicial: float,
                            nome_condominio: str = "Condomínio") -> str:
    """
    Gera o PDF do relatório mensal e retorna o caminho do arquivo gerado.
    
    Args:
        resumo: dict retornado por db.resumo_mensal(mes, ano)
        saldo_inicial: valor do saldo inicial configurado
        nome_condominio: nome do condomínio para o cabeçalho
    
    Returns:
        Caminho absoluto do PDF gerado.
    """
    # Garante que a pasta de relatórios existe
    if not os.path.exists(RELATORIOS_DIR):
        os.makedirs(RELATORIOS_DIR)

    mes = resumo["mes"]
    ano = resumo["ano"]

    pdf = RelatorioPDF(mes, ano, nome_condominio)

    # Seção de Resumo Financeiro
    pdf.secao_resumo(
        saldo_inicial=saldo_inicial,
        total_entradas=resumo["total_entradas"],
        total_saidas=resumo["total_saidas"],
        saldo_mes=resumo["saldo_mes"],
    )

    # Seção de Entradas
    pdf.secao_transacoes(
        titulo="Entradas (Receitas)",
        transacoes=resumo.get("entradas", []),
        cor_header=(46, 125, 50),  # verde
    )

    # Seção de Saídas
    pdf.secao_transacoes(
        titulo="Saídas (Despesas)",
        transacoes=resumo.get("saidas", []),
        cor_header=(198, 40, 40),  # vermelho
    )

    # Observação final se não houve movimentação
    if not resumo.get("entradas") and not resumo.get("saidas"):
        pdf.set_font("Arial", "I", 11)
        pdf.set_text_color(117, 117, 117)
        pdf.cell(0, 10, "Nenhuma movimentação registrada neste período.", align="C")

    # Nome do arquivo: relatorio_MM_YYYY.pdf
    nome_arquivo = f"relatorio_{mes:02d}_{ano}.pdf"
    caminho = os.path.join(RELATORIOS_DIR, nome_arquivo)
    pdf.output(caminho)

    return caminho
