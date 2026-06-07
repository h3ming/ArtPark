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
# NAME ANALYSIS
# --------------------------------

STOPWORDS = {
    "a", "an", "the", "and", "or", "of", "in", "at", "to", "for",
    "on", "with", "by", "from", "as", "is", "it", "its", "de", "la",
    "le", "von", "van", "el", "ii", "iii", "iv", "&"
}

def compute_word_freq(df=ART_DATA, top_n=30):
    names = df["NAME"].dropna().str.lower()
    words = []
    for name in names:
        tokens = name.replace("(", "").replace(")", "").replace("/", " ").split()
        for word in tokens:
            word = word.strip(".,\"'-")
            if word and word not in STOPWORDS and len(word) > 1:
                words.append(word)

    freq = pd.Series(words).value_counts().reset_index()
    freq.columns = ["word", "count"]
    return freq.head(top_n)


def make_word_freq_chart(df=ART_DATA, top_n=30):
    freq = compute_word_freq(df, top_n=top_n)

    fig = px.bar(
        freq,
        x="count",
        y="word",
        orientation="h",
        title=f"Most Common Words in Artwork Titles (Top {top_n})"
    )

    fig.update_layout(
        xaxis_title="Number of artworks",
        yaxis_title="Word",
        yaxis={"categoryorder": "total ascending"},
        margin=dict(l=120, r=20, t=50, b=40)
    )

    return fig


# --------------------------------
# TREEMAP
# --------------------------------

def make_ownership_treemap(df=ART_DATA):
    df = df.dropna(subset=["OWNER"]).copy()
    df = df[df["OWNER"].str.strip() != ""]

    fig = px.treemap(
        df,
        path=["OWNER", "PARK", "NAME"],
        title="Artwork Ownership: Owner → Park → Artwork",
        custom_data=["OWNER", "PARK"]
    )

    fig.update_traces(
        hovertemplate="<b>%{label}</b><br>Owner: %{customdata[0]}<br>Located in: %{customdata[1]}<extra></extra>"
    )

    fig.update_layout(
        margin=dict(l=10, r=10, t=50, b=10)
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
                html.P("Interactive visualizations using the names, location data, and owernship data of public artworks in Chicago parks.")
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
                                dcc.Tab(label="Artwork Count", value="tab2",
                                        children=dcc.Graph(id="bar-chart",
                                                           figure=make_bar_chart())),
                                dcc.Tab(label="Artwork Name Analysis", value="tab3",
                                        children=dcc.Graph(id="name-freq-chart",
                                                           figure=make_word_freq_chart())),
                                dcc.Tab(label="Ownership Treemap", value="tab4",
                                        children=dcc.Graph(id="treemap",
                                                           figure=make_ownership_treemap())),
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
            html.Hr(style={"borderColor": "#ccc", "margin": "16px 0"}),
            html.P(
                "A plot of every public artwork in the Chicago parks, colored by owner. Filter by artist, owner, or park to explore the collection geographically.",
                style={"lineHeight": "1.5"}),
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
                searchable=False,
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
            html.Hr(style={"borderColor": "#ccc", "margin": "16px 0"}),
            html.P(
                "Depicts the count of artworks grouped by park, owner, or artist. Adjust the grouping in the dropdown and top N with the slider to compare how the collections are distributed.",
                style={"lineHeight": "1.5"}),
        ]

    if active_tab == "tab3":
        return [
            html.H2("Top N words"),
            dcc.Slider(
                id="name-topn",
                min=10,
                max=50,
                step=5,
                value=30,
                marks={i: str(i) for i in range(10, 51, 5)},
            ),
            html.Hr(style={"borderColor": "#ccc", "margin": "16px 0"}),
            html.P(
                "The frequency of words appearing in artwork titles. Dominant themes across the collection include: commemorative, community, and figurative.",
                style={"lineHeight": "1.5"}),
        ]

    if active_tab == "tab4":
        return [
            html.P(
                "A hierarchical breakdown of ownership, organized by owner, park, and individual artwork. "
                "Highlights how much of the collection CPD controls versus museums, institutions, and private owners.",
                style={"lineHeight": "1.5"}),
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
    Output("name-freq-chart", "figure"),
    Input("name-topn", "value")
)
def update_name_freq(top_n):
    return make_word_freq_chart(ART_DATA, top_n=top_n or 30)


if __name__ == "__main__":
    app.run(debug=True)