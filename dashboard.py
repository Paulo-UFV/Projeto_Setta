import dash
from dash import dcc, html
from dash.dependencies import Output, Input
import plotly.graph_objs as go
import psycopg2
import pandas as pd

# Configuração do Dash
app = dash.Dash(__name__)

# Função para obter dados do banco de dados
def get_data():
    conn = psycopg2.connect(
        host="localhost",
        database="monitoramento_eficiencia",
        user="postgres",
        password="Nn38510386!"
    )
    cursor = conn.cursor()
    cursor.execute("SELECT data_hora, temperatura, eficiencia FROM public.eficiencia ORDER BY data_hora")
    data = cursor.fetchall()
    df = pd.DataFrame(data, columns=["data_hora", "temperatura", "eficiencia"])
    cursor.close()
    conn.close()
    return df

# Função para calcular a previsão de eficiência
def calculate_efficiency_prediction(df):
    recent_data = df.tail(10)  # Pegue os últimos 10 registros
    efficiency_changes = recent_data["temperatura"].diff().fillna(0)  # Calcule a diferença entre temperaturas consecutivas
    prediction_sum = efficiency_changes[-8:].sum()  # Some as mudanças dos últimos 8 registros
    return prediction_sum

# Layout do Dash
app.layout = html.Div([
    html.H1("Dashboard de Monitoramento de Eficiência", style={'text-align': 'center'}),
    html.Div([
        dcc.Graph(id='gauge-efficiency', config={'displayModeBar': False}),
        dcc.Graph(id='gauge-temperature', config={'displayModeBar': False})
    ], style={'display': 'flex', 'justify-content': 'center'}),
    dcc.Interval(id='interval-component', interval=1*60000, n_intervals=0)
])

# Callback para atualizar os gráficos
@app.callback(
    [Output('gauge-efficiency', 'figure'),
     Output('gauge-temperature', 'figure')],
    [Input('interval-component', 'n_intervals')]
)
def update_gauges(n):
    df = get_data()
    efficiency = df['eficiencia'].iloc[-1]
    temperature = df['temperatura'].iloc[-1]

    efficiency_gauge = go.Figure(go.Indicator(
        mode="gauge+number",
        value=efficiency,
        title={'text': "Eficiência Atual (%)"},
        gauge={
            'axis': {'range': [0, 100]},
            'bar': {'color': "darkblue"},
            'steps': [
                {'range': [0, 20], 'color': 'red'},
                {'range': [20, 40], 'color': 'orange'},
                {'range': [40, 60], 'color': 'yellow'},
                {'range': [60, 80], 'color': 'lightgreen'},
                {'range': [80, 100], 'color': 'green'}
            ],
        }
    ))

    temperature_gauge = go.Figure(go.Indicator(
        mode="gauge+number",
        value=temperature,
        title={'text': "Temperatura Atual (°C)"},
        gauge={
            'axis': {'range': [0, 40]},
            'bar': {'color': "darkblue"},
            'steps': [
                {'range': [0, 10], 'color': 'lightcyan'},
                {'range': [10, 20], 'color': 'cyan'},
                {'range': [20, 30], 'color': 'royalblue'},
                {'range': [30, 40], 'color': 'darkblue'}
            ],
        }
    ))

    return efficiency_gauge, temperature_gauge

if __name__ == '__main__':
    app.run_server(debug=True)
