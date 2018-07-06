# -*- coding: utf-8 -*-
import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
import pandas as pd
import plotly.graph_objs as go
from dev.db_build import TVShowDatabase

#########################
# Dashboard Layout / View
#########################
app = dash.Dash(__name__)
server = app.server
app.css.append_css({"external_url": "https://codepen.io/chriddyp/pen/bWLwgP.css"})

db = TVShowDatabase()

df_s = pd.read_sql("SELECT * FROM shows ORDER BY title", db.conn)
df_e = pd.read_sql("SELECT * FROM episodes WHERE ep_rating > 0.0", db.conn)

show_opts = [{'label': row[0],'value': row[1]} for row in zip(df_s['title'],df_s['imdb_id'])]

app.layout = html.Div(
                    [                       
                        html.Img(src="https://s3-us-west-1.amazonaws.com/plotly-tutorials/logo/new-branding/dash-logo-by-plotly-stripe.png",
                                style={
                                    'height': '100px',
                                    'float': 'right'
                                },
                        ),

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
    graph_list = []
    for imdb_id in imdb_id_list:
        data = df_e[df_e.imdb_id == imdb_id]
        traces = []

        for i in sorted(data.season.unique()):
            season_data = data[data.season == i]
            season_figure = go.Scatter(
                                x=season_data["ep_num"],
                                y=season_data["ep_rating"],
                                mode="markers",
                                opacity=0.3,
                                marker={
                                            "size": 15,
                                            "line": {"width": 0.5, "color": "white"}
                                        },
                                name='season-{}-graph'.format(i)
                            )
            traces.append(season_figure)
        
        graph_list.append(dcc.Graph(
                    id=imdb_id + "-graph",
                    figure=
                        {
                            'data': traces,
                            'layout': go.Layout(
                                xaxis={'title': "Episode Number"},
                                yaxis={'title': "Rating"},
                                hovermode='closest'
                            )
                        }
                    )
        )

    return graph_list


if __name__ == "__main__":
    app.run_server(debug=True)                  