import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from pathlib import Path
from dash import Dash, html, dcc, Input, Output
import numpy as np

# --------------------------------
# PROJECT SETUP
# --------------------------------
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
DATA = DATA_DIR / "CPD_ParkArt.csv"
ART_DATA = pd.read_csv(DATA)

# --------------------------------
# HELPERS
# --------------------------------
def make_dropdown_options(column, df=ART_DATA):
    counts = df[column].value_counts(dropna=True)
    return [{"label": f"{value} ({count})", "value": value}
            for value, count in counts.items()]


def filter_data(df=ART_DATA, artists=None, parks=None, owners=None):
    df = df.copy()
    if artists:
        df = df[df["ARTIST"].isin(artists)]
    if parks:
        df = df[df["PARK"].isin(parks)]
    if owners:
        df = df[df["OWNER"].isin(owners)]
    return df


# --------------------------------
# MAP
# --------------------------------

def make_art_map(df=ART_DATA):
    fig = px.scatter_map(
        df,
        lat="Y_COORD",
        lon="X_COORD",
        color="OWNER",
        hover_name="NAME",
        hover_data={
            "ARTIST": True,
            "PARK": True,
            "OWNER": True,
        },
        zoom=10,
        height=700
    )

    fig.update_layout(
        map_center={"lat": 41.8781, "lon": -87.6298},
        margin={"r": 0, "t": 0, "l": 5, "b": 0},
        legend_title_text="Owner"
    )

    return fig


# --------------------------------
# BAR CHART
# --------------------------------

def make_bar_chart(df=ART_DATA, groupby="PARK", top_n=20):
    agg = (
        df.groupby(groupby)
        .size()
        .reset_index(name="count")
        .sort_values("count", ascending=False)
        .head(top_n)
    )

    label = groupby.capitalize()

    fig = px.bar(
        agg,
        x="count",
        y=groupby,
        orientation="h",
        title=f"Public Artworks by {label} (Top {top_n})"
    )

    fig.update_layout(
        xaxis_title="Number of artworks",
        yaxis_title=label,
        margin=dict(l=120, r=20, t=50, b=40)
    )

    return fig


# --------------------------------
# SPATIAL SPREAD
# --------------------------------

LAT_SCALE = 111.0
LON_SCALE = 111.0 * np.cos(np.radians(41.8))

def compute_artist_dispersion(df=ART_DATA, min_works=2):
    df = df.copy()
    df = df[~df["ARTIST"].isin(["Unknown", "Unknown Artist"])]
    df = df.dropna(subset=["ARTIST", "X_COORD", "Y_COORD"])

    results = []
    for artist, group in df.groupby("ARTIST"):
        if len(group) < min_works:
            continue
        x_km = group["X_COORD"] * LON_SCALE
        y_km = group["Y_COORD"] * LAT_SCALE
        x_c = x_km.mean()
        y_c = y_km.mean()
        dist = np.sqrt((x_km - x_c) ** 2 + (y_km - y_c) ** 2)
        results.append({
            "ARTIST": artist,
            "dispersion_km": dist.mean(),
            "num_works": len(group)
        })
    return pd.DataFrame(results)


def make_artist_dispersion_chart(df=ART_DATA, min_works=2):
    agg = compute_artist_dispersion(df, min_works=min_works)
    agg = agg.sort_values("dispersion_km", ascending=False)

    fig = px.scatter(
        agg,
        x="dispersion_km",
        y="num_works",
        hover_name="ARTIST",
        color="ARTIST",
        size="num_works",
        title="Artist Spatial Spread vs Number of Works"
    )

    fig.update_layout(
        xaxis_title="Spatial dispersion (km)",
        yaxis_title="Number of works",
        margin=dict(l=140, r=20, t=50, b=40)
    )

    return fig


# --------------------------------
# APP
# --------------------------------

app = Dash(__name__, suppress_callback_exceptions=True)

app.layout = html.Div(
    className="app-shell",
    children=[

        html.Header(
            className="app-header",
            children=[
                html.H1("Chicago Public Art Explorer"),
                html.P("Interactive visualizations of public artworks in Chicago parks.")
            ]
        ),

        html.Div(
            className="body",
            children=[

                html.Div(
                    className="sidebar",
                    id="sidebar",
                    children=[]
                ),

                html.Main(
                    className="main-content",
                    children=[
                        dcc.Tabs(
                            id="tabs",
                            value="tab1",
                            children=[
                                dcc.Tab(label="Interactive Map", value="tab1",
                                        children=dcc.Graph(id="main-map",
                                                           figure=make_art_map())),
                                dcc.Tab(label="Bar Chart", value="tab2",
                                        children=dcc.Graph(id="bar-chart",
                                                           figure=make_bar_chart())),
                                dcc.Tab(label="Artists and Spatial Spread", value="tab3",
                                        children=dcc.Graph(id="spatial-graph",
                                                           figure=make_artist_dispersion_chart())),
                            ]
                        ),
                    ],
                ),
            ]
        ),
    ]
)


# --------------------------------
# CALLBACKS
# --------------------------------

# ---------- Sidebar -------------
@app.callback(
    Output("sidebar", "children"),
    Input("tabs", "value")
)
def update_sidebar(active_tab):
    if active_tab == "tab1":
        return [
            html.H2("Filter by..."),
            dcc.Dropdown(id="map-artist-filter", options=make_dropdown_options("ARTIST"),
                         multi=True, placeholder="Filter by artist"),
            dcc.Dropdown(id="map-owner-filter", options=make_dropdown_options("OWNER"),
                         multi=True, placeholder="Filter by owner"),
            dcc.Dropdown(id="map-park-filter", options=make_dropdown_options("PARK"),
                         multi=True, placeholder="Filter by park"),
        ]

    if active_tab == "tab2":
        return [
            html.H2("Group by..."),
            dcc.Dropdown(
                id="bar-groupby",
                options=[
                    {"label": "Park", "value": "PARK"},
                    {"label": "Owner", "value": "OWNER"},
                    {"label": "Artist", "value": "ARTIST"},
                ],
                value="PARK",
                clearable=False,
            ),
            html.H2("Top N"),
            dcc.Slider(
                id="bar-topn",
                min=5,
                max=50,
                step=5,
                value=20,
                marks={i: str(i) for i in range(5, 51, 5)},
            ),
        ]

    if active_tab == "tab3":
        return [
            html.H2("Minimum works"),
            dcc.Slider(
                id="spatial-min-works",
                min=2,
                max=7,
                step=1,
                value=2,
                marks={i: str(i) for i in range(2, 8)},
            ),
        ]

    return []


@app.callback(
    Output("main-map", "figure"),
    Input("map-artist-filter", "value"),
    Input("map-park-filter", "value"),
    Input("map-owner-filter", "value")
)
def update_map(selected_artists, selected_parks, selected_owners):
    filtered = filter_data(ART_DATA,
                           artists=selected_artists,
                           parks=selected_parks,
                           owners=selected_owners)
    return make_art_map(filtered)


@app.callback(
    Output("bar-chart", "figure"),
    Input("bar-groupby", "value"),
    Input("bar-topn", "value")
)
def update_bar(groupby, top_n):
    return make_bar_chart(ART_DATA, groupby=groupby, top_n=top_n or 20)


@app.callback(
    Output("spatial-graph", "figure"),
    Input("spatial-min-works", "value")
)
def update_spatial(min_works):
    return make_artist_dispersion_chart(ART_DATA, min_works=min_works or 2)


if __name__ == "__main__":
    app.run(debug=True)