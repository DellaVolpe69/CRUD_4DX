import sys
import subprocess
import streamlit as st
import pandas as pd
from datetime import date
from pathlib import Path, PureWindowsPath
import itertools
from requests_oauthlib import OAuth2Session
import time
import requests



# --- LINK DIRETO DA IMAGEM NO GITHUB ---
url_imagem = (
    "https://raw.githubusercontent.com/DellaVolpe69/Images/main/AppBackground02.png"
)
url_logo = "https://raw.githubusercontent.com/DellaVolpe69/Images/main/DellaVolpeLogoBranco.png"
fox_image = "https://raw.githubusercontent.com/DellaVolpe69/Images/main/Foxy4.png"

st.markdown(
    f"""
    <style>
    /* Remove fundo padrão dos elementos de cabeçalho que às vezes ‘brigam’ com o BG */
    header, [data-testid="stHeader"] {{
        background: transparent;
    }}
    </style>
    """,
    unsafe_allow_html=True,
)


modulos_dir = Path(__file__).parent / "Modulos"

# Se o diretório ainda não existir, faz o clone direto do GitHub
if not modulos_dir.exists():
    print("📥 Clonando repositório Modulos do GitHub...")
    subprocess.run(
        [
            "git",
            "clone",
            "https://github.com/DellaVolpe69/Modulos.git",
            str(modulos_dir),
        ],
        check=True,
    )

# Garante que o diretório está no caminho de importação
if str(modulos_dir) not in sys.path:
    sys.path.insert(0, str(modulos_dir))

# Agora importa o módulo normalmente
from Modulos import AzureLogin
from Modulos import ConectionSupaBase

###################################
# from Modulos.Minio.examples.MinIO import read_file  # ajuste o caminho se necessário


# ---------------------------------------------------
# IMPORTA CONEXÃO SUPABASE
# ---------------------------------------------------
sys.path.append(
    PureWindowsPath(
        r"\\tableau\Central_de_Performance\BI\Cloud\Scripts\Modulos"
    ).as_posix()
)
import ConectionSupaBase

supabase = ConectionSupaBase.conexao()