import asyncio
import json
import os
import pandas as pd
from dash.dependencies import Input, Output, State
from dash import dcc, html, Dash, ctx
from dash.exceptions import PreventUpdate
import dash_bootstrap_components as dbc
import dash_ag_grid as dag
from sqlalchemy import create_engine 
import utils.transforms as transforms
from utils.asyncquery import APIClient
# from dotenv import find_dotenv, dotenv_values

# config = dotenv_values(find_dotenv())
config = dict(os.environ)

uri = f"postgresql+psycopg://{config['DB_USER']}:{config['DB_PASS']}@{config['DB_HOST']}:{config['DB_PORT']}/{config['DB']}"
backend_api_url = f"http://{config['BACKEND_HOST']}:{config['BACKEND_PORT']}/calibrar"
engine = create_engine(uri)

logo = html.Div([
    html.Img(src='https://via.placeholder.com/1024x100?text=Instituto+Nacional+de+Evaluación+Educativa', className='img')
])

numeric_input = html.Div([
    dbc.Col(html.P("Porcentaje de respuestas en blanco para considerar exclusión: "), width="auto"),
    dbc.Col(dbc.Input(id='na_percent', type="number", min = 0, max = 100, step = 10, value = 30), width="auto")
], id="styled-numeric-input", className = 'divInline')

upper_div = html.Div([
    dbc.Card([
        html.H1('Base de ceros y unos'),
        dbc.CardBody([
            dcc.Upload(id = 'base-upload', className = 'uploader', children=html.Div([
                    'Arrastre aquí o ',
                    html.A('seleccione un archivo de texto (.csv)')
                ])),
                dbc.Spinner(html.Div(id="loading-output"), 
                            color='primary', spinner_class_name="customSpinner", 
                            fullscreen=True, fullscreen_style={"background-color": "rgba(0, 0, 0, 0.4)"}),      
        ]),
        numeric_input
        ], class_name='w-90'
    ),
    
    
])

lower_div = dbc.Card([
    dbc.Row(
                [
                    html.Div([html.H1('Mapas técnicos')]),
                ]
            ),
        dbc.Row([
            dbc.Col([dcc.Upload(id='elemental-upload', className = 'uploader', children=html.Div('Elemental'))]),
        dbc.Col([dcc.Upload(id='media-upload', className = 'uploader', children=html.Div('Media'))]),
        dbc.Col([dcc.Upload(id='superior-upload', className = 'uploader', children=html.Div('Superior'))]),
        dbc.Col([dcc.Upload(id='bachillerato-upload', className = 'uploader', children=html.Div('Bachillerato'))]),
        ])
            
        ])



first_tab = dcc.Tab(
    id='tab-1',
    label='Bases', children=[
            
            dbc.Row(
                upper_div, align="center"
            ),
            
            dbc.Row(
                lower_div,
            ),
            dbc.Row(
                dbc.Col(dbc.Button('Calibrar', id = 'submit-button', color='primary'), width = "auto")
            )
            
        ]
)

second_tab = html.Div([dcc.Tab(
    id='tab-2',
    label='Resultados', children=[
        html.Div(id='output-div')
    ]
), dcc.Store(id='store')])

app = Dash(__name__, external_stylesheets=[dbc.themes.MATERIA])
server = app.server

app.layout = html.Div([
    logo,
    dcc.Tabs(
        id='tabs', children = [
        first_tab, second_tab
    ], value='tab-1'),
    
])

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
    Output('tabs', 'value'), 
    Output('store', 'data'),
    Input('submit-button', 'n_clicks'),
    State('na_percent', 'value'),
    State('base-upload', 'contents'),
    State('elemental-upload', 'contents'),
    State('media-upload', 'contents'),
    State('superior-upload', 'contents'),
    State('bachillerato-upload', 'contents')
)
def process_base_maps(clicks, na_value, base_content, elemental_content, media_content, superior_content, bachillerato_content):
    
    client = APIClient(backend_api_url)
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
            resp = asyncio.run(client.process_data(table))
        
        print(json.dumps(resp))
               
                        
    return 'tab-2', json.dumps(resp)



@app.callback(
    Output('output-div', 'children'),
    Input('store', 'data')
)
def update_output(data):
    df = pd.DataFrame(data)
    
    return dag.AgGrid('grid-table', columnDefs=[{"field": i} for i in df.columns], rowData=df.to_dict(orient='records'))


if __name__ == '__main__':
    app.run_server(debug=False)