import dash
from dash import dcc, html, Input, Output
import pandas as pd
from dash import dash_table

app = dash.Dash(__name__)

app.layout = html.Div([
    html.Div([
        html.Link(
            rel='stylesheet',
            href='https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css'
        ),
        html.Div([
            # Top image
            html.Img(
                src='assets/img/agus.PNG',
                style={
                    'width': '150px',
                    'margin': '10px auto',
                    'display': 'block',
                    'border-radius': '80px',
                    'border': '2px solid #6A5ACD'
                }
            ),
            html.H2([
                html.I(className='fa-brands fa-octopus-deploy', style={'marginRight': '10px'}),
                'Agustina Fassina'
            ], style={
                'display': 'flex',
                'justifyContent': 'center',
                'alignItems': 'center',
                'margin': '20px 0',
                'fontFamily': 'Arial, sans-serif',
                'color': '#fff'
            }),
            html.Button([
                html.I(className='fas fa-satellite button-icon'),
                'IPs Scanned'
            ], id='btn-ips', className='modern-button'),

            html.Button([
                html.I(className='fas fa-wifi button-icon'),
                'Open ports'
            ], id='btn-ports', className='modern-button'),

            html.Button([
                html.I(className='fas fa-globe-americas button-icon'),
                'Domains'
            ], id='btn-domains', className='modern-button')
        ], style={
            'width': '18%',
            'backgroundColor': '#483D8B',
            'padding': '10px',
            'display': 'flex',
            'flexDirection': 'column',
            'height': '90vh',
            'fontFamily': 'Arial, sans-serif',
        }),
        html.Div(id='content-area')
    ], style={
        'display': 'flex',
        'flexDirection': 'row',
        'height': '90vh',
        'fontFamily': 'Arial, sans-serif'
    }),
    # Footer
    html.Footer("© 2025 By Agustina Fassina")
], style={'display': 'flex', 'flexDirection': 'column', 'minHeight': '100vh'})

@app.callback(
    Output('content-area', 'children'),
    [Input('btn-ips', 'n_clicks'),
     Input('btn-ports', 'n_clicks'),
     Input('btn-domains', 'n_clicks')]
)
def display_content(n_clicks_ips, n_clicks_ports, n_clicks_domains):
    ctx = dash.callback_context
    if not ctx.triggered:
        return html.P("Select menu option")
    button_id = ctx.triggered[0]['prop_id'].split('.')[0]

    if button_id == 'btn-ips':
        df = pd.read_csv('scan_publicips_result-1.csv')

        # 1. Ips count
        ip_counts = df['Public_IP'].value_counts().reset_index()
        ip_counts.columns = ['Public IP', 'Count']
        total_ips = df['Public_IP'].nunique()

        # 2. IPs with open ports and what they are
        ips_with_port_22 = df[df['Open_Ports'].dropna().apply(lambda x: '22' in str(x).split(','))]
        ips_with_port_22_unique = len(ips_with_port_22['Public_IP'].unique())

        # 2. IPs with RDP port open (3389)
        ips_con_rdp = df[df['Open_Ports'].dropna().apply(lambda x: '3389' in str(x).split(','))]
        count_rdp = len(ips_con_rdp['Public_IP'].unique())

        # 3. Number of open ports (histogram)
        df['Ports_List'] = df['Open_Ports'].apply(lambda x: len(str(x).split(',')))

        fig_barras = {
            'data': [
                {'x': ['Puerto 22', 'RDP (3389)', 'Total IPs'], 'y': [ips_with_port_22_unique, count_rdp, total_ips], 'type': 'bar'}
            ],
            'layout': {
                'title': 'Comparación de IPs con puertos abiertos',
                'yaxis': {'title': 'Cantidad'},
                'xaxis': {'title': 'Métrica'}
            }
        }

        # Table with Ips
        ip_table = dash_table.DataTable(
            data=ip_counts.to_dict('records'),
            columns=[{'name': col, 'id': col} for col in ip_counts.columns],
            style_header={'backgroundColor': 'rgb(230, 230, 230)', 'fontWeight': 'bold'},
        )

        total_count_html = html.Div([
                html.H4("Results"),
                html.P(f"Total number of unique IPs: {total_ips}"),
                html.P(f"IPs with port 22 open: {ips_with_port_22_unique}")
            ], style={'width': '40%', 'padding': '10px', 'border': '1px solid #ccc', 'border-radius': '8px', 'backgroundColor': '#f9f9f9'
        })

        return html.Div([
            # Flex container
            html.H2([
                html.I(className='fas fa-satellite button-icon', style={'marginRight': '10px'}),
                    'IPs Scanned'
                ], style={'display': 'flex', 'alignItems': 'center'}
            ),
            html.Div([
                # Graph
                html.Div([
                    html.H4("Number of open ports on IPs"),
                    dcc.Graph(figure=fig_barras, style={'height': '400px'})
                ], style={'width': '60%', 'padding': '10px'}),

                # Counter
                total_count_html,
            ], style={'display': 'flex', 'flexDirection': 'row'}),
            ip_table
        ])
    elif button_id == 'btn-domains':
        df = pd.read_csv('scan_publicips_result-1.csv')
        return html.Div([
            html.H3("Dominios"),
            dcc.Graph(figure={
                'data': [{'labels': df['Domain'], 'values': df['Count'], 'type': 'pie'}],
                'layout': {'title': 'Dominios'}
            })
        ])

if __name__ == '__main__':
    app.run(debug=True)