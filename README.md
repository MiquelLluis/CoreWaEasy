<a id="corewaeasy"></a>

# corewaeasy

CoRe Watpy made easy.

Includes the class CoReManager which centralices all common operations
in watpy.

---
- Author: Miquel Llorens
- E-mail: miquel.llorens@uv.es
- Last updated: 2023-10-24
---

<a id="corewaeasy.corewaeasy.CoReManager"></a>

## CoReManager Objects

```python
class CoReManager()
```

Manage easily usual tasks of CoRe-Watpy.

Ad-hoc manager to automate and make easier usual tasks in Watpy.

Attributes
----------
cdb : watpy.coredb.coredb.CoRe_db
    Instance of CoRe_db from which everything is managed.

db_path : Path
    Folder where is or will be stored CoRe database.
    Refer to 'watpy.coredb.coredb.CoRe_db' for more details.

eos : set
    All EOS found available.

metadata : pd.DataFrame
    Metadata from all simulations in 'cdb' collected in a single DF.

downloaded : dict
    3-Level dictionary containing the path to existing strains (saved as
    TXT files), their eccentricity and radius of extraction.
    Tree-format:
        txt_files[simkey][run] = {
            'file': 'path/to/file.txt',
            'eccentricity': ecc,
            'r_extraction': rext
        }
    NOTE: ONLY 1 RUN PER SIMULATION FOR NOW

<a id="corewaeasy.corewaeasy.CoReManager.__init__"></a>

#### \_\_init\_\_

```python
def __init__(db_path)
```

Init.

Parameters
----------
db_path : str
    Folder where is or will be stored CoRe database.
    Refer to 'watpy.coredb.coredb.CoRe_db' for more details.

<a id="corewaeasy.corewaeasy.CoReManager.count_runs"></a>

#### count\_runs

```python
def count_runs(filters=[])
```

Count total number of runs in the database.

Parameters
----------
filters : list of lists
    Format: [[key0, value0], [key1, value1], ...]

<a id="corewaeasy.corewaeasy.CoReManager.download_strains"></a>

#### download\_strains

```python
def download_strains(simkeys, keep_h5=False, overwrite=False, prot='https', lfs=False, verbose=True)
```

Download ONLY the optimum strains rh_22.

Downloads each simulation, keeps the strains with the lowest
eccentricity and highest extraction point 'r' in a TXT file, updates
the database 'self.downloaded', and (optional) removes the original
HDF5 file from CoRe to free up space.

Parameters
----------
simkeys : list
    List of simulation keys ('db_keys' in watpy) to download.

keep_h5 : bool
    If False (default) removes the HDF5 file downloaded by watpy.

overwrite : bool
    If False (default) and a certain simulation in 'simkeys' is already
    present in 'self.downloaded', skip it. Otherwise downloads
    everything again.

verbose : bool
    If True (default), print which simulations are downloaded and which
    are skipped.

prot, lfs :
    Refer to 'watpy.coredb.coredb.CoRe_db.sync'.

<a id="corewaeasy.corewaeasy.CoReManager.load_sim"></a>

#### load\_sim

```python
def load_sim(skey)
```

Load a previously downloaded gw simulation.

<a id="corewaeasy.corewaeasy.CoReManager.get_runkey_lowest_eccentricity"></a>

#### get\_runkey\_lowest\_eccentricity

```python
def get_runkey_lowest_eccentricity(skey)
```

Find the run with the lowest eccentricity for a given simulation.

Return the key of the run and the value of its eccentricity for which
this parameter is the lowest among all runs of the 'skey' simulation.

If a simulation has multiple runs with the same eccentricity
(typically all values set to 0 or NAN) it will pick the first run in
the list.

If there are one or more runs with eccentricity = NAN, the first one
will be returned.

Parameters
----------
skey : str
    Key (database_key) of the simulation.

Returns
-------
run_key : str
    Key of the run.
ecc : float
    Eccentricity of the run.

<a id="corewaeasy.corewaeasy.CoReManager.cast_to_float"></a>

#### cast\_to\_float

```python
@staticmethod
def cast_to_float(string)
```

Cast a string to float, considering '' also a NaN.

<a id="corewaeasy.corewaeasy.CoReManager._get_highest_r_extraction_"></a>

#### \_get\_highest\_r\_extraction\_

```python
def _get_highest_r_extraction_(extractions)
```

Return the key and value of 'r' of the gw with the highest 'r'.

It also includes the case when the value of 'r' in the data is Inf
instead of a number.

Parameters
----------
extractions : dict
    Channel 'rh_22' returned by CoRe_h5.read_dset().

