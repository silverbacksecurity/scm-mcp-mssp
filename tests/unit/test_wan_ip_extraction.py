"""Unit tests for WAN IP extraction: NGFW running-config XML parsing and the
SD-WAN topology mermaid IP annotation. Pure functions, no I/O.
"""

from __future__ import annotations

from scm_mcp_mssp.audit.extractor import parse_ngfw_interface_ips
from scm_mcp_mssp.audit.sdwan_topo import topology_to_mermaid

_SAMPLE_XML = """<?xml version="1.0"?>
<config version="10.2.0">
  <devices>
    <entry name="localhost.localdomain">
      <network>
        <interface>
          <ethernet>
            <entry name="ethernet1/1">
              <layer3>
                <ip>
                  <entry name="203.0.113.5/30"/>
                </ip>
              </layer3>
            </entry>
            <entry name="ethernet1/2">
              <layer3>
                <dhcp-client>
                  <enable>yes</enable>
                </dhcp-client>
              </layer3>
            </entry>
            <entry name="ethernet1/3">
              <layer2/>
            </entry>
          </ethernet>
          <aggregate-ethernet>
            <entry name="ae1">
              <layer3>
                <ip>
                  <entry name="198.51.100.9/29"/>
                  <entry name="198.51.100.10/29"/>
                </ip>
              </layer3>
            </entry>
          </aggregate-ethernet>
        </interface>
      </network>
      <vsys>
        <entry name="vsys1">
          <zone>
            <entry name="untrust">
              <network>
                <layer3>
                  <member>ethernet1/1</member>
                  <member>ethernet1/2</member>
                </layer3>
              </network>
            </entry>
            <entry name="dmz">
              <network>
                <layer3>
                  <member>ae1</member>
                </layer3>
              </network>
            </entry>
          </zone>
        </entry>
      </vsys>
    </entry>
  </devices>
</config>
"""


class TestParseNgfwInterfaceIps:
    def test_static_interface(self) -> None:
        result = parse_ngfw_interface_ips(_SAMPLE_XML)
        by_iface = {r["interface"]: r for r in result}
        assert by_iface["ethernet1/1"]["addressing"] == "static"
        assert by_iface["ethernet1/1"]["ip_addresses"] == ["203.0.113.5/30"]
        assert by_iface["ethernet1/1"]["zone"] == "untrust"

    def test_dhcp_interface_has_no_leased_ip(self) -> None:
        result = parse_ngfw_interface_ips(_SAMPLE_XML)
        by_iface = {r["interface"]: r for r in result}
        assert by_iface["ethernet1/2"]["addressing"] == "dhcp"
        assert by_iface["ethernet1/2"]["ip_addresses"] == []

    def test_aggregate_ethernet_multiple_ips(self) -> None:
        result = parse_ngfw_interface_ips(_SAMPLE_XML)
        by_iface = {r["interface"]: r for r in result}
        assert by_iface["ae1"]["ip_addresses"] == [
            "198.51.100.9/29",
            "198.51.100.10/29",
        ]
        assert by_iface["ae1"]["zone"] == "dmz"

    def test_layer2_interface_excluded(self) -> None:
        result = parse_ngfw_interface_ips(_SAMPLE_XML)
        assert "ethernet1/3" not in {r["interface"] for r in result}

    def test_malformed_xml_returns_empty(self) -> None:
        assert parse_ngfw_interface_ips("<not valid xml") == []

    def test_empty_xml_returns_empty(self) -> None:
        assert parse_ngfw_interface_ips("<config></config>") == []


class TestTopologyMermaidWanIps:
    def test_site_node_annotated_with_ip(self) -> None:
        sites = [{"id": "s1", "name": "Branch-1", "element_cluster_role": "spoke"}]
        connections = [
            {
                "source_site_id": "s1",
                "target_site_id": "s1",
                "wan_network_name": "Internet",
                "wan_type": "AUTO-PUBLIC",
                "status": "up",
            }
        ]
        wan_ips = [{"site_id": "s1", "ipv4_addresses": ["203.0.113.5/30"], "used_for": "public"}]
        diagram = topology_to_mermaid(connections, sites, [], wan_ips=wan_ips)
        assert "203.0.113.5/30" in diagram

    def test_no_wan_ips_still_renders(self) -> None:
        sites = [{"id": "s1", "name": "Branch-1", "element_cluster_role": "spoke"}]
        diagram = topology_to_mermaid([], sites, [], wan_ips=None)
        assert "Branch-1" in diagram
