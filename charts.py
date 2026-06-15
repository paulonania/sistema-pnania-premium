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
        verde_inf = [4.0, 5.0, 6.0]
        verde_sup = [5.0, 6.0, 7.0]
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
    rotulo_perfil, _, _ = classificar_perfil(media_fases, meta.get("tipo_pista", "Pista de Treinamento"))

    plt.suptitle("ÍNDICE DE PENETRÔMETRO", fontsize=13, fontweight="bold", color="#0f3a61", y=0.98)
    plt.title(
        f"{meta['fazenda']} — {meta['pista']} — {meta['data']}\nPenetrômetro Geral: {media_fases:.1f} cm | {rotulo_perfil}",
        fontsize=10.5,
        pad=12,
        fontweight="bold",
        color="#0f3a61",
    )
    ax.legend(loc="upper left", frameon=True, facecolor="white", edgecolor="#e0e0e0", fontsize=9)

    plt.subplots_adjust(bottom=0.12, top=0.85)
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
    y_labels = []
    for val in y_ticks:
        if val == 1:
            y_labels.append("Entrada / Ponto 1")
        elif val == n_pontos:
            y_labels.append(f"Fundo / Ponto {n_pontos}")
        else:
            y_labels.append(f"Ponto {val}")
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
        verde_inf = [4.0, 5.0, 6.0]
        verde_sup = [5.0, 6.0, 7.0]

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
