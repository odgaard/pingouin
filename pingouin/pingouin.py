"""
Main functions
"""
import numpy as np
from scipy import stats
from six import string_types
import pandas as pd


__all__ = ["convert_effsize", "compute_effsize", "compute_effsize_from_T"]


# SUB-FUNCTIONS
def _check_data(dv=None, group=None, data=None, x=None, y=None):
    """Extract data from dataframe or numpy arrays"""

    # OPTION A: a pandas DataFrame and column names are specified
    # -----------------------------------------------------------
    if all(v is not None for v in [dv, group, data]):
        for input in [dv, group]:
            if not isinstance(input, string_types):
                err = "Could not interpret input '{}'".format(input)
                raise ValueError(err)
        # Check that data is a pandas dataframe
        if not isinstance(data, pd.DataFrame):
            err = "data must be a pandas dataframe"
            raise ValueError(err)
        # Extract group information
        group_keys = data[group].unique()
        if len(group_keys) != 2:
            err = "group must have exactly two unique values."
            raise ValueError(err)
        # Extract data
        x = data[data[group] == group_keys[0]][dv]
        y = data[data[group] == group_keys[1]][dv]

    # OPTION B: x and y vectors are specified
    # ---------------------------------------
    else:
        if all(v is not None for v in [x, y]):
            for input in [x, y]:
                if not isinstance(input, (list, np.ndarray)):
                    err = "x and y must be np.ndarray"
                    raise ValueError(err)
    nx, ny = len(x), len(y)
    dof = nx + ny - 2
    return x, y, nx, ny, dof


def _check_eftype(eftype):
    """Check validity of eftype"""
    return True if eftype in ['hedges', 'cohen', 'r', 'eta-square', 'odds-ratio', 'AUC'] else False

# MAIN FUNCTIONS
def convert_effsize(ef, input_type, output_type, nx=None, ny=None):
    """Conversion between effect sizes

    Parameters
    ----------
    ef: float
        Original effect size
    input_type: string
        Effect size type of ef
    output_type: string
        Desired effect size type
    nx, ny: int, int
        Length of vector x and y.
        nx and ny are required to convert to Hedges g
    Return
    ------
    ef: float
        Desred converted effect size
    """
    # Check input and output type
    for input in [input_type, output_type]:
        if not _check_eftype(input):
            err = "Could not interpret input '{}'".format(input)
            raise ValueError(err)

    # First convert to Cohen's d
    if input_type == 'r':
        d = (2 * ef) / np.sqrt(1 - ef**2)
    elif input_type == 'cohen':
        d = ef

    # Then convert to the desired output type
    if output_type == 'cohen':
        return d
    elif output_type == 'hedges':
        if all(v is not None for v in [nx, ny]):
            return d * (1 - (3 / (4 * (nx + ny) - 9)))
        else:
            # If shapes of x and y are not known, return cohen's d
            print("You need to pass nx and ny arguments to compute Hedges g. Returning Cohen's d instead")
            return d
    elif output_type == 'r':
        if all(v is not None for v in [nx, ny]):
            a = (nx + ny)**2 / (nx * ny)
        else:
            a = 4
        return d / np.sqrt(d**2 + a)
    elif output_type == 'eta-square':
        return (d/2)**2 / (1 + (d/2)**2)
    elif output_type == 'odds-ratio':
        return np.exp(d * np.pi / np.sqrt(3))
    elif output_type == 'AUC':
        from scipy.stats import norm
        return norm.cdf(d / np.sqrt(2))


def compute_effsize(dv=None, group=None, data=None, x=None, y=None, eftype=None):
    """Compute effect size from pandas dataframe or two numpy arrays

    Case A: pass a DataFrame
        >>>> compute_effsize(dv='Height', 'group='Countries', data=df)
    Case B: pass two vectors
        >>>> x = np.random.normal(loc=172, size=N)
        >>>> y = np.random.normal(loc=175, size=N)
        >>>> compute_effsize(x=x, y=y, data=df)

    Parameters
    ----------
    dv: string
        Column name of dependant variable in data, optional
    group: string
        Column name of group factor in data, optional
    data : DataFrame, optional
        Pandas Dataframe containing columns dv and group
    x, y: vector data, optional
        X and Y are only taken into account if dv, group and data = None
    eftype: desired output effect size, optional

    Return
    ------
    ef: float
        Effect size
    """
    # Check arguments
    if not _check_eftype(eftype):
        err = "Could not interpret input '{}'".format(eftype)
        raise ValueError(err)

    # Extract data
    x, y, nx, ny, dof = _check_data(dv, group, data, x, y)

    # Compute unbiased Cohen's d effect size
    # https://en.wikipedia.org/wiki/Effect_size
    d = (np.mean(x) - np.mean(y)) / np.sqrt(((nx - 1) * np.std(x, ddof=1) ** 2 +
                                             (ny - 1) * np.std(y, ddof=1) ** 2) / dof)

    if eftype == 'cohen':
        return d
    else:
        return convert_effsize(d, input_type='cohen', output_type=eftype, nx=nx, ny=ny)

def compute_effsize_from_T(T, nx, ny, eftype):
    """Compute effect size from pandas dataframe or two numpy arrays

    Parameters
    ----------
    T: float
        T-value
    nx, ny: int
        Length of vector x and y.
    eftype: desired output effect size, optional

    Return
    ------
    ef: float
        Effect size
    """
    if not _check_eftype(eftype):
        err = "Could not interpret input '{}'".format(eftype)
        raise ValueError(err)

    if not isinstance(T, float):
        err = "T-value must be float"
        raise ValueError(err)

    for input in [nx, ny]:
        if not isinstance(input, int):
            err = "nx and ny must be int"
            raise ValueError(err)

    # Compute Cohen d
    d = (T * (nx + ny)) / np.sqrt((nx + ny - 2) * (nx * ny))
    return convert_effsize(d, input_type='cohen', output_type=eftype, nx=nx, ny=ny)