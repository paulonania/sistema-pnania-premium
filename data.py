import io
import os
import re
import tempfile
from urllib.parse import parse_qs, urlparse

import pandas as pd

COLunas_EXPORT = {
    "1ª Queda": "1ª Queda - Impacto (cm)",
    "2ª Queda": "2ª Queda - Suporte (cm)",
    "3ª Queda": "3ª Queda - Tração (cm)",
    "Umidade": "Umidade TDR (%)",
    "Espessura": "Espessura da Camada (cm)",
}

DEFAULTS = {
    "q1": 4.0,
    "q2": 5.5,
    "q3": 7.2,
    "umi": 18.0,
    "esp": 12,
}


def meta_padrao():
    return {
        "fazenda": "Fazenda Calunga",
        "pista": "Picadeiro Coberto",
        "dimensao": "30x50m",
        "data": "06/06/2026",
        "ideal_umi": "18.0%",
        "ideal_esp": "12 cm",
        "n_linhas": 4,
        "n_pontos": 5,
        "coletou_umidade": True,
        "coletou_espessura": True,
        "global_umi": 18.0,
        "global_esp": 12,
        "notas_gerais": "",
        "notas_manejo": "",
        "notas_parecer": "",
        "passo": 0,
        "tipo_pista": "Pista de Treinamento",
    }


def criar_grade(n_linhas, n_pontos, global_umi=4.5, global_esp=12):
    linhas = []
    for linha in range(1, n_linhas + 1):
        for ponto in range(1, n_pontos + 1):
            linhas.append({
                "Linha": linha,
                "Ponto": ponto,
                "1ª Queda": DEFAULTS["q1"],
                "2ª Queda": DEFAULTS["q2"],
                "3ª Queda": DEFAULTS["q3"],
                "Umidade": global_umi,
                "Espessura": global_esp,
            })
    return pd.DataFrame(linhas)


def mesclar_grade(anterior, n_linhas, n_pontos, global_umi, global_esp):
    nova = criar_grade(n_linhas, n_pontos, global_umi, global_esp)
    if anterior is None or anterior.empty:
        return nova

    lookup = {
        (int(r["Linha"]), int(r["Ponto"])): r
        for _, r in anterior.iterrows()
    }
    for idx, row in nova.iterrows():
        chave = (int(row["Linha"]), int(row["Ponto"]))
        if chave in lookup:
            ant = lookup[chave]
            for col in ["1ª Queda", "2ª Queda", "3ª Queda", "Umidade", "Espessura"]:
                nova.at[idx, col] = ant[col]
    return nova


def obter_valor_multi_chaves(row, chaves, padrao=""):
    for c in chaves:
        val = row.get(c)
        if pd.notna(val):
            return str(val)
    return padrao


class ArquivoMemoria:
    def __init__(self, data, name):
        self._data = data
        self.name = name
        self.size = len(data)

    def seek(self, pos):
        self._pos = pos

    def read(self):
        if getattr(self, "_pos", 0):
            data = self._data[self._pos :]
            self._pos = 0
            return data
        return self._data

    def getvalue(self):
        return self._data


def _extrair_id_google(url):
    url = url.strip()
    if not url:
        raise ValueError("Cole um link do Google Drive ou Google Planilhas.")

    padroes = [
        r"docs\.google\.com/spreadsheets/d/([a-zA-Z0-9_-]+)",
        r"drive\.google\.com/file/d/([a-zA-Z0-9_-]+)",
        r"drive\.google\.com/open\?id=([a-zA-Z0-9_-]+)",
        r"drive\.google\.com/uc\?(?:export=download&)?(?:.*&)?id=([a-zA-Z0-9_-]+)",
    ]
    for padrao in padroes:
        match = re.search(padrao, url)
        if match:
            return match.group(1), "sheet" if "spreadsheets" in padrao else "file"

    parsed = urlparse(url)
    query_id = parse_qs(parsed.query).get("id", [None])[0]
    if query_id:
        return query_id, "file"

    raise ValueError("Link do Google Drive inválido. Use um link de compartilhamento do arquivo ou planilha.")


def _baixar_url(url, timeout=30):
    import urllib.error
    import urllib.request

    request = urllib.request.Request(
        url,
        headers={"User-Agent": "Mozilla/5.0"},
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            data = response.read()
            if not data:
                raise ValueError("O arquivo no Google Drive está vazio.")
            if b"<!DOCTYPE html" in data[:200].lower() or b"<html" in data[:200].lower():
                raise ValueError(
                    "Não foi possível baixar o arquivo. Compartilhe como "
                    "'Qualquer pessoa com o link' e tente novamente."
                )
            return data
    except urllib.error.HTTPError as exc:
        if exc.code in (401, 403):
            raise ValueError(
                "Acesso negado ao arquivo. No Google Drive, abra Compartilhar e escolha "
                "'Qualquer pessoa com o link'."
            ) from exc
        raise ValueError(f"Erro ao baixar do Google Drive (HTTP {exc.code}).") from exc
    except urllib.error.URLError as exc:
        raise ValueError(f"Não foi possível acessar o Google Drive: {exc.reason}") from exc


def _baixar_planilha_google(file_id):
    for formato, ext in (("csv", "csv"), ("xlsx", "xlsx")):
        url = f"https://docs.google.com/spreadsheets/d/{file_id}/export?format={formato}"
        try:
            data = _baixar_url(url)
            return data, f"planilha_google.{ext}"
        except ValueError:
            continue
    raise ValueError(
        "Não foi possível importar a planilha. Compartilhe como 'Qualquer pessoa com o link'."
    )


def _baixar_arquivo_google(file_id):
    try:
        import gdown
    except ImportError as exc:
        raise ValueError("Dependência gdown ausente. Atualize o app e tente novamente.") from exc

    url = f"https://drive.google.com/uc?id={file_id}"
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        temp_path = tmp.name

    try:
        gdown.download(url, temp_path, quiet=True)
        if not os.path.exists(temp_path) or os.path.getsize(temp_path) == 0:
            raise ValueError("Download vazio do Google Drive.")
        with open(temp_path, "rb") as handle:
            data = handle.read()
    finally:
        if os.path.exists(temp_path):
            os.unlink(temp_path)

    if b"<!DOCTYPE html" in data[:200].lower() or b"<html" in data[:200].lower():
        raise ValueError(
            "Não foi possível baixar o arquivo. Compartilhe como "
            "'Qualquer pessoa com o link' e tente novamente."
        )

    nome = f"arquivo_google_{file_id}"
    if data[:2] == b"PK":
        nome += ".xlsx"
    else:
        nome += ".csv"
    return data, nome


def baixar_do_google_drive(url):
    file_id, tipo = _extrair_id_google(url)
    if tipo == "sheet":
        data, nome = _baixar_planilha_google(file_id)
    else:
        data, nome = _baixar_arquivo_google(file_id)
    return ArquivoMemoria(data, nome)


def _ler_csv_bytes(uploaded_file):
    uploaded_file.seek(0)
    raw = uploaded_file.getvalue() if hasattr(uploaded_file, "getvalue") else uploaded_file.read()
    uploaded_file.seek(0)

    ultimo_erro = None
    for encoding in ("utf-8-sig", "utf-8", "latin-1", "cp1252"):
        try:
            df = pd.read_csv(io.BytesIO(raw), encoding=encoding)
            if df is not None and not df.empty:
                return df
            raise ValueError("O arquivo CSV está vazio.")
        except (UnicodeDecodeError, pd.errors.ParserError, ValueError) as exc:
            ultimo_erro = exc
    raise ValueError(
        "Não foi possível ler o CSV. Verifique o formato e a codificação do arquivo."
    ) from ultimo_erro


def carregar_csv(uploaded_file):
    import os
    if uploaded_file is None:
        raise ValueError("Nenhum arquivo enviado.")

    nome = getattr(uploaded_file, "name", "")
    is_excel = False
    is_csv = False

    if isinstance(uploaded_file, str):
        nome_lower = uploaded_file.lower()
    else:
        nome_lower = nome.lower()

    if nome_lower:
        if nome_lower.endswith(('.xlsx', '.xls')):
            is_excel = True
        elif nome_lower.endswith('.csv'):
            is_csv = True
        else:
            raise ValueError("Formato de arquivo não suportado. Por favor, envie apenas arquivos CSV ou Excel (.xlsx, .xls).")
    else:
        # Fallback se não houver nome de arquivo (ex: testes internos com stream de bytes)
        is_csv = True

    try:
        if is_excel:
            df = pd.read_excel(uploaded_file)
        else:
            df = _ler_csv_bytes(uploaded_file)
    except Exception as e:
        raise ValueError(
            f"Erro ao ler o arquivo. Certifique-se de que é um formato suportado (CSV ou Excel) "
            f"e de que o arquivo não esteja corrompido. Erro original: {e}"
        )

    if df is None or df.empty:
        raise ValueError("O arquivo enviado está vazio ou não pôde ser lido corretamente.")

    # Mapear os metadados
    meta = meta_padrao()
    primeira = df.iloc[0]

    meta["fazenda"] = str(primeira.get("Haras", primeira.get("Fazenda", primeira.get("fazenda", meta["fazenda"]))))
    meta["pista"] = str(primeira.get("Pista", primeira.get("Picadeiro", primeira.get("pista", meta["pista"]))))
    meta["dimensao"] = str(primeira.get("Dimensão", primeira.get("Dimensao", meta["dimensao"])))
    meta["data"] = str(primeira.get("Data", primeira.get("Data da Coleta", primeira.get("data", meta["data"]))))
    
    meta["notas_gerais"] = obter_valor_multi_chaves(primeira, ["Observações", "Observacoes", "Notas Gerais", "observações", "observacoes"])
    meta["notas_manejo"] = obter_valor_multi_chaves(primeira, ["Manejo Recomendado", "Manejo", "manejo recomendado", "manejo"])
    meta["notas_parecer"] = obter_valor_multi_chaves(primeira, ["Parecer Técnico", "Parecer", "Parecer tecnico", "parecer técnico", "parecer tecnico", "parecer"])
    meta["passo"] = int(primeira.get("Passo", 0)) if pd.notna(primeira.get("Passo")) else 0
    meta["tipo_pista"] = str(primeira.get("Tipo de Pista", primeira.get("tipo_pista", "Pista de Treinamento")))

    if "Ideal Umidade" in primeira and pd.notna(primeira["Ideal Umidade"]):
        meta["ideal_umi"] = str(primeira["Ideal Umidade"])
    if "Ideal Espessura" in primeira and pd.notna(primeira["Ideal Espessura"]):
        meta["ideal_esp"] = str(primeira["Ideal Espessura"])
    if "Coletou Umidade" in primeira and pd.notna(primeira["Coletou Umidade"]):
        val = str(primeira["Coletou Umidade"]).strip().lower()
        meta["coletou_umidade"] = val in ["1", "1.0", "true", "yes"]
    if "Coletou Espessura" in primeira and pd.notna(primeira["Coletou Espessura"]):
        val = str(primeira["Coletou Espessura"]).strip().lower()
        meta["coletou_espessura"] = val in ["1", "1.0", "true", "yes"]
    if "Global Umidade" in primeira and pd.notna(primeira["Global Umidade"]):
        try:
            meta["global_umi"] = float(primeira["Global Umidade"])
        except ValueError:
            pass
    if "Global Espessura" in primeira and pd.notna(primeira["Global Espessura"]):
        try:
            meta["global_esp"] = int(float(primeira["Global Espessura"]))
        except ValueError:
            pass

    # Garante colunas de Linha e Ponto
    col_linha_nome = None
    for k in ["Linha", "linha"]:
        if k in df.columns:
            col_linha_nome = k
            break
            
    col_ponto_nome = None
    for k in ["Ponto", "ponto"]:
        if k in df.columns:
            col_ponto_nome = k
            break

    if col_linha_nome is None or col_ponto_nome is None:
        raise ValueError("O arquivo não possui as colunas obrigatórias 'Linha' e 'Ponto'.")

    # Helper para extrair colunas flexíveis de medição
    def obter_coluna_flexivel(dataframe, chaves_possiveis, obrigatorio=False, nome_coluna=""):
        for chave in chaves_possiveis:
            if chave in dataframe.columns:
                return dataframe[chave]
        if obrigatorio:
            raise ValueError(f"A coluna obrigatória '{nome_coluna}' não foi encontrada no arquivo.")
        return None

    col_q1 = obter_coluna_flexivel(df, ["1ª Queda - Impacto (cm)", "1ª Queda - Amortecimento (cm)", "1ª Queda", "Queda 1"], obrigatorio=True, nome_coluna="1ª Queda")
    col_q2 = obter_coluna_flexivel(df, ["2ª Queda - Suporte (cm)", "2ª Queda - Transição (cm)", "2ª Queda", "Queda 2"], obrigatorio=True, nome_coluna="2ª Queda")
    col_q3 = obter_coluna_flexivel(df, ["3ª Queda - Tração (cm)", "3ª Queda - Suporte (cm)", "3ª Queda", "Queda 3"], obrigatorio=True, nome_coluna="3ª Queda")
    col_umi = obter_coluna_flexivel(df, ["Umidade TDR (%)", "Umidade", "Umidade (%)"])
    col_esp = obter_coluna_flexivel(df, ["Espessura da Camada (cm)", "Espessura", "Espessura da Camada"])

    # Conversão numérica coerciva para garantir apenas dados reais
    df["1ª Queda"] = pd.to_numeric(col_q1, errors="coerce")
    df["2ª Queda"] = pd.to_numeric(col_q2, errors="coerce")
    df["3ª Queda"] = pd.to_numeric(col_q3, errors="coerce")

    # Limpar Linha, Ponto e Quedas contra NaNs
    df = df.dropna(subset=[col_linha_nome, col_ponto_nome, "1ª Queda", "2ª Queda", "3ª Queda"])
    if df.empty:
        raise ValueError("O arquivo não possui nenhuma linha com dados válidos de Linha, Ponto e as 3 Quedas.")

    df["Linha"] = pd.to_numeric(df[col_linha_nome].astype(str).str.extract(r"(\d+)", expand=False), errors="coerce").fillna(1).astype(int)
    df["Ponto"] = pd.to_numeric(df[col_ponto_nome].astype(str).str.extract(r"(\d+)", expand=False), errors="coerce").fillna(1).astype(int)
    
    meta["n_linhas"] = max(2, int(df["Linha"].max()))
    meta["n_pontos"] = max(2, int(df["Ponto"].max()))

    col_umi_num = pd.to_numeric(col_umi, errors="coerce") if col_umi is not None else pd.Series([pd.NA] * len(df), index=df.index)
    col_esp_num = pd.to_numeric(col_esp, errors="coerce") if col_esp is not None else pd.Series([pd.NA] * len(df), index=df.index)

    coleta = pd.DataFrame({
        "Linha": df["Linha"],
        "Ponto": df["Ponto"],
        "1ª Queda": df["1ª Queda"].astype(float),
        "2ª Queda": df["2ª Queda"].astype(float),
        "3ª Queda": df["3ª Queda"].astype(float),
        "Umidade": col_umi_num.loc[df.index].fillna(0.0).astype(float),
        "Espessura": col_esp_num.loc[df.index].fillna(0).astype(int),
    })

    return meta, coleta.sort_values(["Linha", "Ponto"]).reset_index(drop=True)


def preparar_dados_analise(df_coleta, meta):
    df = df_coleta.copy()
    df["X"] = df["Linha"]
    df["Y"] = df["Ponto"]
    df["Haras"] = meta["fazenda"]
    df["Pista"] = meta["pista"]
    df["Dimensão"] = meta["dimensao"]
    df["Data"] = meta["data"]
    df["Observações"] = meta.get("notas_gerais", "")
    df["Manejo Recomendado"] = meta.get("notas_manejo", "")
    df["Parecer Técnico"] = meta.get("notas_parecer", "")
    df["Passo"] = meta.get("passo", 0)
    df["Tipo de Pista"] = meta.get("tipo_pista", "Pista de Treinamento")

    df["Ideal Umidade"] = meta.get("ideal_umi", "")
    df["Ideal Espessura"] = meta.get("ideal_esp", "")
    df["Coletou Umidade"] = 1 if meta.get("coletou_umidade", True) else 0
    df["Coletou Espessura"] = 1 if meta.get("coletou_espessura", True) else 0
    df["Global Umidade"] = meta.get("global_umi", 0.0)
    df["Global Espessura"] = meta.get("global_esp", 0)

    if not meta["coletou_umidade"]:
        df["Umidade"] = meta["global_umi"]
    if not meta["coletou_espessura"]:
        df["Espessura"] = meta["global_esp"]
    
    # Garantir a estrutura de colunas com "Espessura da Camada (cm)" como alias de "Espessura"
    df["Espessura da Camada (cm)"] = df["Espessura"]
    return df


def exportar_csv(df_coleta, meta):
    df = preparar_dados_analise(df_coleta, meta)
    export = df.assign(
        Linha=df["Linha"].map(lambda n: f"Linha {n}"),
        Ponto=df["Ponto"].map(lambda n: f"Ponto {n}"),
    ).drop(columns=["X", "Y"]).rename(columns=COLunas_EXPORT)
    return export.to_csv(index=False).encode("utf-8")


def extrair_df_editor(valor, base_df):
    if valor is None:
        return base_df.copy()
    if isinstance(valor, pd.DataFrame):
        return valor.copy()
    if isinstance(valor, dict):
        if not valor:
            return base_df.copy()
        # Dict de colunas -> listas (formato comum do Streamlit)
        if all(isinstance(k, str) for k in valor.keys()):
            try:
                return pd.DataFrame(valor)
            except (ValueError, TypeError):
                pass
        # Dict de índice -> alterações por coluna
        if all(isinstance(k, int) for k in valor.keys()):
            df = base_df.copy()
            for idx, changes in valor.items():
                if not isinstance(changes, dict):
                    continue
                for col, val in changes.items():
                    if col in df.columns and idx in df.index:
                        df.at[idx, col] = val
            return df
    return base_df.copy()


def normalizar_df_coleta(df):
    if not isinstance(df, pd.DataFrame):
        df = pd.DataFrame(df)
    df = df.copy().reset_index(drop=True)
    df["Linha"] = pd.to_numeric(df["Linha"], errors="coerce").fillna(1).astype(int)
    df["Ponto"] = pd.to_numeric(df["Ponto"], errors="coerce").fillna(1).astype(int)
    df["1ª Queda"] = pd.to_numeric(df["1ª Queda"], errors="coerce").fillna(0.0)
    df["2ª Queda"] = pd.to_numeric(df["2ª Queda"], errors="coerce").fillna(0.0)
    df["3ª Queda"] = pd.to_numeric(df["3ª Queda"], errors="coerce").fillna(0.0)
    df["Umidade"] = pd.to_numeric(df["Umidade"], errors="coerce").fillna(0.0)
    df["Espessura"] = pd.to_numeric(df["Espessura"], errors="coerce").fillna(0).astype(int)
    return df


def assinatura_grade(meta):
    return (
        int(meta["n_linhas"]),
        int(meta["n_pontos"]),
        bool(meta["coletou_umidade"]),
        bool(meta["coletou_espessura"]),
    )
