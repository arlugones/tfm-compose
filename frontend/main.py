import urllib
import os
import pandas as pd
from dash.dependencies import Input, Output, State
from dash import dcc, html, Dash, DiskcacheManager, CeleryManager
from dash.exceptions import PreventUpdate
import dash_bootstrap_components as dbc
import dash_ag_grid as dag
import plotly.express as px
import plotly.graph_objs as go
from sqlalchemy import create_engine 
import utils.transforms as transforms
# from utils.asyncquery import APIClient, HttpxAPIClient, process_data
from utils.syncquery import process_data
from dotenv import find_dotenv, dotenv_values

# config = dotenv_values(find_dotenv())
config = dict(os.environ)

# if 'REDIS_URL' in os.environ:
#     # Use Redis & Celery if REDIS_URL set as an env variable
#     from celery import Celery
#     celery_app = Celery(__name__, broker=os.environ['REDIS_URL'], backend=os.environ['REDIS_URL'])
#     background_callback_manager = CeleryManager(celery_app)

# else:
#     # Diskcache for non-production apps when developing locally
#     import diskcache
#     cache = diskcache.Cache("./cache")
#     background_callback_manager = DiskcacheManager(cache)

import diskcache
cache = diskcache.Cache("./cache")
background_callback_manager = DiskcacheManager(cache)

uri = f"postgresql+psycopg://{config['DB_USER']}:{config['DB_PASS']}@{config['DB_HOST']}:{config['DB_PORT']}/{config['DB']}"
backend_api_url = f"http://{config['BACKEND_HOST']}:{config['BACKEND_PORT']}/calibrar"
engine = create_engine(uri)

logo = html.Div([
    html.Img(src='https://via.placeholder.com/1024x100?text=Instituto+Nacional+de+Evaluación+Educativa', className='img')
])

numeric_input = html.Div([
    dbc.Col(html.P("Porcentaje de respuestas en blanco para considerar exclusión: ", style={'margin': '0.5rem'}), width="auto"),
    dbc.Col(dbc.Input(id='na_percent', type="number", min = 0, max = 100, step = 10, value = 30), width="auto")
], id="styled-numeric-input", className = 'divInline')

upper_div = html.Div([
    dbc.Card([
        html.H1('Base de aciertos de estudiantes', style={'margin': '0.5rem'}),
        dbc.CardBody([
            dcc.Upload(id='base-upload', className='uploader', children=html.Div([
                'Arrastre aquí o ',
                html.A('seleccione un archivo de texto (.csv)')
            ])),

        ]),
        numeric_input
    ], class_name='w-90', style={'margin': '1rem'})
    
    
])

lower_div = html.Div([
    dbc.Card([
        html.H1('Mapas técnicos', style={'margin': '0.5rem'}),
        dbc.Row([
            dbc.Col([dcc.Upload(id='elemental-upload', className = 'uploader', children=html.Div('Elemental'))]),
        dbc.Col([dcc.Upload(id='media-upload', className = 'uploader', children=html.Div('Media'))]),
        dbc.Col([dcc.Upload(id='superior-upload', className = 'uploader', children=html.Div('Superior'))]),
        dbc.Col([dcc.Upload(id='bachillerato-upload', className = 'uploader', children=html.Div('Bachillerato'))]),
        ])
    ], style={'margin': '1rem'})
])

first_tab = dbc.Tab(
    id='tab-1',
    label='Bases', children=[
            
            dbc.Row(
                upper_div, align="center"
            ),
            
            dbc.Row(
                lower_div,
            ),
            dbc.Row(
                dbc.Col(dbc.Button('Calibrar', id = 'submit-button', color='primary'), width = "auto"), style={'margin': '0.5rem'}
            )
            
        ],
        tab_id='tab-1'
)

second_tab = dbc.Tab(
    id='tab-2',
    label='Resultados', 
    children=[
        html.Div(id='output-div')
    ],
    tab_id='tab-2',
    style={'margin': '1rem'}
)

third_tab = dbc.Tab(
    id='tab-3',
    label='Clustering', 
    children=[
        html.Div(id='plot-div')
    ],
    tab_id='tab-3',
    style={'margin': '1rem'}
)

app = Dash(__name__, external_stylesheets=[dbc.themes.LUMEN], 
           suppress_callback_exceptions=True, title='Calibrador de ítems',
           update_title='Cargando...',)
server = app.server

app.layout = html.Div([
    logo,
    dbc.Tabs(
        id='tabs', children = [
        first_tab, second_tab, third_tab
    ], active_tab='tab-1'),
    dbc.Spinner(html.Div(id="loading-output"), 
                            color='primary', spinner_class_name="customSpinner", 
                            fullscreen=True, fullscreen_style={"background-color": "rgba(0, 0, 0, 0.4)"}),
    dcc.Store(id='mystore', storage_type='session')]
    
)

@app.callback(
    Output('submit-button', 'disabled'),
    [Input('base-upload', 'filename'),
     Input('elemental-upload', 'filename'),
     Input('media-upload', 'filename'),
     Input('superior-upload', 'filename'),
     Input('bachillerato-upload', 'filename')]
)
def update_submit_button(base_upload, elemental_upload, media_upload, superior_upload, bachillerato_upload):
    return not (base_upload and elemental_upload or base_upload and media_upload or base_upload and superior_upload or base_upload and bachillerato_upload)


## Actualiza nombre de uploaders
@app.callback(
    Output("base-upload", "children"),
    Input("base-upload", "filename")
)
def update_uploader_text(base_mapname):
    
    if base_mapname:
        return html.Div([base_mapname])
    else:
        raise PreventUpdate

@app.callback(
    Output("media-upload", "children"),
    Input("media-upload", "filename")
)
def update_uploader_text(media_mapname):
    
    if media_mapname:
        return html.Div([media_mapname])
    else:
        raise PreventUpdate
    
@app.callback(
    Output("superior-upload", "children"),
    Input("superior-upload", "filename")
)
def update_uploader_text(superior_mapname):
    
    if superior_mapname:
        return html.Div([superior_mapname])
    else:
        raise PreventUpdate

@app.callback(
    Output("elemental-upload", "children"),
    Input("elemental-upload", "filename")
)
def update_uploader_text(elemental_mapname):
    
    if elemental_mapname:
        return html.Div([elemental_mapname])
    else:
        raise PreventUpdate
    
@app.callback(
    Output("bachillerato-upload", "children"),
    Input("bachillerato-upload", "filename")
)
def update_uploader_text(bachillerato_mapname):
    
    if bachillerato_mapname:
        return html.Div([bachillerato_mapname])
    else:
        raise PreventUpdate

# Procesamiento principal de datos
@app.callback(
    Output('tabs', 'active_tab'), 
    Output('mystore', 'data'),
    Output('loading-output', 'children'),
    Input('submit-button', 'n_clicks'),
    State('na_percent', 'value'),
    State('base-upload', 'contents'),
    State('elemental-upload', 'contents'),
    State('media-upload', 'contents'),
    State('superior-upload', 'contents'),
    State('bachillerato-upload', 'contents'),
    background=True,
    manager=background_callback_manager,
)
def process_base_maps(clicks, na_value, base_content, elemental_content, media_content, superior_content, bachillerato_content):
    
    # client = HttpxAPIClient(backend_api_url)
    if clicks is None:
        raise PreventUpdate

    else:
        try:
            # db_schema = re.search(r'^(\w+?)_', filename).group(1)

            base = transforms.base_processing(base_content)
            
        
            # Mapas
            mapa_contenidos = {
                'elemental': elemental_content or None, 
                'media': media_content or None, 
                'superior': superior_content or None, 
                'bachillerato': bachillerato_content or None
            }

            mapas = transforms.map_processing(mapa_contenidos)

        ## TODO mejorar manejo de excepciones: esquema no coincide, formato no reconocido, etc.
        except:
            return dbc.Modal(
            [
                dbc.ModalHeader(
                    dbc.ModalTitle("Error de procesamiento"), close_button=False
                ),
                dbc.ModalBody(
                    "Al menos uno de los archivos subidos contiene errores. Corrija el formato y/o la estructura y vuelva a subirlos."
                ),
                dbc.ModalFooter(dbc.Button("Cerrar", id="close-dismiss")),
            ],
            id="modal-dismiss",
            keyboard=False,
            backdrop="static",
        ) 

        group_list_keys = [
                'bachillerato_estudios_sociales',
                'bachillerato_ciencias_naturales',
            ]
        ## Se asume el orden en que aparecen las preguntas en ciencias_naturales y estudios sociales
        weird_map = {
                'bachillerato_ciencias_naturales': mapas['bachillerato_fisica'] + mapas['bachillerato_quimica'] + mapas['bachillerato_biologia'],
                'bachillerato_estudios_sociales': mapas['bachillerato_historia'] + mapas['bachillerato_educacion_para_la_ciudadania'] + mapas['bachillerato_filosofia']
            }
        
        ## Revisar demora
        table_list = []
        resp = []
        for k in base.keys():
            df = base[k]
            dfcols = df.columns
            base_matches_p = dfcols.str.match(r'p\d+')
            rename_dict = {
                col: new_name for col, new_name in zip(dfcols[base_matches_p], weird_map[k] if k in group_list_keys else mapas[k])
            }
            drop_columns = [name for name in dfcols[base_matches_p] if name not in rename_dict.keys()]

            df = df.rename(columns=rename_dict)
            df = df.drop(columns=drop_columns)

            na_percentages =df.drop(columns=['grado', 'instrumento']).isna().mean(axis=1)
            df = df[na_percentages <= na_value / 100]
            
            base[k] = df        

            table_name = k
            
            # Escribiendo en la base de PG
            table_list.append(table_name)
            base[k].to_sql(table_name, con=engine)

        for table in table_list:
            # resp = asyncio.run(process_data(backend_api_url, table))
            resp.append(process_data(backend_api_url, table))
  
                        
    return 'tab-2', resp, None


@app.callback(
    Output('output-div', 'children'),
    Input('mystore', 'data')
)
def update_output(mydata):
    if mydata is None:
        raise PreventUpdate
    else:
        flat_dict = [dict(**d) for sublist in mydata for d in sublist]
        df = pd.DataFrame(flat_dict)
    
    return [
        html.H1('Tabla de resultados de calibración'),
        dag.AgGrid(
            id='grid-table', 
            columnDefs=[{"field": i} for i in df.columns], 
            rowData=df.to_dict(orient='records'),
            defaultColDef={"filter": "agTextColumnFilter"},
            className='ag-theme-balham'
        ),
        dbc.Button("Descargar CSV", color="success", className="me-1", id="download-button"),
        ]

@app.callback(
    Output("download-button", "href"),
    Input("download-button", "n_clicks"),
    Input('mystore', 'data')
)
def download_csv(n_clicks, mydata):
    if n_clicks is None:
        raise PreventUpdate
    else:
        flat_dict = [dict(**d) for sublist in mydata for d in sublist]
        df = pd.DataFrame(flat_dict)
        csv_string = df.to_csv(sep=';', decimal=',', index=False, encoding='utf-8')
        csv_string = "data:text/csv;charset=utf-8," + urllib.parse.quote(csv_string.encode('utf-8'))
        return csv_string

@app.callback(
    Output('plot-div', 'children'),
    Input('mystore', 'data')
)
def clustering_plot(mydata):

    if mydata is None:
        raise PreventUpdate
    else:
        flat_dict = [dict(**d) for sublist in mydata for d in sublist]
        df = pd.DataFrame(flat_dict)
        return [
            
            html.Div([
                dbc.Row(html.H1('Clustering de items calibrados')),
                dbc.Row([
                    dbc.Col([
                        dbc.Label('Seleccione grado'),
                        dbc.Select(
                            id='campo-dropdown',
                            options=[{'label': col, 'value': col} for col in df['campo'].unique()],
                            placeholder='Seleccione grado',
                            value=df['campo'].unique()[0]
                        ),
                        dbc.Label('Seleccione materia'),
                        dbc.Select(
                            id='materia-dropdown',
                            options=[{'label': col, 'value': col} for col in df['materia'].unique()],
                            placeholder='Seleccione materia',
                            value=df['materia'].unique()[0]
                        ),
                        dbc.Label('Número de clusters'),
                        dbc.Input(id='clusters-input', type="number", min=1, max=10, step=1, value=3),
                        html.Hr(),
                        dbc.Label('Eje x'),
                        dbc.Select(
                            id='x-axis-dropdown',
                            options=[{'label': col, 'value': col} for col in df.select_dtypes(include=['int64', 'float64']).columns],
                            placeholder='Seleccione eje x',
                            value=df.select_dtypes(include=['int64', 'float64']).columns[1]
                        ),
                        dbc.Label('Eje y'),
                        dbc.Select(
                            id='y-axis-dropdown',
                            options=[{'label': col, 'value': col} for col in df.select_dtypes(include=['int64', 'float64']).columns],
                            placeholder='Seleccione eje y',
                            value=df.select_dtypes(include=['int64', 'float64']).columns[2]
                        )

                    ], width=4),
                    dbc.Col([
                        dcc.Graph(
                            id='cluster-plot',
                            figure={}
                        )
                    ], width=8)
                ])
            ])
        ]

@app.callback(
    Output('cluster-plot', 'figure'),
    Input('campo-dropdown', 'value'),
    Input('materia-dropdown', 'value'),
    Input('clusters-input', 'value'),
    Input('x-axis-dropdown', 'value'),
    Input('y-axis-dropdown', 'value'),
    State('mystore', 'data')
)
def plot_clusters(campo, materia, clusters, x, y, df):
    if df is None:
        raise PreventUpdate
    else:
        flat_dict = [dict(**d) for sublist in df for d in sublist]
        df = pd.DataFrame(flat_dict)

        df = df[(df['campo'] == campo) & (df['materia'] == materia)]

        df = transforms.clustering(df, clusters, x, y).reset_index()

    #     fig = px.scatter(df, x=x, y=y, color='cluster', symbol='cluster', hover_data='id_item')
    #     fig.update_layout(height=500, width=700)
    
    # return fig
        data = [
            go.Scatter(
                x=df.loc[df.cluster == clust, x],
                y=df.loc[df.cluster == clust, y],
                mode="markers",
                marker={"size": 8},
                name=f"Cluster {clust}",
                hovertext=df.loc[df.cluster == clust, 'id_item']
            )
            for clust in range(clusters)
        ]

    layout = {"xaxis": {"title": x}, "yaxis": {"title": y}}

    return go.Figure(data=data, layout=layout)

# if __name__ == '__main__':
#     app.run_server(debug=True, port=8050)