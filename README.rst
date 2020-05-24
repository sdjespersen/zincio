pyzinc: Project Haystack Zinc I/O in Python
===========================================

Overview
--------

`Zinc <https://project-haystack.org/doc/Zinc>`_ is a CSV-like format for
Project Haystack. This project exists solely to make it simple—and *fast!*—to
load Zinc-format strings into a ``Grid``.

Other Python libraries for Zinc exist, notably `hszinc
<https://github.com/widesky/hszinc>`_. So why this library? Basically only one
reason: `performance`_. Note that this does not have feature parity with the
hszinc library, so this comparison is not yet fair.

Please note: This implementation does not claim to adhere to the Zinc spec
yet, and it likely never will; the spec includes support for things like
nested Grids, which completely upend the assumptions of tabular data. This
library sacrifices some completeness for speed.

Example usage
-------------

The API mimics the Pandas API, due to the similarity in use cases.

Say you have the following in ``example.zinc``::

  ver:"3.0" view:"chart" hisStart:2020-05-18T00:00:00-07:00 Los_Angeles hisEnd:2020-05-18T01:15:00-07:00 Los_Angeles hisLimit:10000 dis:"Mon 18-May-2020"
  ts disKey:"ui::timestamp" tz:"Los_Angeles" chartFormat:"ka",v0 id:@p:q01b001:r:0197767d-c51944e4 "Building One VAV1-01 Eff Heat SP" navName:"Eff Heat SP" point his siteRef:@p:q01b001:r:8fc116f8-72c5320c "Building One" equipRef:@p:q01b001:r:b78a8dcc-828caa1b "Building One VAV1-01" curVal:65.972°F curStatus:"ok" kind:"Number" unit:"°F" tz:"Los_Angeles" sp temp cur haystackPoint air effective heating
  2020-05-17T23:47:08-07:00 Los_Angeles,
  2020-05-17T23:55:00-07:00 Los_Angeles,68.553°F
  2020-05-18T00:00:00-07:00 Los_Angeles,68.554°F
  2020-05-18T00:05:00-07:00 Los_Angeles,69.723°F
  2020-05-18T01:13:09-07:00 Los_Angeles,

you can load it with

.. code:: python

  import pyzinc

  grid = pyzinc.read_zinc("example.zinc")

Which returns a ``Grid``. This is basically a glorified ``pandas.DataFrame``,
with some extra metadata about the grid (e.g. version info) and the columns
(e.g. units, current values, etc.). To access the tabular data as a `pandas`
type, use

.. code:: python

  grid.data()

which returns a ``pandas.Series`` if there is only one column of data and a
``pandas.DataFrame`` otherwise. If you want a single column returned as a frame, use

.. code:: python

  grid.data(squeeze=False)

The grid can be written to a file or a string with

.. code:: python

  grid.to_zinc()  # returns a string
  grid.to_zinc(output_file)  # writes to `output_file`

Performance
-----------

Run ``bench/benchmark.py`` for these numbers.

On a 59KB Zinc Grid with 16 columns and 287 rows:

* ``pyzinc.read_zinc`` takes 45ms
* ``hszinc.parse`` takes about 7.84 seconds

On a 107KB Zinc Grid with 32 columns and 287 rows:

* ``pyzinc.read_zinc`` takes 88ms
* ``hszinc.parse`` takes about 15.2 seconds

In other words, ``pyzinc.read_zinc`` is about 200x faster than
``hszinc.parse``, mostly thanks to using ``pandas.read_csv`` under the hood.

On a larger 11MB Grid with 2002 columns and 849 rows, ``pyzinc.read_zinc``
took 37.6 seconds, and ``hszinc.parse`` did not terminate within 10 minutes.
