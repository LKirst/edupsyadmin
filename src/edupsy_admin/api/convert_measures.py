#!/usr/bin/env python3
import argparse
from scipy.stats import norm

IQ_MEAN = 100
IQ_SD = 15
T_MEAN = 50
T_SD = 10


def percentile_to_z(percentile):
    z = norm.ppf(percentile / 100)
    return z


def percentile_to_t(percentile):
    z = percentile_to_z(percentile)
    t = z_to_normaldist(z, T_MEAN, T_SD)
    return t


def z_to_normaldist(z, mean, sd):
    converted_val = mean + z * sd
    return converted_val


def normaldist_to_z(value, mean, sd):
    z = (value - mean) / sd
    return z


def iq_to_z(iq):
    z = normaldist_to_z(iq, IQ_MEAN, IQ_SD)
    return z


def t_to_z(t):
    z = normaldist_to_z(t, T_MEAN, T_SD)
    return z


def iq_to_t(iq):
    t = ((iq - 100) / 15) * 10 + 50
    return t


if __name__ == "__main__":

    formats = ["t", "z", "iq", "percentile"]

    parser = argparse.ArgumentParser()
    parser.add_argument("f", type=str, help="from", choices=formats)
    parser.add_argument("t", type=str, help="to", choices=formats)
    parser.add_argument("value", type=float)
    parser.add_argument("--round", type=int, default=2)
    args = parser.parse_args()

    if (args.f == "iq") and (args.t == "t"):
        print(round(iq_to_t(args.value), args.round))
    elif (args.f == "iq") and (args.t == "z"):
        print(round(iq_to_z(args.value), args.round))
    elif (args.f == "percentile") and (args.t == "t"):
        print(round(percentile_to_t(args.value), args.round))
    else:
        print("The conversion you requested is not yet implemented")
