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

## CoReManager

```python
class CoReManager()
```

Manage easily usual tasks of CoRe-Watpy.

Ad-hoc manager to automate and make easier usual tasks in Watpy.

Attributes
----------
`cdb` : watpy.coredb.coredb.CoRe_db
Instance of CoRe_db from which everything is managed.

`db_path` : Path
Folder where is or will be stored CoRe database.
Refer to 'watpy.coredb.coredb.CoRe_db' for more details.

`eos` : set
All EOS found available.

`metadata` : pd.DataFrame
Metadata from all simulations in 'cdb' collected in a single DF.

`downloaded` : dict
3-Level dictionary containing the path to existing strains (saved as
TXT files), their eccentricity and radius of extraction.
Tree-format:
```python
txt_files[simkey][run] = {
        'file': 'path/to/file.txt',
        'eccentricity': ecc,
        'r_extraction': rext
    }
```
ONLY 1 RUN PER SIMULATION FOR NOW
