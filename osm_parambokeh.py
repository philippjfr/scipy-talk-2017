import holoviews as hv, geoviews as gv, param, parambokeh, dask.dataframe as dd

from copy import deepcopy
import numpy as np
from colorcet import cm
from bokeh.models import WMTSTileSource
from holoviews.operation.datashader import aggregate, shade
from holoviews.operation import histogram
from holoviews.streams import RangeXY, PlotSize

hv.extension('bokeh')

df = dd.read_parquet('./data/osm-1billion.snappy.parq/').persist()

url='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{Z}/{Y}/{X}.jpg'
tiles = gv.WMTS(WMTSTileSource(url=url))

hv.opts("WMTS [width=800 height=475 xaxis=None yaxis=None bgcolor='black']"
        "Histogram [logy=True] (fill_color='white') {+framewise} VLine (color='black')")

class OSMExplorer(hv.streams.Stream):
    alpha      = param.Magnitude(default=0.75, doc="Alpha value for the map opacity")
    cmap        = param.ObjectSelector(default=cm["fire"], objects=cm.values())
    min_count   = param.Number(default=0, bounds=(0, 100))
    output      = parambokeh.view.Plot()

def filter_count(agg, min_count, **kwargs):
    if min_count:
        agg = deepcopy(agg)
        agg.data.Count.data[agg.data.Count.data<min_count] = 0
    return agg

def hline_fn(min_count, **kwargs): return hv.VLine(min_count)

def tiles_fn(alpha, **kwargs): return tiles.opts(style=dict(alpha=alpha))

explorer = OSMExplorer(name="OpenStreetMap GPS Explorer")

tile = hv.DynamicMap(tiles_fn, streams=[explorer])
agg = aggregate(hv.Points(df))
filtered = hv.util.Dynamic(agg, operation=filter_count, streams=[explorer])
shaded = shade(filtered, streams=[explorer])
hline = hv.DynamicMap(hline_fn, streams=[explorer])
explorer.output = (tile * shaded) << histogram(agg, log=True) * hline

doc = parambokeh.Widgets(explorer, view_position='right', callback=explorer.event, mode='server')
