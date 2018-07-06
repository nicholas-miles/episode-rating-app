# -*- coding: utf-8 -*-
import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
import pandas as pd
from plotly import tools
import plotly.graph_objs as go
from dev.db_build import TVShowDatabase

#########################
# Dashboard Layout / View
#########################
app = dash.Dash(__name__)
server = app.server
app.css.append_css({"external_url": "https://codepen.io/chriddyp/pen/bWLwgP.css"})

db = TVShowDatabase()

df_s = pd.read_sql("SELECT * FROM public.shows ORDER BY title", db.conn)
df_e = pd.read_sql("SELECT * FROM public.episodes WHERE ep_rating > 0.0", db.conn)

show_opts = [{'label': row[0],'value': row[1]} for row in zip(df_s['title'],df_s['imdb_id'])]

app.layout = html.Div(
                    [                       
                        dcc.Dropdown(
                            id='shows',
                            options=show_opts,
                            multi=True,
                            placeholder="Pick shows to plot"
                        ),
                        html.Div(id='graph-container', children=[])
             ])

@app.callback(
    Output(component_id='graph-container', component_property='children'),
    [Input(component_id='shows', component_property='value')]
)
def update_graph(imdb_id_list):
    graph_list = [build_graph(imdb_id) for imdb_id in imdb_id_list]
            
    return graph_list

def build_graph(imdb_id):
    show_name = df_s[df_s.imdb_id == imdb_id]['title'].values[0]
    id_data = df_e[df_e.imdb_id == imdb_id]
    seasons = [int(i) for i in sorted(id_data.season.unique())]

    fig = tools.make_subplots(rows=1, cols=int(max(seasons)), shared_yaxes=True)

    for s in seasons:
        season_data = id_data[id_data.season == s]
        hover_text = ["Episode {}: {}".format(e[0],e[1]) \
            for e in zip(season_data['ep_num'],season_data['ep_name'])]

        trace = go.Scatter(
            x=season_data['ep_num'],
            y=season_data['ep_rating'],
            text=hover_text,
            hoverinfo='text',
            mode='markers',
            opacity=0.75,
            marker={
                'size': 5
            },
            name="season-{}-graph".format(s)
        )

        fig.append_trace(trace, 1, s)
        fig['layout']['xaxis{}'.format(s)].update(showgrid=False,
                                                  showticklabels=False,
                                                  zeroline=False)
    
    fig['layout'].update(
        title=show_name,
        hovermode='closest',
        yaxis=dict(
            autorange=False,
            range=[0,10],
            zeroline=False,
            showgrid=False))

    graph = dcc.Graph(id=imdb_id + "-graph", figure=fig)
    return graph

if __name__ == "__main__":
    app.run_server(debug=True)                  