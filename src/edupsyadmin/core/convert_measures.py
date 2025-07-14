from scipy.stats import norm

IQ_MEAN = 100
IQ_SD = 15
T_MEAN = 50
T_SD = 10


def percentile_to_z(percentile: int) -> float:
    """
    Convert a percentile to a Z-score.

    :param percentile: a percentile
    :return: the Z-score which corresponds to the percentile
    """
    z: float = norm.ppf(percentile / 100)
    return z


def percentile_to_t(percentile: int) -> float:
    """
    Convert a percentile to a t-value.

    :param percentile: a percentile
    :return: the t-value that corresponds to the percentile
    """
    z = percentile_to_z(percentile)
    return z_to_normaldist(z, T_MEAN, T_SD)


def z_to_normaldist(z: float, mean: float, sd: float) -> float:
    """
    Convert a Z-score to a corresponding value from a different normal
    distribution.

    :param z: a Z-score
    :param mean: the mean of the target normal distribution
    :param sd: the standard deveation of the target normal distribution
    :return: the value in the target normal distribution that corresponds to
    the Z-score
    """
    return mean + z * sd


def normaldist_to_z(value: float, mean: float, sd: float) -> float:
    """
    Convert a value of a normal distribution to a Z-score.

    :param value: the value from the normal distribution
    :param mean: the mean of the normal distribution
    :param sd: the standard deviation of the normal distribution
    :return: the Z-score that corresponds to the value from the normal
    distribution
    """
    return (value - mean) / sd


def iq_to_z(iq: float) -> float:
    """
    Convert from IQ to Z-score.

    :param iq: IQ-score
    :return: Z-score
    """
    return normaldist_to_z(iq, IQ_MEAN, IQ_SD)


def t_to_z(t: float) -> float:
    """
    Convert a t-value to a Z-score

    :param t: t-value
    :return: Z-score
    """
    return normaldist_to_z(t, T_MEAN, T_SD)


def iq_to_t(iq: float) -> float:
    """
    Convert an IQ to a Z-score

    :param iq: IQ-score
    :return: Z-score
    """
    return ((iq - 100) / 15) * 10 + 50
