"""Unit-Tests für die Input-Validierung."""

import pytest

from src.mcp_server.tools.input_validation import (
    validate_nmap_flags,
    validate_nuclei_templates,
    validate_ports,
    validate_target,
)


# --- Target-Validierung ---

def test_valid_ipv4():
    assert validate_target("10.10.10.5") == "10.10.10.5"


def test_valid_cidr():
    assert validate_target("10.10.10.0/24") == "10.10.10.0/24"


def test_valid_domain():
    assert validate_target("scanme.nmap.org") == "scanme.nmap.org"


def test_valid_comma_separated():
    assert validate_target("10.10.10.3,10.10.10.5") == "10.10.10.3,10.10.10.5"


def test_empty_target_fails():
    with pytest.raises(ValueError, match="leer"):
        validate_target("")


def test_shell_injection_blocked():
    """Command Injection über Sonderzeichen wird verhindert."""
    with pytest.raises(ValueError, match="ungültige Zeichen"):
        validate_target("10.10.10.5; rm -rf /")


def test_pipe_injection_blocked():
    with pytest.raises(ValueError, match="ungültige Zeichen"):
        validate_target("10.10.10.5 | cat /etc/passwd")


def test_backtick_injection_blocked():
    with pytest.raises(ValueError, match="ungültige Zeichen"):
        validate_target("`whoami`")


# --- Port-Validierung ---

def test_valid_single_port():
    assert validate_ports("80") == "80"


def test_valid_port_list():
    assert validate_ports("80,443,8080") == "80,443,8080"


def test_valid_port_range():
    assert validate_ports("1-1000") == "1-1000"


def test_port_too_high():
    with pytest.raises(ValueError, match="65535"):
        validate_ports("99999")


def test_port_zero():
    with pytest.raises(ValueError, match="1-65535"):
        validate_ports("0")


# --- nmap-Flag-Validierung ---

def test_valid_nmap_flags():
    result = validate_nmap_flags(["-sV", "-sC", "-Pn"])
    assert result == ["-sV", "-sC", "-Pn"]


def test_dangerous_nmap_flag_blocked():
    """Gefährliche Flags wie --script werden blockiert."""
    with pytest.raises(ValueError, match="nicht erlaubt"):
        validate_nmap_flags(["--script=exploit"])


def test_file_input_flag_blocked():
    with pytest.raises(ValueError, match="nicht erlaubt"):
        validate_nmap_flags(["-iL"])


# --- nuclei-Template-Validierung ---

def test_valid_nuclei_templates():
    result = validate_nuclei_templates(["cves", "vulnerabilities"])
    assert "cves" in result


def test_invalid_nuclei_template():
    with pytest.raises(ValueError, match="nicht erlaubt"):
        validate_nuclei_templates(["exploit"])
