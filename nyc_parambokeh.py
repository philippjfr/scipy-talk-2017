import holoviews as hv
import geoviews as gv
import param, parambokeh
import pandas as pd
import dask.dataframe as dd

from colorcet import cm
from bokeh.models import WMTSTileSource
from holoviews.operation.datashader import datashade
from holoviews.streams import RangeXY, PlotSize

hv.extension('bokeh')

ddf = dd.read_parquet('./data/nyc_taxi.parq/').persist()

tiles = gv.WMTS(WMTSTileSource(url='https://server.arcgisonline.com/ArcGIS/rest/services/'
                                   'World_Imagery/MapServer/tile/{Z}/{Y}/{X}.jpg'))
tile_options = dict(width=800,height=475,xaxis=None,yaxis=None,bgcolor='black',show_grid=False)

passenger_counts = sorted(ddf.passenger_count.unique().compute().tolist())

class NYCTaxiExplorer(hv.streams.Stream):
    alpha       = param.Magnitude(default=0.75, doc="Alpha value for the map opacity")
    colormap    = param.ObjectSelector(default=cm["fire"], objects=cm.values())
    plot        = param.ObjectSelector(default="pickup",   objects=["pickup","dropoff"])
    passengers  = param.ObjectSelector(default=1,          objects=passenger_counts)
    output      = parambokeh.view.Plot()

    def __init__(self, **params):
        super(NYCTaxiExplorer, self).__init__(**params)
        self.output = hv.DynamicMap(self.make_view, streams=[self, RangeXY()])

    def make_view(self, x_range, y_range, alpha, colormap, plot, passengers, **kwargs):
        map_tiles = tiles(style=dict(alpha=alpha), plot=tile_options)
        df_filt = ddf[ddf.passenger_count==passengers]
        points = hv.Points(df_filt, kdims=[plot+'_x', plot+'_y'])
        taxi_trips = datashade(points, x_sampling=1, y_sampling=1, cmap=colormap,
                               dynamic=False, x_range=x_range, y_range=y_range)
        return map_tiles * taxi_trips

selector = NYCTaxiExplorer(name="")
doc = parambokeh.Widgets(selector, view_position='right', callback=selector.event, mode='server')
doc.title = 'NYC Taxi Explorer'
