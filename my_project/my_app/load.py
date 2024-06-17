from django.contrib.gis.utils import LayerMapping
from my_app.models import WorldBorder
world_mapping = {
    "fips": "FIPS",
    "iso2": "ISO2",
    "iso3": "ISO3",
    "un": "UN",
    "name": "NAME",
    "area": "AREA",
    "pop2005": "POP2005",
    "region": "REGION",
    "subregion": "SUBREGION",
    "lon": "LON",
    "lat": "LAT",
    "mpoly": "MULTIPOLYGON",
}
world_shp = "D:/work/MPM/T231/data/TM_WORLD_BORDERS-0.3/TM_WORLD_BORDERS-0.3.shp"
def run(verbose=True):
    lm = LayerMapping(WorldBorder, world_shp, world_mapping, transform=False)
    lm.save(strict=True, verbose=verbose)