import re


def _replace_config_bytes(output):
    config_bytes_pattern = re.compile(r"^Current configuration : \d+ bytes$", flags=re.M | re.I)
    output = re.sub(config_bytes_pattern, "Current configuration : CONFIG_BYTES", output)
    return output


def _replace_timestamps(output):
    datetime_pattern = re.compile(
        r"\d+:\d+:\d+\d+\s+[a-z]{3}\s+(mon|tue|wed|thu|fri|sat|sun)\s+(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\s+\d+\s+\d+",
        flags=re.M | re.I,
    )
    output = re.sub(datetime_pattern, "TIME_STAMP_REPLACED", output)
    return output


def _replace_configured_by(output):
    configured_by_pattern = re.compile(
        r"^! Last configuration change at TIME_STAMP_REPLACED by (\w+)$", flags=re.M | re.I
    )
    output = re.sub(
        configured_by_pattern, "! Last configuration change at TIME_STAMP_REPLACED", output
    )
    return output


def _replace_crypto_strings(output):
    crypto_pattern = re.compile(
        r"^\s+certificate self-signed.*$\s(^\s{2}(\w+\s){1,8})+\s+quit$", flags=re.M | re.I
    )
    output = re.sub(crypto_pattern, "CRYPTO_REPLACED", output)
    return output


def clean_output_data(test, output):
    if test["replace_bytes"]:
        output = _replace_config_bytes(output)
    if test["replace_timestamps"]:
        output = _replace_timestamps(output)
    if test["replace_cfg_by"]:
        output = _replace_configured_by(output)
    if test["replace_crypto"]:
        output = _replace_crypto_strings(output)
    return output
