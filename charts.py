import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from scipy.interpolate import griddata
from analysis import classificar_espessura, classificar_penetro, classificar_umidade, classificar_perfil, calcular_io


def fig_penetrometro(df, meta, stats):
    fases = ["Impacto", "Suporte", "Tração"]
    tipo_pista = meta.get("tipo_pista", "Pista de Treinamento")
    if tipo_pista == "Pista de Competição":
        verde_inf = [3.0, 4.0, 5.0]
        verde_sup = [4.0, 5.0, 6.0]
    else:
        verde_inf = [3.0, 5.0, 7.0]
        verde_sup = [5.0, 7.0, 9.0]
    medicao_atual = stats["medicao_atual"]

    max_valor = max(df["1ª Queda"].max(), df["2ª Queda"].max(), df["3ª Queda"].max())
    limite_y = float(max(10.0, np.ceil(max_valor + 1.5)))

    fig, ax = plt.subplots(figsize=(9, 5.0))
    ax.set_facecolor("#f4f4f6")
    x_indices = np.arange(len(fases))

    ax.fill_between(x_indices, verde_inf, verde_sup, color="#e2f0d9", alpha=0.7, label="Alvo")
    ax.plot(x_indices, verde_sup, color="#a9d08e", linestyle="--", linewidth=1.2)
    ax.plot(x_indices, verde_inf, color="#a9d08e", linestyle="--", linewidth=1.2)
    ax.plot(
        x_indices,
        medicao_atual,
        color="#0f3a61",
        linewidth=3.5,
        marker="s",
        markersize=12,
        markerfacecolor="white",
        markeredgewidth=3,
        label="Medição",
    )

    for i, valor in enumerate(medicao_atual):
        ax.annotate(
            f"{valor:.1f}",
            (x_indices[i], medicao_atual[i]),
            textcoords="offset points",
            xytext=(0, 14),
            ha="center",
            fontweight="bold",
            fontsize=11,
            color="#0f3a61",
        )

    ax.set_ylim(0, limite_y)
    ax.set_ylabel("Profundidade (cm)", fontsize=10, fontweight="bold", color="#555555")
    ax.set_xticks(x_indices)
    ax.set_xticklabels(fases, fontsize=10, fontweight="bold")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.grid(axis="y", linestyle=":", alpha=0.5, color="#cccccc")

    media_fases = sum(stats["medicao_atual"]) / 3
    rotulo_perfil, _, desc_perfil = classificar_perfil(media_fases, meta.get("tipo_pista", "Pista de Treinamento"))

    pista = meta.get("pista", "")
    data = meta.get("data", "")
    fazenda = meta.get("fazenda", "")

    title_line1 = f"Índice do Penetrômetro - {fazenda}" if fazenda else "Índice do Penetrômetro"
    title_line2 = f"{pista} | {data} | {rotulo_perfil}"
    if desc_perfil:
        title_line2 += f" | {desc_perfil}"

    title_str = f"{title_line1}\n{title_line2}"

    plt.title(
        title_str,
        fontsize=11,
        pad=15,
        fontweight="bold",
        color="#0f3a61",
    )
    ax.legend(loc="upper left", frameon=True, facecolor="white", edgecolor="#e0e0e0", fontsize=9)

    plt.subplots_adjust(bottom=0.12, top=0.90)
    return fig


def _fig_mapa(df, coluna, titulo, label_barra, n_linhas, n_pontos):
    xi, yi = np.meshgrid(
        np.linspace(1, n_linhas, 100),
        np.linspace(1, n_pontos, 100),
    )
    zi = griddata((df["X"], df["Y"]), df[coluna], (xi, yi), method="cubic")

    fig, ax = plt.subplots(figsize=(7, 4.2))
    mapa = ax.imshow(zi, extent=[1, n_linhas, 1, n_pontos], origin="lower", cmap="turbo", aspect="auto")
    ax.set_title(titulo, fontsize=11, fontweight="bold", color="#0f3a61", pad=12)
    
    y_ticks = list(range(1, n_pontos + 1))
    ax.set_yticks(y_ticks)
    y_labels = [f"Ponto {val}" for val in y_ticks]
    ax.set_yticklabels(y_labels, fontsize=9, fontweight="bold")

    x_ticks = list(range(1, n_linhas + 1))
    ax.set_xticks(x_ticks)
    x_labels = [f"Linha {val}" for val in x_ticks]
    ax.set_xticklabels(x_labels, fontsize=9, fontweight="bold")

    fig.colorbar(mapa, ax=ax).set_label(label_barra, fontweight="bold")
    return fig


def fig_mapa_espessura(df, n_linhas, n_pontos):
    return _fig_mapa(df, "Espessura", "MAPA DE ESPESSURA DA PISTA", "Espessura (cm)", n_linhas, n_pontos)


def fig_mapa_umidade(df, n_linhas, n_pontos):
    return _fig_mapa(df, "Umidade", "MAPA DE UMIDADE DA PISTA", "Umidade (%)", n_linhas, n_pontos)


def fig_mapa_penetrometro(df, n_linhas, n_pontos):
    df = df.copy()
    # Média das 3 quedas
    df["Media_Penetrometro"] = (df["1ª Queda"] + df["2ª Queda"] + df["3ª Queda"]) / 3
    
    xi, yi = np.meshgrid(
        np.linspace(1, n_linhas, 100),
        np.linspace(1, n_pontos, 100),
    )
    zi = griddata((df["X"], df["Y"]), df["Media_Penetrometro"], (xi, yi), method="cubic")

    fig, ax = plt.subplots(figsize=(7, 4.2))
    mapa = ax.imshow(zi, extent=[1, n_linhas, 1, n_pontos], origin="lower", cmap="turbo", aspect="auto", vmin=1.0, vmax=11.0)
    ax.set_title("MAPA DO ÍNDICE DO PENETRÔMETRO (MÉDIA)", fontsize=11, fontweight="bold", color="#0f3a61", pad=12)
    
    y_ticks = list(range(1, n_pontos + 1))
    ax.set_yticks(y_ticks)
    y_labels = [f"Ponto {val}" for val in y_ticks]
    ax.set_yticklabels(y_labels, fontsize=9, fontweight="bold")

    x_ticks = list(range(1, n_linhas + 1))
    ax.set_xticks(x_ticks)
    x_labels = [f"Linha {val}" for val in x_ticks]
    ax.set_xticklabels(x_labels, fontsize=9, fontweight="bold")

    cbar = fig.colorbar(mapa, ax=ax)
    cbar.set_label("Penetração (cm) | Classificação", fontweight="bold")
    
    # Tick positions at class centers
    cbar_ticks = [2.0, 3.5, 4.5, 5.75, 7.25, 8.5, 10.0]
    cbar.set_ticks(cbar_ticks)
    cbar.set_ticklabels([
        "Muito Dura (<3.0)",
        "Dura (3.0-4.0)",
        "Firme 1 (4.0-5.0)",
        "Firme 2 (5.0-6.5)",
        "Macia 1 (6.5-8.0)",
        "Macia 2 (8.0-9.0)",
        "Pesada (>=9.0)"
    ])
    
    # Anotações de texto dentro do mapa de calor em cada ponto levantado
    for _, row in df.iterrows():
        x = row["X"]
        y = row["Y"]
        media_pt = row["Media_Penetrometro"]
        
        # Determina a classificação
        if media_pt < 3.0:
            lbl = "Muito Dura"
        elif media_pt < 4.0:
            lbl = "Dura"
        elif media_pt < 5.0:
            lbl = "Firme 1"
        elif media_pt < 6.5:
            lbl = "Firme 2"
        elif media_pt < 8.0:
            lbl = "Macia 1"
        elif media_pt < 9.0:
            lbl = "Macia 2"
        else:
            lbl = "Pesada"
            
        # Adiciona o texto no gráfico com caixa branca semitransparente para legibilidade
        ax.text(
            x, y, lbl,
            color="#222222",
            fontsize=7,
            fontweight="bold",
            ha="center",
            va="center",
            bbox=dict(boxstyle="round,pad=0.15", facecolor="white", edgecolor="none", alpha=0.65)
        )
        
    return fig



def fig_comparativa(historico_dados, meta=None):
    fases = ["Impacto", "Suporte", "Tração"]
    
    tipo_pista = "Pista de Treinamento"
    if meta is not None:
        tipo_pista = meta.get("tipo_pista", "Pista de Treinamento")
    elif historico_dados:
        tipo_pista = historico_dados[0].get("meta", {}).get("tipo_pista", "Pista de Treinamento")
        
    if tipo_pista == "Pista de Competição":
        verde_inf = [3.0, 4.0, 5.0]
        verde_sup = [4.0, 5.0, 6.0]
    else:
        verde_inf = [3.0, 5.0, 7.0]
        verde_sup = [5.0, 7.0, 9.0]

    max_valor = 10.0
    for item in historico_dados:
        max_valor = max(max_valor, max(item["stats"]["medicao_atual"]))
    limite_y = float(max(10.0, np.ceil(max_valor + 1.5)))

    fig, ax = plt.subplots(figsize=(9, 5.0))
    ax.set_facecolor("#f4f4f6")
    x_indices = np.arange(len(fases))

    # Zona de Alvo no fundo
    ax.fill_between(x_indices, verde_inf, verde_sup, color="#e2f0d9", alpha=0.7, label="Alvo")
    ax.plot(x_indices, verde_sup, color="#a9d08e", linestyle="--", linewidth=1.2)
    ax.plot(x_indices, verde_inf, color="#a9d08e", linestyle="--", linewidth=1.2)

    # Plotar cada medição
    for item in historico_dados:
        meta = item["meta"]
        stats = item["stats"]
        medicao_atual = stats["medicao_atual"]
        label_curva = f"Medição ({meta['data']})"
        ax.plot(
            x_indices,
            medicao_atual,
            linewidth=2.5,
            marker="o",
            markersize=8,
            label=label_curva,
        )
        
        # Adicionar anotações
        for i, val in enumerate(medicao_atual):
            ax.annotate(
                f"{val:.1f}",
                (x_indices[i], medicao_atual[i]),
                textcoords="offset points",
                xytext=(0, 10),
                ha="center",
                fontweight="bold",
                fontsize=9,
            )

    ax.set_ylim(0, limite_y)
    ax.set_ylabel("Profundidade (cm)", fontsize=10, fontweight="bold", color="#555555")
    ax.set_xticks(x_indices)
    ax.set_xticklabels(fases, fontsize=10, fontweight="bold")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.grid(axis="y", linestyle=":", alpha=0.5, color="#cccccc")

    plt.suptitle("COMPARATIVO HISTÓRICO DE PENETROMETRIA", fontsize=13, fontweight="bold", color="#0f3a61", y=0.98)
    ax.legend(loc="upper left", frameon=True, facecolor="white", edgecolor="#e0e0e0", fontsize=9)

    plt.subplots_adjust(bottom=0.12, top=0.88)
    return fig
