# -*- coding: utf-8 -*-
# Dash Libraries
import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output

# Plotly Libraries
from plotly import tools
import plotly.graph_objs as go
import colorlover as cl

# Scientific libraries
import pandas as pd
import numpy as np
from scipy import stats
from sklearn import linear_model

# Project Assets
from dev.db_build import TVShowDatabase

#########################
# Dashboard Layout / View
#########################
app = dash.Dash(__name__)
server = app.server
app.css.append_css({"external_url": "https://codepen.io/evsDevs/pen/zLBRLL.css"})

db = TVShowDatabase()

df_s = pd.read_sql("SELECT * FROM public.shows ORDER BY title", db.conn)
df_e = pd.read_sql("SELECT * FROM public.episodes WHERE ep_rating > 0.0", db.conn)

show_opts = [{'label': row[0],'value': row[1]} for row in zip(df_s['title'],df_s['imdb_id'])]

colors = {
    'background':  '#35374A',
    'text': '#D4D6DD',
    'items': '#3B3D52',

}

app.layout = html.Div(
                    [   
                    html.Div(className='header', style={'display': 'flex'}, children=[
                        html.Img(src="/assets/tv.svg"),
                        html.H1(children='Episode Ratings')  
                        ]),                  
                    dcc.Dropdown(
                        id='shows',
                        options=show_opts,
                        multi=True,
                        placeholder="Pick shows to plot",
                    ),
                    html.Div(id='graph-container', children=[])
             ])

@app.callback(
    Output(component_id='graph-container', component_property='children'),
    [Input(component_id='shows', component_property='value')]
)
def update_graph(imdb_id_list):
    try:
        graph_list = [build_graph(imdb_id) for imdb_id in imdb_id_list]  
        return graph_list

    except TypeError:
        pass

def build_graph(imdb_id):
    show_name = df_s[df_s.imdb_id == imdb_id].title.values[0]
    id_data = df_e[df_e.imdb_id == imdb_id]
    seasons = [int(i) for i in sorted(id_data.season.unique())]
    total_seasons = max(seasons)

    fig = tools.make_subplots(rows=1, cols=total_seasons, shared_yaxes=True)

    color_scale = cl.scales['11']['qual']['Paired']
    if total_seasons > 11:
        color_scale = cl.interp(color_scale, total_seasons)

    for s in seasons:
        season_data = id_data[id_data.season == s]

        fig.append_trace(scatter_plot(season_data, color_scale[s - 1]), 1, s)
        fig.append_trace(best_fit_dim(season_data, color_scale[s - 1]), 1, s)

        fig['layout']['xaxis{}'.format(s)].update(showgrid=False,
                                                  showticklabels=False,
                                                  zeroline=False)
    
    fig['layout'].update(
        title=show_name,
        hovermode='closest',
        showlegend=False,
        yaxis=dict(
            autorange=True,
            zeroline=False,
            showgrid=False),
        paper_bgcolor= '#3B3D52',
        plot_bgcolor = '#3B3D52')

    graph = dcc.Graph(
        id=imdb_id + "-graph", 
        className='imdbgraph', 
        figure=fig,
        )
    return graph

def scatter_plot(season_data, color):
    season = season_data.season.values[0]
    hover_text = ["Episode {}: {} ({})".format(e[0],e[1], e[2]) \
        for e in zip(season_data['ep_num'],season_data['ep_name'], season_data['ep_rating'])]

    scatter = go.Scatter(
        x=season_data['ep_num'],
        y=season_data['ep_rating'],
        text=hover_text,
        hoverinfo='text',
        mode='markers',
        opacity=0.3,
        marker={
            'size': 5,
            'color': color
        },
        name="season-{}-graph".format(season)
    )
    return scatter

def best_fit(season_data, color):
    X = season_data['ep_num']
    Y = season_data['ep_rating']

    slope, intercept, r_value, p_value, std_err = stats.linregress(X, Y)
    line = slope * X + intercept

    print(type(line))

    figure = go.Scatter(
        x=X,
        y=line,
        mode='lines',
        opacity=0.75,
        marker={
            'color': color
        }
    )
    return figure

def best_fit_dim(season_data, color, dim=2):
    eps = season_data['ep_num']

    X = [[ep ** (d + 1) for d in range(dim)] for ep in eps]
    Y = season_data['ep_rating']

    clf = linear_model.LinearRegression()
    clf.fit(X, Y)
    Y_hat = pd.Series(clf.predict(X))

    figure = go.Scatter(
        x=eps,
        y=Y_hat,
        mode='lines',
        opacity=0.75,
        marker={
            'color': color
        }
    )
    return figure



if __name__ == "__main__":
    app.run_server(debug=True)                  