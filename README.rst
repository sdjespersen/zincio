===============================================
zincio: Read/write Project Haystack Zinc Format
===============================================

Overview
========

`Zinc <https://project-haystack.org/doc/Zinc>`_ is a CSV-like format for
Project Haystack. This library makes it easy—and fast—to read Zinc to a
``Grid``, to write a ``Grid`` back to Zinc, or to obtain a
``pandas.DataFrame`` from a ``Grid``.

Other Python libraries for Zinc exist, notably `hszinc
<https://github.com/widesky/hszinc>`_. So why this library? Basically only one
reason: `performance`_. However, zincio does not have feature parity with
hszinc library, so this comparison is not yet fair.

.. note::

   This implementation does not claim to adhere to the `Zinc spec
   <https://project-haystack.org/doc/Zinc>`_ yet, and it likely never will. In
   particular, the spec includes support for things like nested ``Grid``\ s;
   this library does not. Nested ``Grid``\ s completely upend the assumption
   that your data is tabular. Is your data tabular? Then this should work
   fine.


Getting Started
===============

Install ``zincio`` from source (``pip install [-e] .``).

.. code:: python

  import zincio

Consider the file ``examples/example.zinc`` (available in the repo)::

  ver:"3.0" view:"chart" hisStart:2020-05-18T00:00:00-07:00 Los_Angeles hisEnd:2020-05-18T01:15:00-07:00 Los_Angeles hisLimit:10000 dis:"Mon 18-May-2020"
  ts disKey:"ui::timestamp" tz:"Los_Angeles" chartFormat:"ka",v0 id:@p:q01b001:r:0197767d-c51944e4 "Building One VAV1-01 Eff Heat SP" navName:"Eff Heat SP" point his siteRef:@p:q01b001:r:8fc116f8-72c5320c "Building One" equipRef:@p:q01b001:r:b78a8dcc-828caa1b "Building One VAV1-01" curVal:65.972°F curStatus:"ok" kind:"Number" unit:"°F" tz:"Los_Angeles" sp temp cur haystackPoint air effective heating
  2020-05-17T23:47:08-07:00 Los_Angeles,
  2020-05-17T23:55:00-07:00 Los_Angeles,68.553°F
  2020-05-18T00:00:00-07:00 Los_Angeles,68.554°F
  2020-05-18T00:05:00-07:00 Los_Angeles,69.723°F
  2020-05-18T01:13:09-07:00 Los_Angeles,

you can load it with

.. code:: python

  grid = zincio.read("examples/example.zinc")

which returns a ``zincio.Grid`` instance. There is also ``zincio.parse(str)``
if you already have a string in memory. Writing the grid to file (or returning
it as a string) is as in Pandas:

.. code:: python

  >>> grid.to_zinc("example_output.zinc")
  >>> print(grid.to_zinc())
  ver:"3.0" view:"chart" hisStart:2020-05-18T00:00:00-07:00 Los_Angeles hisEnd:2020-05-18T01:15:00-07:00 Los_Angeles hisLimit:10000 dis:"Mon 18-May-2020"
  ts disKey:"ui::timestamp" tz:"Los_Angeles" chartFormat:"ka",v0 id:@p:q01b001:r:0197767d-c51944e4 "Building One VAV1-01 Eff Heat SP" navName:"Eff Heat SP" point his siteRef:@p:q01b001:r:8fc116f8-72c5320c "Building One" equipRef:@p:q01b001:r:b78a8dcc-828caa1b "Building One VAV1-01" curVal:65.972°F curStatus:"ok" kind:"Number" unit:"°F" tz:"Los_Angeles" sp temp cur haystackPoint air effective heating
  2020-05-17T23:47:08-07:00 Los_Angeles,
  2020-05-17T23:55:00-07:00 Los_Angeles,68.553°F
  2020-05-18T00:00:00-07:00 Los_Angeles,68.554°F
  2020-05-18T00:05:00-07:00 Los_Angeles,69.723°F
  2020-05-18T01:13:09-07:00 Los_Angeles,


A ``zincio.Grid`` has four primary attributes:

* A ``version`` indicating the version of Zinc used.
* A ``grid_info`` attribute consisting of metadata about the entire ``Grid``.
* A ``column_info`` attribute consisting of metadata about each individual
  column, including, e.g., pertinent tags.
* A ``data`` attribute, which contains the underlying tabular data as a
  ``pandas.DataFrame``.

A common use case is to immediately extract the tabular data from the ``Grid``
as a ``pandas.DataFrame``; you can do this with the ``to_pandas`` method.

Here they are, in action:

  >>> grid.version
  3

  >>> grid.grid_info
  {'view': String(chart), 'hisStart': Datetime(2020-05-18T00:00:00-07:00, "Los_Angeles"), 'hisEnd': Datetime(2020-05-18T01:15:00-07:00, "Los_Angeles"), 'hisLimit': Number(10000.0, "None"), 'dis': String(Mon 18-May-2020)}

  >>> grid.column_info
  {'ts': {'disKey': String(ui::timestamp), 'tz': String(Los_Angeles), 'chartFormat': String(ka)}, 'v0': {'id': Ref(p:q01b001:r:0197767d-c51944e4, "Building One VAV1-01 Eff Heat SP"), 'navName': String(Eff Heat SP), 'point': Marker, 'his': Marker, 'siteRef': Ref(p:q01b001:r:8fc116f8-72c5320c, "Building One"), 'equipRef': Ref(p:q01b001:r:b78a8dcc-828caa1b, "Building One VAV1-01"), 'curVal': Number(65.972, "°F"), 'curStatus': String(ok), 'kind': String(Number), 'unit': String(°F), 'tz': String(Los_Angeles), 'sp': Marker, 'temp': Marker, 'cur': Marker, 'haystackPoint': Marker, 'air': Marker, 'effective': Marker, 'heating': Marker}}

  >>> grid.to_pandas()  # returns a Series since only one column present
  ts
  2020-05-17 23:47:08-07:00       NaN
  2020-05-17 23:55:00-07:00    68.553
  2020-05-18 00:00:00-07:00    68.554
  2020-05-18 00:05:00-07:00    69.723
  2020-05-18 01:13:09-07:00       NaN
  Name: @p:q01b001:r:0197767d-c51944e4 "Building One VAV1-01 Eff Heat SP", dtype: float64

  >>> grid.to_pandas(squeeze=False)  # returns a DataFrame
                             @p:q01b001:r:0197767d-c51944e4 "Building One VAV1-01 Eff Heat SP"
  ts
  2020-05-17 23:47:08-07:00                                                NaN
  2020-05-17 23:55:00-07:00                                             68.553
  2020-05-18 00:00:00-07:00                                             68.554
  2020-05-18 00:05:00-07:00                                             69.723
  2020-05-18 01:13:09-07:00                                                NaN

For more details, see the `API docs <api.html>`_.

Performance
===========

Run ``bench/benchmark.py`` for these numbers.

On a 59KB Zinc Grid with 16 columns and 287 rows (``small_example.zinc``):

* ``zincio.parse`` takes about 0.192 seconds, avg of 20 runs
* ``hszinc.parse`` takes about 7.93 seconds, avg of 5 runs

On a 107KB Zinc Grid with 32 columns and 287 rows (``medium_example.zinc``):

* ``zincio.parse`` takes about 0.325 seconds, avg of 20 runs
* ``hszinc.parse`` takes about 15.3 seconds, avg of 5 runs

In other words, ``zincio.parse`` is about 40-50x faster than
``hszinc.parse``.
