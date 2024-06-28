from flask import Flask, render_template, redirect
import psycopg2
import requests
import matplotlib.pyplot as plt
import datetime
import logging
import os

app = Flask(__name__)

# logs
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# conexão com o banco
def get_db_connection():
    try:
        conn = psycopg2.connect(
            host="localhost",
            database="monitoramento_eficiencia",
            user="postgres",
            password="Nn38510386!"
        )
        logger.info("Conexão com o banco de dados estabelecida com sucesso.")
        return conn
    except psycopg2.Error as e:
        logger.error(f"Erro ao conectar ao banco de dados: {e}")
        raise e

# API
def get_weather_data():
    try:
        api_key = "bbcb951172e3ee733b94637b4b5be5ab"
        city = "Patos de Minas"
        url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric"
        response = requests.get(url)
        data = response.json()
        logger.info(f"Dados recebidos da API: {data}")
        if 'main' in data:
            temperature = round(data['main']['temp'], 2)
            efficiency = round(max(23, min(100, 23 + (temperature - 21) * 7.545)), 2)
            return temperature, efficiency
        else:
            raise KeyError(f"A chave 'main' não está presente na resposta da API: {data}")
    except Exception as e:
        logger.error(f"Erro ao obter dados da API: {e}")
        raise e

# registrar dados no banco de dados
def log_data(conn, temperature, efficiency):
    try:
        cursor = conn.cursor()
        timestamp = datetime.datetime.now()
        logger.info(f"Inserindo dados: {timestamp}, {temperature}, {efficiency}")
        cursor.execute("INSERT INTO public.eficiencia (data_hora, temperatura, eficiencia) VALUES (%s, %s, %s)",
                       (timestamp, temperature, efficiency))
        conn.commit()
        cursor.close()
        logger.info("Dados inseridos com sucesso")
    except psycopg2.Error as e:
        conn.rollback()
        logger.error(f"Erro ao registrar dados no banco de dados: {e}")
        raise e

# buscar dados do banco de dados
def fetch_data(conn):
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT data_hora, temperatura, eficiencia FROM public.eficiencia ORDER BY data_hora")
        data = cursor.fetchall()
        cursor.close()
        logger.info(f"Dados buscados do banco de dados: {data}")
        return data
    except psycopg2.Error as e:
        logger.error(f"Erro ao buscar dados do banco de dados: {e}")
        raise e

# gerar o gráfico
def plot_data(data):
    try:
        timestamps = [row[0] for row in data]
        temperatures = [row[1] for row in data]
        efficiencies = [row[2] for row in data]

        plt.figure(figsize=(10, 5))
        plt.plot(timestamps, temperatures, label='Temperatura (°C)', color='blue')
        plt.plot(timestamps, efficiencies, label='Eficiência (%)', color='orange')
        plt.xlabel('Data e Hora')
        plt.ylabel('Valores')
        plt.title('Temperatura e Eficiência ao longo do tempo', pad=20)

        # Adicionando anotações a cada ponto com ajustes
        for i, (ts, temp, eff) in enumerate(zip(timestamps, temperatures, efficiencies)):
            plt.annotate(f"{temp}°C", (ts, temp), textcoords="offset points", xytext=(0,10), ha='center', fontsize=8, color='blue')
            plt.annotate(f"{eff}%", (ts, eff), textcoords="offset points", xytext=(0,10), ha='center', fontsize=8, color='orange')

        plt.legend()
        plt.grid(False)
        plot_path = os.path.join('static', 'plot.png')
        plt.savefig(plot_path)
        plt.close()
        logger.info("Gráfico gerado com sucesso")
        return plot_path
    except Exception as e:
        logger.error(f"Erro ao gerar o gráfico: {e}")
        raise e

@app.route('/')
def index():
    conn = None
    try:
        conn = get_db_connection()
        temperature, efficiency = get_weather_data()
        log_data(conn, temperature, efficiency)
        data = fetch_data(conn)
        plot_url = plot_data(data)
        last_entry = data[-1] if data else (None, None, None)
        last_update = last_entry[0].strftime('%d/%m/%Y %H:%M:%S') if last_entry[0] else None
        display_temperature = int(last_entry[1]) if last_entry[1] is not None else None
        display_efficiency = round(last_entry[2], 2) if last_entry[2] is not None else None
        return render_template('index.html', temperature=display_temperature, efficiency=display_efficiency, last_update=last_update, plot_url=plot_url)
    except Exception as e:
        logger.error(f"Ocorreu um erro: {str(e)}")
        return f"Ocorreu um erro: {str(e)}"
    finally:
        if conn:
            conn.close()
            logger.info("Conexão com o banco de dados fechada.")

@app.route('/dashboard')
def dashboard_redirect():
    return redirect("http://localhost:8050", code=302)

if __name__ == '__main__':
    app.run(debug=True)
