# coding: utf-8
import io
import numpy as np  # type: ignore
import pandas as pd  # type: ignore
import pytest  # type: ignore
import pyzinc

from collections import OrderedDict
from pandas.api.types import CategoricalDtype  # type: ignore
from pathlib import Path


def get_abspath(relpath):
    return Path(__file__).parent / relpath


FULL_GRID_FILE = get_abspath("full_grid.zinc")
SINGLE_SERIES_FILE = get_abspath("single_series_grid.zinc")
HISREAD_SERIES_FILE = get_abspath("hisread_series.zinc")


def assert_grid_equal(a, b):
    assert a.grid_info == b.grid_info
    assert a.column_info == b.column_info
    pd.testing.assert_frame_equal(a.data(squeeze=False), b._data)


def test_read_zinc_grid():
    expected_grid_info = OrderedDict(
        ver="3.0",
        view="chart",
        hisStart=pyzinc.Datetime(
            "2020-05-18T00:00:00-07:00", tz="Los_Angeles"),
        hisEnd=pyzinc.Datetime(
            "2020-05-18T01:15:00-07:00", tz="Los_Angeles"),
        hisLimit=10000,
        dis="Mon 18-May-2020")
    expected_column_info = OrderedDict(
        ts=OrderedDict(
            disKey='ui::timestamp',
            tz='Los_Angeles',
            chartFormat='ka',
        ),
        v0=OrderedDict(
            id=pyzinc.Ref('p:q01b001:r:0197767d-c51944e4',
                          'Building One VAV1-01 Eff Heat SP'),
            navName='Eff Heat SP',
            point=pyzinc.MARKER,
            his=pyzinc.MARKER,
            siteRef=pyzinc.Ref(
                'p:q01b001:r:8fc116f8-72c5320c', 'Building One'),
            equipRef=pyzinc.Ref(
                'p:q01b001:r:b78a8dcc-828caa1b', 'Building One VAV1-01'),
            curVal=pyzinc.Quantity(65.972, '°F'),
            curStatus='ok',
            kind='Number',
            unit='°F',
            tz='Los_Angeles',
            sp=pyzinc.MARKER,
            temp=pyzinc.MARKER,
            cur=pyzinc.MARKER,
            haystackPoint=pyzinc.MARKER,
            air=pyzinc.MARKER,
            effective=pyzinc.MARKER,
            heating=pyzinc.MARKER
        ),
        v1=OrderedDict(
            id=pyzinc.Ref('p:q01b001:r:e69a7401-f4b340ff',
                          'Building One VAV1-01 Eff Occupancy'),
            navName='Eff Occupancy',
            point=pyzinc.MARKER,
            his=pyzinc.MARKER,
            siteRef=pyzinc.Ref(
                'p:q01b001:r:8fc116f8-72c5320c', 'Building One'),
            equipRef=pyzinc.Ref(
                'p:q01b001:r:b78a8dcc-828caa1b', 'Building One VAV1-01'),
            curVal='Occupied',
            curStatus='ok',
            kind='Str',
            tz='Los_Angeles',
            sensor=pyzinc.MARKER,
            cur=pyzinc.MARKER,
            haystackPoint=pyzinc.MARKER,
            hisCollectCov=pyzinc.MARKER,
            enum='Nul,Occupied,Unoccupied,Bypass,Standby',
            effective=pyzinc.MARKER,
            occupied=pyzinc.MARKER,
        ),
        v2=OrderedDict(
            id=pyzinc.Ref('p:q01b001:r:dcfe87d9-cd034388',
                          'Building One VAV1-01 Damper Pos'),
            navName='Damper Pos',
            point=pyzinc.MARKER,
            his=pyzinc.MARKER,
            siteRef=pyzinc.Ref(
                'p:q01b001:r:8fc116f8-72c5320c', 'Building One'),
            equipRef=pyzinc.Ref(
                'p:q01b001:r:b78a8dcc-828caa1b', 'Building One VAV1-01'),
            curVal=pyzinc.Quantity(41.5, '%'),
            curStatus='ok',
            kind='Number',
            unit='%',
            tz='Los_Angeles',
            sensor=pyzinc.MARKER,
            cur=pyzinc.MARKER,
            damper=pyzinc.MARKER,
            precision=1.0,
            haystackPoint=pyzinc.MARKER,
            air=pyzinc.MARKER
        ),
        v3=OrderedDict(
            id=pyzinc.Ref('p:q01b001:r:8fab195e-58ffca99',
                          'Building One VAV1-01 Occ Heat SP Offset'),
            navName='Occ Heat SP Offset',
            point=pyzinc.MARKER,
            his=pyzinc.MARKER,
            siteRef=pyzinc.Ref(
                'p:q01b001:r:8fc116f8-72c5320c', 'Building One'),
            equipRef=pyzinc.Ref(
                'p:q01b001:r:b78a8dcc-828caa1b', 'Building One VAV1-01'),
            curVal=pyzinc.Quantity(-2.394, '°C'),
            curStatus='ok',
            kind='Number',
            unit='°C',
            tz='Los_Angeles',
            sp=pyzinc.MARKER,
            temp=pyzinc.MARKER,
            cur=pyzinc.MARKER,
            air=pyzinc.MARKER,
            occ=pyzinc.MARKER,
            writable=pyzinc.MARKER,
            writeStatus='unknown',
            zone=pyzinc.MARKER,
            hisCollectInterval='5min',
            heating=pyzinc.MARKER,
            offset=pyzinc.MARKER,
            writeLevel=8.0,
            haystackPoint=pyzinc.MARKER,
            writeVal=pyzinc.Quantity(-10.0, '°C'),
            actions=('ver:\\"3.0\\"\\ndis,expr\\n\\"Override\\",'
                        '\\"pointOverride(\\$self, \\$val, \\$duration)\\"\\n'
                        '\\"Auto\\",\\"pointAuto(\\$self)\\"\\n')
        ),
        v4=OrderedDict(
            id=pyzinc.Ref('p:q01b001:r:260ce2bb-2ef5065f',
                          'Building One VAV1-01 Air Flow'),
            navName='Air Flow',
            point=pyzinc.MARKER,
            his=pyzinc.MARKER,
            siteRef=pyzinc.Ref(
                'p:q01b001:r:8fc116f8-72c5320c', 'Building One'),
            equipRef=pyzinc.Ref(
                'p:q01b001:r:b78a8dcc-828caa1b', 'Building One VAV1-01'),
            curVal=pyzinc.Quantity(117.6611, 'cfm'),
            curStatus='ok',
            kind='Number',
            unit='cfm',
            tz='Los_Angeles',
            sensor=pyzinc.MARKER,
            cur=pyzinc.MARKER,
        )
    )
    expected_index = pd.DatetimeIndex(
        [
            pd.to_datetime('2020-05-17T23:47:08-07:00'),
            pd.to_datetime('2020-05-17T23:55:00-07:00'),
            pd.to_datetime('2020-05-18T00:00:00-07:00'),
            pd.to_datetime('2020-05-18T00:05:00-07:00'),
            pd.to_datetime('2020-05-18T01:13:09-07:00'),
        ],
        name='ts')
    expected_dataframe = pd.DataFrame(
        index=expected_index,
        data={
            ('@p:q01b001:r:0197767d-c51944e4 '
             '"Building One VAV1-01 Eff Heat SP"'): [
                np.nan, 68.553, 68.554, 69.723, np.nan,
            ],
            ('@p:q01b001:r:e69a7401-f4b340ff '
             '"Building One VAV1-01 Eff Occupancy"'): pd.Series(
                ['Occupied', '', '', '', 'Unoccupied'],
                index=expected_index,
                dtype=CategoricalDtype(categories=[
                    'Nul', 'Occupied', 'Unoccupied', 'Bypass', 'Standby'])
            ),
            ('@p:q01b001:r:dcfe87d9-cd034388 '
             '"Building One VAV1-01 Damper Pos"'): [np.nan, 3, 7, 18, np.nan],
            ('@p:q01b001:r:8fab195e-58ffca99 '
             '"Building One VAV1-01 Occ Heat SP Offset"'): [
                np.nan, -1.984, -2.203, 5.471, np.nan,
            ],
            '@p:q01b001:r:260ce2bb-2ef5065f "Building One VAV1-01 Air Flow"': [
                np.nan, 118.65, 62.0, np.nan, np.nan,
            ],
        })
    actual = pyzinc.read_zinc(FULL_GRID_FILE)
    expected = pyzinc.Grid(
        grid_info=expected_grid_info,
        column_info=expected_column_info,
        data=expected_dataframe)
    assert_grid_equal(actual, expected)


def test_read_zinc_single_series():
    expected_grid_info = OrderedDict(
        ver="3.0",
        view="chart",
        hisStart=pyzinc.Datetime(
            "2020-05-18T00:00:00-07:00", tz="Los_Angeles"),
        hisEnd=pyzinc.Datetime(
            "2020-05-18T01:15:00-07:00", tz="Los_Angeles"),
        hisLimit=10000,
        dis="Mon 18-May-2020")
    expected_column_info = OrderedDict(
        ts=OrderedDict(
            disKey='ui::timestamp',
            tz='Los_Angeles',
            chartFormat='ka',
        ),
        v0=OrderedDict(
            id=pyzinc.Ref('p:q01b001:r:0197767d-c51944e4',
                          'Building One VAV1-01 Eff Heat SP'),
            navName='Eff Heat SP',
            point=pyzinc.MARKER,
            his=pyzinc.MARKER,
            siteRef=pyzinc.Ref(
                'p:q01b001:r:8fc116f8-72c5320c', 'Building One'),
            equipRef=pyzinc.Ref(
                'p:q01b001:r:b78a8dcc-828caa1b', 'Building One VAV1-01'),
            curVal=pyzinc.Quantity(65.972, '°F'),
            curStatus='ok',
            kind='Number',
            unit='°F',
            tz='Los_Angeles',
            sp=pyzinc.MARKER,
            temp=pyzinc.MARKER,
            cur=pyzinc.MARKER,
            haystackPoint=pyzinc.MARKER,
            air=pyzinc.MARKER,
            effective=pyzinc.MARKER,
            heating=pyzinc.MARKER
        ),
    )
    dname = '@p:q01b001:r:0197767d-c51944e4 "Building One VAV1-01 Eff Heat SP"'
    expected_data = pd.DataFrame(
        data={dname: [np.nan, 68.553, 68.554, 69.723, np.nan]},
        index=pd.DatetimeIndex(
            [
                pd.to_datetime('2020-05-17T23:47:08-07:00'),
                pd.to_datetime('2020-05-17T23:55:00-07:00'),
                pd.to_datetime('2020-05-18T00:00:00-07:00'),
                pd.to_datetime('2020-05-18T00:05:00-07:00'),
                pd.to_datetime('2020-05-18T01:13:09-07:00'),
            ],
            name='ts',
        ))
    expected = pyzinc.Grid(
        grid_info=expected_grid_info,
        column_info=expected_column_info,
        data=expected_data)
    actual = pyzinc.read_zinc(SINGLE_SERIES_FILE)
    assert_grid_equal(actual, expected)
    pd.testing.assert_series_equal(actual.data(), expected._data[dname])


def test_read_zinc_deficient_column_info():
    expected_grid_info = OrderedDict(
        ver="3.0",
        id=pyzinc.Ref("p:q01b001:r:20aad139-beff4e8c",
                      "Building One VAV1-01 DA Temp"),
        hisStart=pyzinc.Datetime(
            "2020-04-01T00:00:00-07:00", tz="Los_Angeles"),
        hisEnd=pyzinc.Datetime(
            "2020-04-02T00:00:00-07:00", tz="Los_Angeles"))
    expected_column_info = OrderedDict(ts={}, val={})
    expected_data = pd.DataFrame(
        data={'val': [66.092, 66.002, 65.930]},
        index=pd.DatetimeIndex(
            [
                pd.to_datetime('2020-04-01T00:00:00-07:00'),
                pd.to_datetime('2020-04-01T00:05:00-07:00'),
                pd.to_datetime('2020-04-01T00:10:00-07:00'),
            ],
            name='ts',
        ))
    expected = pyzinc.Grid(
        grid_info=expected_grid_info,
        column_info=expected_column_info,
        data=expected_data)
    actual = pyzinc.read_zinc(HISREAD_SERIES_FILE)
    assert_grid_equal(actual, expected)
    pd.testing.assert_series_equal(actual.data(), expected._data['val'])


def test_read_zinc_malformed_grid():
    grid = 'this is not a legal grid'
    with pytest.raises(pyzinc.ZincParseException):
        pyzinc.read_zinc(io.StringIO(grid))


def test_read_zinc_error_grid():
    err_grid = (
        'ver:"3.0" errType:"sys::NullErr" err '
        'errTrace:"sys::NullErr: java.lang.NullPointerException\n" '
        'dis:"sys::NullErr: java.lang.NullPointerException"\n'
        'empty')
    with pytest.raises(pyzinc.ZincErrorGridException):
        pyzinc.read_zinc(io.StringIO(err_grid))


def test_read_zinc_stringio_same_as_file():
    expected = pyzinc.read_zinc(FULL_GRID_FILE)
    with open(FULL_GRID_FILE, encoding='utf-8') as f:
        raw = f.read()
    actual = pyzinc.read_zinc(io.StringIO(raw))
    assert_grid_equal(actual, expected)


def test_grid_to_zinc_string():
    with open(SINGLE_SERIES_FILE, encoding='utf-8') as f:
        expected = f.read()
    actual = pyzinc.read_zinc(SINGLE_SERIES_FILE).to_zinc()
    assert actual == expected


def test_grid_to_zinc_file(tmp_path):
    with open(SINGLE_SERIES_FILE, encoding='utf-8') as f:
        expected = f.read()
    output_file = tmp_path / "output.zinc"
    pyzinc.read_zinc(SINGLE_SERIES_FILE).to_zinc(output_file)
    with open(output_file, encoding="utf-8") as f:
        actual = f.read()
    assert actual == expected
