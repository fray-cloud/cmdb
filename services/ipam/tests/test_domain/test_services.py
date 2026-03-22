"""Unit tests for IPAM domain services."""

import pytest
from ipam.domain.ip_address import IPAddress
from ipam.domain.ip_range import IPRange
from ipam.domain.prefix import Prefix
from ipam.domain.services import (
    AvailablePrefixService,
    IPAvailabilityService,
    IPRangeUtilizationService,
    PrefixUtilizationService,
)
from ipam.domain.value_objects import PrefixStatus

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def make_prefix(network: str, status: PrefixStatus = PrefixStatus.ACTIVE) -> Prefix:
    p = Prefix.create(network=network, status=status)
    p.collect_uncommitted_events()
    return p


def make_ip(address: str) -> IPAddress:
    ip = IPAddress.create(address=address)
    ip.collect_uncommitted_events()
    return ip


# ---------------------------------------------------------------------------
# PrefixUtilizationService
# ---------------------------------------------------------------------------


class TestPrefixUtilizationService:
    def setup_method(self):
        self.service = PrefixUtilizationService()

    def test_empty_prefix_with_no_children_and_no_ips_returns_zero(self):
        prefix = make_prefix("192.168.0.0/24")
        result = self.service.calculate(prefix, [], [])
        assert result == 0.0

    def test_prefix_with_no_network_returns_zero(self):
        prefix = Prefix()  # no create() called, network is None
        result = self.service.calculate(prefix, [], [])
        assert result == 0.0

    def test_single_ip_in_slash24_gives_correct_ratio(self):
        prefix = make_prefix("192.168.0.0/24")
        ip = make_ip("192.168.0.1")
        result = self.service.calculate(prefix, [], [ip])
        # 1 IP out of 256 addresses
        assert result == pytest.approx(1 / 256)

    def test_multiple_ips_give_correct_ratio(self):
        prefix = make_prefix("10.0.0.0/24")
        ips = [make_ip(f"10.0.0.{i}") for i in range(1, 11)]
        result = self.service.calculate(prefix, [], ips)
        assert result == pytest.approx(10 / 256)

    def test_child_prefix_contributes_its_size(self):
        parent = make_prefix("10.0.0.0/24")
        child = make_prefix("10.0.0.0/28")  # 16 addresses
        result = self.service.calculate(parent, [child], [])
        assert result == pytest.approx(16 / 256)

    def test_multiple_child_prefixes_sum_correctly(self):
        parent = make_prefix("10.0.0.0/24")
        child1 = make_prefix("10.0.0.0/28")  # 16 addresses
        child2 = make_prefix("10.0.0.16/28")  # 16 addresses
        result = self.service.calculate(parent, [child1, child2], [])
        assert result == pytest.approx(32 / 256)

    def test_combined_child_prefixes_and_ips(self):
        parent = make_prefix("10.0.0.0/24")
        child = make_prefix("10.0.0.0/28")  # 16 addresses
        ips = [make_ip(f"10.0.0.{i}") for i in range(100, 104)]  # 4 IPs
        result = self.service.calculate(parent, [child], ips)
        assert result == pytest.approx(20 / 256)

    def test_fully_used_prefix_returns_1_0(self):
        # Use a /30 (4 addresses) filled with a /30 child
        parent = make_prefix("10.0.0.0/30")
        child = make_prefix("10.0.0.0/30")
        result = self.service.calculate(parent, [child], [])
        assert result == 1.0

    def test_result_is_capped_at_1_0_when_oversubscribed(self):
        # Oversubscribe: child is larger than parent due to host count
        parent = make_prefix("10.0.0.0/30")  # 4 addresses
        child1 = make_prefix("10.0.0.0/29")  # 8 addresses (larger)
        result = self.service.calculate(parent, [child1], [])
        assert result == 1.0

    def test_child_prefix_with_no_network_is_skipped(self):
        parent = make_prefix("10.0.0.0/24")
        child_no_network = Prefix()  # network is None
        result = self.service.calculate(parent, [child_no_network], [])
        assert result == 0.0

    def test_slash32_prefix_full_with_one_ip(self):
        prefix = make_prefix("10.0.0.1/32")
        ip = make_ip("10.0.0.1")
        result = self.service.calculate(prefix, [], [ip])
        assert result == 1.0

    def test_ipv6_prefix_utilization(self):
        prefix = make_prefix("2001:db8::/126")  # 4 addresses
        ip = make_ip("2001:db8::1")
        result = self.service.calculate(prefix, [], [ip])
        assert result == pytest.approx(1 / 4)


# ---------------------------------------------------------------------------
# AvailablePrefixService
# ---------------------------------------------------------------------------


class TestAvailablePrefixService:
    def setup_method(self):
        self.service = AvailablePrefixService()

    def test_parent_with_no_network_returns_empty_list(self):
        parent = Prefix()  # no network
        result = self.service.find_available(parent, [], 28)
        assert result == []

    def test_find_all_slash28_in_slash24_with_no_children(self):
        parent = make_prefix("192.168.0.0/24")
        result = self.service.find_available(parent, [], 28)
        # /24 contains 16 non-overlapping /28 subnets
        assert len(result) == 16

    def test_all_found_prefixes_are_valid_cidr_strings(self):
        parent = make_prefix("10.0.0.0/24")
        result = self.service.find_available(parent, [], 28)
        import ipaddress

        for subnet_str in result:
            net = ipaddress.ip_network(subnet_str, strict=True)
            assert net.prefixlen == 28

    def test_all_found_prefixes_are_subnets_of_parent(self):
        parent = make_prefix("10.0.0.0/24")
        result = self.service.find_available(parent, [], 28)
        import ipaddress

        parent_net = ipaddress.ip_network("10.0.0.0/24")
        for subnet_str in result:
            subnet = ipaddress.ip_network(subnet_str)
            assert subnet.subnet_of(parent_net)

    def test_used_child_prefix_is_excluded(self):
        parent = make_prefix("192.168.0.0/24")
        used = make_prefix("192.168.0.0/28")
        result = self.service.find_available(parent, [used], 28)
        assert "192.168.0.0/28" not in result
        assert len(result) == 15  # 16 - 1 used

    def test_multiple_used_child_prefixes_excluded(self):
        parent = make_prefix("192.168.0.0/24")
        used1 = make_prefix("192.168.0.0/28")
        used2 = make_prefix("192.168.0.16/28")
        result = self.service.find_available(parent, [used1, used2], 28)
        assert "192.168.0.0/28" not in result
        assert "192.168.0.16/28" not in result
        assert len(result) == 14

    def test_all_subnets_used_returns_empty_list(self):
        parent = make_prefix("10.0.0.0/30")  # 4 addresses
        used = make_prefix("10.0.0.0/30")  # same subnet fills it
        result = self.service.find_available(parent, [used], 30)
        assert result == []

    def test_desired_prefix_length_same_as_parent(self):
        parent = make_prefix("10.0.0.0/28")
        result = self.service.find_available(parent, [], 28)
        assert result == ["10.0.0.0/28"]

    def test_child_prefix_with_no_network_is_ignored(self):
        parent = make_prefix("10.0.0.0/24")
        child_no_network = Prefix()  # network is None
        result = self.service.find_available(parent, [child_no_network], 28)
        # All /28 subnets should still be available
        assert len(result) == 16

    def test_overlapping_child_prefix_excludes_candidate(self):
        parent = make_prefix("10.0.0.0/24")
        # Use a /29 that overlaps with the first /28
        used = make_prefix("10.0.0.0/29")
        result = self.service.find_available(parent, [used], 28)
        # 10.0.0.0/28 overlaps with 10.0.0.0/29
        assert "10.0.0.0/28" not in result

    def test_ipv6_parent_finds_available_subnets(self):
        parent = make_prefix("2001:db8::/48")
        result = self.service.find_available(parent, [], 56)
        # /48 contains 256 non-overlapping /56 subnets
        assert len(result) == 256

    def test_result_contains_no_duplicates(self):
        parent = make_prefix("10.0.0.0/24")
        result = self.service.find_available(parent, [], 28)
        assert len(result) == len(set(result))


# ---------------------------------------------------------------------------
# IPAvailabilityService
# ---------------------------------------------------------------------------


class TestIPAvailabilityService:
    def setup_method(self):
        self.service = IPAvailabilityService()

    def test_prefix_with_no_network_returns_empty_list(self):
        prefix = Prefix()  # no network
        result = self.service.find_available(prefix, [], count=5)
        assert result == []

    def test_find_one_available_ip_in_empty_prefix(self):
        prefix = make_prefix("10.0.0.0/30")
        result = self.service.find_available(prefix, [], count=1)
        assert len(result) == 1
        assert result[0] == "10.0.0.1"  # first host in /30

    def test_find_multiple_available_ips(self):
        prefix = make_prefix("10.0.0.0/29")  # hosts: .1 through .6
        result = self.service.find_available(prefix, [], count=3)
        assert len(result) == 3

    def test_found_ips_are_within_prefix(self):
        import ipaddress

        prefix = make_prefix("192.168.10.0/28")
        result = self.service.find_available(prefix, [], count=5)
        net = ipaddress.ip_network("192.168.10.0/28")
        for ip_str in result:
            assert ipaddress.ip_address(ip_str) in net

    def test_used_addresses_are_excluded(self):
        prefix = make_prefix("10.0.0.0/30")
        # In a /30: hosts are .1 and .2
        used = [make_ip("10.0.0.1")]
        result = self.service.find_available(prefix, used, count=1)
        assert "10.0.0.1" not in result
        assert result == ["10.0.0.2"]

    def test_multiple_used_addresses_are_excluded(self):
        prefix = make_prefix("10.0.0.0/29")  # hosts: .1-.6
        used = [make_ip("10.0.0.1"), make_ip("10.0.0.2"), make_ip("10.0.0.3")]
        result = self.service.find_available(prefix, used, count=3)
        for ip_str in result:
            assert ip_str not in {"10.0.0.1", "10.0.0.2", "10.0.0.3"}

    def test_count_limits_number_of_results(self):
        prefix = make_prefix("10.0.0.0/24")
        result = self.service.find_available(prefix, [], count=5)
        assert len(result) == 5

    def test_count_larger_than_available_returns_all_hosts(self):
        prefix = make_prefix("10.0.0.0/30")  # only 2 host addresses
        result = self.service.find_available(prefix, [], count=100)
        assert len(result) == 2  # only 2 actual hosts in /30

    def test_all_addresses_used_returns_empty_list(self):
        prefix = make_prefix("10.0.0.0/30")  # hosts: .1 and .2
        used = [make_ip("10.0.0.1"), make_ip("10.0.0.2")]
        result = self.service.find_available(prefix, used, count=1)
        assert result == []

    def test_result_contains_no_duplicates(self):
        prefix = make_prefix("10.0.0.0/24")
        result = self.service.find_available(prefix, [], count=10)
        assert len(result) == len(set(result))

    def test_default_count_is_1(self):
        prefix = make_prefix("10.0.0.0/24")
        result = self.service.find_available(prefix, [])
        assert len(result) == 1

    def test_ipv6_prefix_returns_available_addresses(self):
        prefix = make_prefix("2001:db8::/126")  # hosts: ::1, ::2
        result = self.service.find_available(prefix, [], count=2)
        assert len(result) == 2
        assert "2001:db8::1" in result
        assert "2001:db8::2" in result

    def test_ipv6_used_address_is_excluded(self):
        prefix = make_prefix("2001:db8::/126")
        used = [make_ip("2001:db8::1")]
        result = self.service.find_available(prefix, used, count=1)
        assert "2001:db8::1" not in result
        assert result == ["2001:db8::2"]

    def test_network_and_broadcast_addresses_excluded_for_ipv4(self):
        # In a /30: network=.0, hosts=.1,.2, broadcast=.3
        prefix = make_prefix("10.0.0.0/30")
        result = self.service.find_available(prefix, [], count=10)
        assert "10.0.0.0" not in result  # network address
        assert "10.0.0.3" not in result  # broadcast address

    def test_ip_address_with_no_address_is_skipped(self):
        prefix = make_prefix("10.0.0.0/30")
        ip_no_address = IPAddress()  # address is None
        # Should not crash; ip with no address is simply not in used_set
        result = self.service.find_available(prefix, [ip_no_address], count=2)
        assert len(result) == 2


# ---------------------------------------------------------------------------
# IPRangeUtilizationService
# ---------------------------------------------------------------------------


def make_ip_range(start: str, end: str) -> IPRange:
    r = IPRange.create(start_address=start, end_address=end)
    r.collect_uncommitted_events()
    return r


class TestIPRangeUtilizationService:
    def setup_method(self):
        self.service = IPRangeUtilizationService()

    def test_empty_range_no_addresses(self):
        ip_range = make_ip_range("10.0.0.1", "10.0.0.10")
        result = self.service.calculate(ip_range, [])
        assert result == 0.0

    def test_one_address_in_range_of_ten(self):
        ip_range = make_ip_range("10.0.0.1", "10.0.0.10")
        used = [make_ip("10.0.0.5")]
        result = self.service.calculate(ip_range, used)
        assert result == pytest.approx(1 / 10)

    def test_all_addresses_used(self):
        ip_range = make_ip_range("10.0.0.1", "10.0.0.3")
        used = [make_ip("10.0.0.1"), make_ip("10.0.0.2"), make_ip("10.0.0.3")]
        result = self.service.calculate(ip_range, used)
        assert result == 1.0

    def test_address_outside_range_not_counted(self):
        ip_range = make_ip_range("10.0.0.1", "10.0.0.5")
        used = [make_ip("10.0.0.100")]
        result = self.service.calculate(ip_range, used)
        assert result == 0.0

    def test_range_with_no_addresses_returns_zero(self):
        ip_range = IPRange()
        result = self.service.calculate(ip_range, [])
        assert result == 0.0

    def test_ipv6_range_utilization(self):
        ip_range = make_ip_range("2001:db8::1", "2001:db8::4")
        used = [make_ip("2001:db8::2")]
        result = self.service.calculate(ip_range, used)
        assert result == pytest.approx(1 / 4)
