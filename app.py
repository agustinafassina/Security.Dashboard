import dash
from dash import dcc, html, Input, Output
import pandas as pd
from dash import dash_table
import plotly.graph_objs as go

app = dash.Dash(__name__)

def report_ips():
    df = pd.DataFrame({'IPs': ['192.168.1.1', '10.0.0.2'], 'Count': [5, 3]})
    fig = go.Figure(data=[go.Bar(x=df['IPs'], y=df['Count'])])
    return html.Div([
        html.H2([
            html.I(style={'marginRight': '10px'}),
                'IPs Scanned'
            ], style={'display': 'flex', 'alignItems': 'center'}
        ),
        dcc.Graph(figure=fig)
    ])

def report_ports():
    df_users = pd.read_csv('scan_publicips_results.csv')

    def check_open_ports(row):
        open_ports = eval(row['OpenPorts'])
        return 'Open' if 22 in open_ports else 'Closed'

    df_users['Port22Status'] = df_users.apply(check_open_ports, axis=1)

    port_status_counts = df_users['Port22Status'].value_counts()

    fig = go.Figure(data=[go.Pie(labels=port_status_counts.index, values=port_status_counts.values,
                                   marker=dict(colors=['#2ca02c', '#d62728']))])

    fig.update_layout(
        title='Port 22 Status by Public IP',
    )

    table = dash_table.DataTable(
        data=df_users.to_dict('records'),
        columns=[{'name': col, 'id': col} for col in df_users.columns],
        page_size=10,
        style_table={'overflowX': 'auto', 'textAlign': 'justify'}
    )

    return html.Div([
        html.H3("Open Ports Report"),
        dcc.Graph(figure=fig),
        html.H4("Details of Public IPs"),
        table
    ])

def report_domains():
    return html.Div([
        html.H3("Domains Report"),
        html.P("Aquí iria tu contenido de dominios")
    ])

def report_users():
    df_users = pd.read_csv('iam_users_results.csv')
    group_counts = df_users['Groups'].value_counts().reset_index()
    group_counts.columns = ['Group', 'Number of Users']
    fig = go.Figure(data=[go.Bar(x=group_counts['Group'], y=group_counts['Number of Users'])])

    table = dash_table.DataTable(
        data=df_users.to_dict('records'),
        columns=[{'name': col, 'id': col} for col in df_users.columns],
        page_size=10,
        style_table={'overflowX': 'auto', 'text-align': 'justify'},
    )

    return html.Div([
        html.H3("IAM: users and permissions"),
        dcc.Graph(figure=fig),
        html.H4("Full Data Table"),
        table
    ])

def report_logs():
    return html.Div([
        html.H3("Logs Analysis"),
        html.P("Análisis de logs")
    ])

app.layout = html.Div([
    html.Link(
        rel='stylesheet',
        href='https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css'
    ),
    html.Div([
        html.Div([
            html.H2(
                [
                    html.I(className='fa-solid fa-building-lock', style={'marginRight': '10px'}),
                    'Security Dashboard'
                ],
                style={'margin': '0', 'display': 'flex', 'alignItems': 'center'}
            ),
        ], style={'flex': 1, 'display': 'flex', 'alignItems': 'center'}
        ),
        html.Div([
            html.Span("Welcome", style={
                'marginRight': '15px', 'fontSize': '20px', 'fontWeight': 'bold', 'alignSelf': 'center'
            }),
            html.Img(
                src='assets/img/agus.PNG',
                style={
                    'width': '55px',
                    'height': '55px',
                    'border-radius': '50%',
                    'border': '2px solid #104E63',
                    'verticalAlign': 'middle',
                    'margin': '5px'
                }
            ),
        ], style={'display': 'flex', 'alignItems': 'center'})
    ], style={'display': 'flex', 'justifyContent': 'space-between', 'backgroundColor': '#fff', 'padding': '0px 50px'}),
    html.Div([
        html.Div([
            dcc.Tabs([
                dcc.Tab(label=' Security Headers report ', children=report_ips(), className="custom-tab"),
                dcc.Tab(label=' Public Ip: Open ports (1000 ports) ', children=report_ports(), className="custom-tab"),
                dcc.Tab(label=' TLS/SSL status in the domains ', children=report_domains(), className="custom-tab"),
                dcc.Tab(label=' IAM: users and permissions ', children=report_users(), className="custom-tab"),
            ]),
        ], className="bottom-area"),
    ], className="header-area"),
    html.Footer("© 2025 By Agustina Fassina", style={'textAlign': 'center', 'padding': '10px', 'fontFamily': 'Arial, sans-serif'})
])

if __name__ == '__main__':
    app.run(debug=True)