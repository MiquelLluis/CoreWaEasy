"""CoRe Watpy made easy.

Includes the class CoReManager which centralices all common operations
in watpy.

Author: Miquel Llorens
E-mail: miquel.llorens@uv.es
Last updated: 2023-10-24

"""
from pathlib import Path
from shutil import rmtree

import numpy as np
import pandas as pd
from tqdm.auto import tqdm
import watpy


class CoReManager:
    """Manage easily usual tasks of CoRe-Watpy.

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

    """
    fields_float = [
        'id_mass',
        'id_rest_mass',
        'id_mass_ratio',
        'id_ADM_mass',
        'id_ADM_angularmomentum',
        'id_gw_frequency_Hz',
        'id_gw_frequency_Momega22',
        'id_kappa2T',
        'id_Lambda',
        'id_eccentricity',
        'id_mass_starA',
        'id_rest_mass_starA',
        'id_mass_starB',
        'id_rest_mass_starB'
    ]
    header_gw_txt = "u/M:0 Reh/M:1 Imh/M:2 Redh/M:3 Imdh/M:4 Momega:5 A/M:6 phi:7 t:8"

    def __init__(self, db_path):
        """Init.

        Parameters
        ----------
        db_path : str
            Folder where is or will be stored CoRe database.
            Refer to 'watpy.coredb.coredb.CoRe_db' for more details.

        """
        self.db_path = Path(db_path)
        self.cdb = watpy.coredb.coredb.CoRe_db(db_path)
        self.metadata = self._gen_metadata_dataframe()
        self.eos = set(self.metadata['id_eos'])
        self.downloaded = self._look_for_existing_strains()

    def __repr__(self):
        return str(self.metadata)

    def __getitem__(self, i):
        return self.metadata[i]

    def __len__(self):
        return len(self.metadata)

    def show(self, key, to_float=False, to_file=None):
        return self.cdb.idb.show(key, to_float=False, to_file=None)

    def filter_by(self, key, value):
        return self.metadata[self.metadata[key] == value]

    def filter_multiple(self, filters):
        md = self.metadata.copy()
        for k, v in filters:
            md = md[md[k] == v]

        return md

    def count_runs(self, filters=[]):
        """Count total number of runs in the database.

        Parameters
        ----------
        filters : list of lists
            Format: [[key0, value0], [key1, value1], ...]

        """
        md = self.filter_multiple(filters)
        counts = 0
        for ind in md.index:
            runs = md.loc[ind].available_runs
            if runs is not None:
                counts += len(runs.split(', '))

        return counts

    def download_strains(self, simkeys, keep_h5=False, overwrite=False,
                         prot='https', lfs=False, verbose=True):
        """Download ONLY the optimum strains rh_22.

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

        """
        for skey in tqdm(simkeys):
            if (not overwrite) and (skey in self.downloaded):
                if verbose: print(f"{skey} already downloaded, skipping.")
                continue

            self.cdb.sync(dbkeys=[skey], prot=prot, lfs=lfs, verbose=False)

            # Get the gw data with lowest eccentricity and at the highest 'r'
            # of extraction.
            runkey, ecc = self.get_runkey_lowest_eccentricity(skey)
            run = self.cdb.sim[skey].run[runkey]
            data = run.data.read_dset()['rh_22']
            rext_key, rext = self._get_highest_r_extraction_(data)
            gw_data = data[rext_key]

            # Save gw data as TXT.
            ofile = Path(run.path) / f'Rh_l2_m2_r{rext:05d}.txt'
            np.savetxt(ofile, gw_data, header=self.header_gw_txt)

            # Update download database.
            self.downloaded[skey] = {}  # ONLY 1 RUN PER SIM FOR NOW
            self.downloaded[skey][runkey] = {
                'file': ofile,
                'eccentricity': ecc,
                'r_extraction': rext
            }

            if not keep_h5: self._clean_h5_data(skey)
            if verbose: print(f"{skey} downloaded.")

    def load_sim(self, skey):
        """Load a previously downloaded gw simulation."""
        
        meta_sim = self.downloaded[skey]
        file = next(iter(meta_sim.values()))['file']
        gw_data = np.loadtxt(file)

        return gw_data

    def get_runkey_lowest_eccentricity(self, skey):
        """Find the run with the lowest eccentricity for a given simulation.

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

        """
        runs = self.cdb.sim[skey].run.copy()
        run_key = 'R01'
        ecc = self.cast_to_float(runs.pop('R01').md.data['id_eccentricity'])

        if np.isnan(ecc):
            return run_key, ecc

        # Look for the minimum eccentricity, or the first one to be NAN.
        for rkey, run in runs.items():
            ecc_i = self.cast_to_float(run.md.data['id_eccentricity'])
            if ecc_i < ecc:
                run_key = rkey
                ecc = ecc_i
            elif np.isnan(ecc_i):
                run_key = rkey
                ecc = ecc_i
                break

        return run_key, ecc

    @staticmethod
    def cast_to_float(string):
        """Cast a string to float, considering '' also a NaN."""

        if string in ['', None]:
            n = np.nan
        else:
            n = float(string)

        return n

    def _clean_h5_data(self, skey):
        """Remove HDF5 files from a downloaded 'skey' simulation.

        Parameters
        ----------
        skey : str
            Simulation key.

        """
        root = Path(self.cdb.sim[skey].path)
        # Remove HDF5 files.
        files = root.glob('*/*.h5')
        for file in files:
            file.unlink()
        # Remove .git folder.
        folder = root / '.git'
        rmtree(folder)

    def _gen_metadata_dataframe(self):
        idb = self.cdb.idb
        key_list = idb.dbkeys
        metalist = [core_md.data for core_md in idb.index]
        md = pd.DataFrame(metalist, index=key_list)
        # Convert data types of the selected columns:
        for field in self.fields_float:
            mask = (md[field] == 'NAN') | (md[field] == '')
            md[field].values[mask] = np.nan
            md[field] = md[field].astype(float)

        return md

    def _get_highest_r_extraction_(self, extractions):
        """Return the key and value of 'r' of the gw with the highest 'r'.

        It also includes the case when the value of 'r' in the data is Inf
        instead of a number.

        Parameters
        ----------
        extractions : dict
            Channel 'rh_22' returned by CoRe_h5.read_dset().

        """
        rext_key = max(extractions.keys())
        if 'Inf' in rext_key:
            rext = 99999  # Highest number with 5 figures, to represent infinity.
        else:
            rext = int(rext_key[-9:-4])

        return rext_key, rext

    def _look_for_existing_strains(self):
        """Strains that were already extracted from CoRe's HDF5 files.

        Save their paths, alongside the eccentricity and radius of extraction,
        in a dictionary tree by simulation key and run.

        Returns
        -------
        txt_files : dict
            3-Level dictionary containing the path to existing strains
            (extracted as TXT files), their eccentricity and radius of
            extraction. Tree-format:
                txt_files[simkey][run] = {
                    'file': 'path/to/file.txt',
                    'eccentricity': ecc,
                    'r_extraction': rext
                }

        """
        txt_files = {}
        for file in self.db_path.rglob('Rh*.txt'):
            key = file.parts[-3].replace('_', ':')
            run = file.parts[-2]
            ecc = self._read_eccentricity(file.parent/'metadata.txt')
            rext = int(file.stem[-5:])
            
            if key not in txt_files:
                txt_files[key] = {}
            
            # If there are multiple files of the same sim and run, only keep
            # the highest extraction point available.
            elif run in txt_files[key]:
                r0 = int(txt_files[key][run]['file'].stem[-5:])
                if rext < r0:
                    continue

            txt_files[key][run] = {
                'file': file,
                'eccentricity': ecc,
                'r_extraction': rext
            }

        return txt_files

    def _read_eccentricity(self, file):
        """Get the value of eccentricity from a metadata file."""

        with open(file) as f:
            for line in f:
                if 'id_eccentricity' in line:
                    break
            else:
                raise EOFError("no value of eccentricity found in the file")
        ecc_txt = line.split()[-1]
        try:
            ecc = float(ecc_txt)
        except ValueError:
            ecc = np.nan

        return ecc

        
