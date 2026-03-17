import os
import string
import random
import psycopg2
from flask import Flask, request, redirect, jsonify, render_template
from dotenv import load_dotenv


load_dotenv()

app = Flask(__name__)

DATABASE_URL = os.getenv("DATABASE_URL")

def get_conn():
    return psycopg2.connect(
        DATABASE_URL,
        sslmode='require'  # 🔥 obrigatório pro Supabase
    )

def gerar_codigo(tamanho=6):
    caracteres = string.ascii_letters + string.digits
    return ''.join(random.choice(caracteres) for _ in range(tamanho))

def get_dominio():
    try:
        with open("dominio.txt", "r") as f:
            dominio = f.read().strip()
            if dominio:
                return dominio
    except:
        pass
    
    return request.host_url

@app.route("/")
def home():
    dominio = get_dominio()
    return render_template("index.html", dominio=dominio)

@app.route("/encurtar", methods=["POST"])
def encurtar():
    try:
        data = request.get_json()

        url = data.get("url")
        nome = data.get("nome")
        codigo_personalizado = data.get("codigo")

        if not url:
            return jsonify({"erro": "URL obrigatória"}), 400
        
        if not url.startswith("http"):
            url = "https://" + url

        if codigo_personalizado:
            codigo = codigo_personalizado.lower().replace(" ", "_")
        else:
            codigo = gerar_codigo()

        conn = get_conn()
        cur = conn.cursor()

        cur.execute("SELECT 1 FROM urls WHERE codigo = %s", (codigo,))
        if cur.fetchone():
            return jsonify({"erro": "Código já existe"}), 400

        cur.execute(
            "INSERT INTO urls (codigo, url_original, nome) VALUES (%s, %s, %s)",
            (codigo, url, nome)
        )

        conn.commit()
        cur.close()
        conn.close()

        dominio = get_dominio()

        return jsonify({"short_url": f"{dominio}{codigo}"})

    except Exception as e:
        print("ERRO BACKEND:", str(e))
        return jsonify({"erro": str(e)}), 500
    

# 📊 LISTAR LINKS
@app.route("/links")
def listar_links():
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        SELECT codigo, url_original, nome, cliques
        FROM urls
        ORDER BY criado_em DESC
    """)

    rows = cur.fetchall()

    dominio = get_dominio()

    resultado = []
    for r in rows:
        resultado.append({
            "codigo": r[0],
            "url": r[1],
            "nome": r[2],
            "cliques": r[3],
            "short": f"{dominio}{r[0]}"
        })

    cur.close()
    conn.close()

    return jsonify(resultado)

# 🔄 REDIRECIONAMENTO
@app.route("/<codigo>")
def redirecionar(codigo):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute(
        "SELECT url_original FROM urls WHERE codigo = %s",
        (codigo,)
    )

    result = cur.fetchone()

    if result:
        url = result[0]

        cur.execute(
            "UPDATE urls SET cliques = cliques + 1 WHERE codigo = %s",
            (codigo,)
        )
        conn.commit()

        cur.close()
        conn.close()

        return redirect(url)

    return "Link não encontrado", 404

@app.route("/excluir/<codigo>", methods=["DELETE"])
def excluir(codigo):
    try:
        conn = get_conn()
        cur = conn.cursor()

        cur.execute("DELETE FROM urls WHERE codigo = %s", (codigo,))
        conn.commit()

        cur.close()
        conn.close()

        return jsonify({"msg": "Excluído com sucesso"})

    except Exception as e:
        return jsonify({"erro": str(e)}), 500

if __name__ == "__main__":
    app.run()