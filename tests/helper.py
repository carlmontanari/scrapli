import re


def cisco_iosxe_clean_response(response):
    def _replace_config_bytes(response):
        config_bytes_pattern = re.compile(r"^Current configuration : \d+ bytes$", flags=re.M | re.I)
        response = re.sub(config_bytes_pattern, "Current configuration : CONFIG_BYTES", response)
        return response

    def _replace_timestamps(response):
        datetime_pattern = re.compile(
            r"\d+:\d+:\d+\d+\s+[a-z]{3}\s+(mon|tue|wed|thu|fri|sat|sun)\s+(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\s+\d+\s+\d+",
            flags=re.M | re.I,
        )
        response = re.sub(datetime_pattern, "TIME_STAMP_REPLACED", response)
        return response

    def _replace_configured_by(response):
        configured_by_pattern = re.compile(
            r"^! Last configuration change at TIME_STAMP_REPLACED by (\w+)$", flags=re.M | re.I
        )
        response = re.sub(
            configured_by_pattern, "! Last configuration change at TIME_STAMP_REPLACED", response
        )
        return response

    def _replace_hashed_passwords(response):
        crypto_pattern = re.compile(r"^enable secret 5 (.*$)", flags=re.M | re.I)
        response = re.sub(crypto_pattern, "enable secret 5 HASHED_PASSWORD", response)
        return response

    def _replace_call_home_comment(response):
        # vrnetlab router seems to get this comment string but vrouter one does not. unclear why,
        # but we'll just remove it just in case
        crypto_pattern = re.compile(
            r"(^.*$)\n^! Call-home is enabled by Smart-Licensing.$(\n^.*$)", flags=re.M | re.I
        )
        response = re.sub(crypto_pattern, r"\1\2", response)
        return response

    def _replace_certificates_and_license(response):
        # replace pki/certificate stuff and license all in one go -- this is always lumped together
        # but in vrnetlab vs vrouter things are sometimes in different order (trustpoints are
        # switched for example) so comparing strings obviously fails even though content is correct
        crypto_pattern = re.compile(
            r"^crypto pki .*\nlicense udi pid CSR1000V sn \w+$", flags=re.M | re.I | re.S
        )
        response = re.sub(crypto_pattern, "CERTIFICATES AND LICENSE", response)
        return response

    response = _replace_config_bytes(response)
    response = _replace_timestamps(response)
    response = _replace_configured_by(response)
    response = _replace_hashed_passwords(response)
    response = _replace_call_home_comment(response)
    response = _replace_certificates_and_license(response)
    return response


def cisco_iosxr_clean_response(response):
    def _replace_timestamps(response):
        datetime_pattern = re.compile(
            r"(mon|tue|wed|thu|fri|sat|sun)\s+(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\s+\d+\s+\d+:\d+:\d+((\.\d+\s\w+)|\s\d+)",
            flags=re.M | re.I,
        )
        response = re.sub(datetime_pattern, "TIME_STAMP_REPLACED", response)
        return response

    def _replace_configured_by(response):
        configured_by_pattern = re.compile(
            r"^!! Last configuration change at TIME_STAMP_REPLACED by (\w+)$", flags=re.M | re.I
        )
        response = re.sub(
            configured_by_pattern, "!! Last configuration change at TIME_STAMP_REPLACED", response
        )
        return response

    def _replace_crypto_strings(response):
        crypto_pattern = re.compile(r"^\ssecret\s5\s[\w$\.\/]+$", flags=re.M | re.I)
        response = re.sub(crypto_pattern, "CRYPTO_REPLACED", response)
        return response

    def _replace_commit_in_progress(response):
        commit_in_progress_pattern = re.compile(r"System configuration.*", flags=re.M | re.I | re.S)
        response = re.sub(commit_in_progress_pattern, "", response)
        return response.rstrip()

    response = _replace_timestamps(response)
    response = _replace_configured_by(response)
    response = _replace_crypto_strings(response)
    response = _replace_commit_in_progress(response)
    return response


def cisco_nxos_clean_response(response):
    def _replace_timestamps(response):
        datetime_pattern = re.compile(
            r"(mon|tue|wed|thu|fri|sat|sun)\s+(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\s+\d+\s+\d+:\d+:\d+\s\d+",
            flags=re.M | re.I,
        )
        response = re.sub(datetime_pattern, "TIME_STAMP_REPLACED", response)
        return response

    def _replace_crypto_strings(response):
        crypto_pattern = re.compile(r"^(.*?\s(?:5|md5)\s)[\w$\.\/]+.*$", flags=re.M | re.I)
        response = re.sub(crypto_pattern, "CRYPTO_REPLACED", response)
        return response

    def _replace_resource_limits(response):
        crypto_pattern = re.compile(
            r"^(\s+limit-resource\s[a-z0-9\-]+\sminimum\s)\d+\smaximum\s\d+$", flags=re.M | re.I
        )
        response = re.sub(crypto_pattern, r"\1N maximum N", response)
        return response

    response = _replace_timestamps(response)
    response = _replace_crypto_strings(response)
    response = _replace_resource_limits(response)
    return response


def arista_eos_clean_response(response):
    def _replace_timestamps(response):
        datetime_pattern = re.compile(
            r"(mon|tue|wed|thu|fri|sat|sun)\s+(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\s+\d+\s+\d+:\d+:\d+\s+\d+$",
            flags=re.M | re.I,
        )
        response = re.sub(datetime_pattern, "TIME_STAMP_REPLACED", response)
        return response

    def _replace_crypto_strings(response):
        crypto_pattern = re.compile(r"secret\ssha512\s[\w$\.\/]+$", flags=re.M | re.I)
        response = re.sub(crypto_pattern, "CRYPTO_REPLACED", response)
        return response

    response = _replace_timestamps(response)
    response = _replace_crypto_strings(response)
    return response


def juniper_junos_clean_response(response):
    def _replace_timestamps(response):
        datetime_pattern = re.compile(
            r"^## Last commit: \d+-\d+-\d+\s\d+:\d+:\d+\s\w+.*$", flags=re.M | re.I
        )
        response = re.sub(datetime_pattern, "TIME_STAMP_REPLACED", response)
        return response

    def _replace_crypto_strings(response):
        crypto_pattern = re.compile(
            r'^\s+encrypted-password\s"[\w$\.\/]+";\s.*$', flags=re.M | re.I
        )
        response = re.sub(crypto_pattern, "CRYPTO_REPLACED", response)
        return response

    response = _replace_timestamps(response)
    response = _replace_crypto_strings(response)
    return response
