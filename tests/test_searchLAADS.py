import pytest
from searchlaads.searchLAADS import searchLAADS


@pytest.fixture(scope = "module")
def new_domain():

    # server = WSDL.Proxy(wsdl)
    # server.config.dumpSOAPOut = 1
    # server.config.dumpSOAPIn = 1

    #start and end times as datetime obj
    endtime = "201704270000"
    starttime = "201704170000"

    product = "MOD35_L2"
    collection = 6
    north = 2.0
    south = -2.0
    east = -70.0
    west = -74.0
    coordsOrTiles = "coords"
    dayNightBoth = "dbn"

    bbox = [north,south,west,east]

    mod35 = searchLAADS(product, collection, starttime, endtime, bbox, coordsOrTiles, dayNightBoth)
    mod35.searchFiles()

    return mod35


def test_estimateHDDspace(new_domain):
    size = new_domain.estimateHDDspace(nsamples= 10)
    assert type(size) == float


