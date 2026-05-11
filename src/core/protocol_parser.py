"""
协议解析模块 - 提供详细的协议解析功能
"""
from scapy.all import *
from scapy.layers.inet import IP, TCP, UDP, ICMP
from scapy.layers.inet6 import IPv6
from scapy.layers.l2 import ARP, Ether
from scapy.layers.dns import DNS
import binascii

class ProtocolParser:
    """协议解析器"""
    
    @staticmethod
    def parse_ethernet(packet):
        """解析Ethernet层"""
        if Ether not in packet:
            return None
            
        eth = packet[Ether]
        return {
            'layer': 'Ethernet',
            'source_mac': eth.src,
            'destination_mac': eth.dst,
            'type': eth.type,
            'description': f"Ethernet II, Src: {eth.src}, Dst: {eth.dst}"
        }
    
    @staticmethod
    def parse_ipv4(packet):
        """解析IPv4层"""
        if IP not in packet:
            return None
            
        ip = packet[IP]
        return {
            'layer': 'IPv4',
            'version': ip.version,
            'header_length': ip.ihl * 4,
            'tos': ip.tos,
            'total_length': ip.len,
            'identification': ip.id,
            'flags': ip.flags,
            'fragment_offset': ip.frag,
            'ttl': ip.ttl,
            'protocol': ip.proto,
            'header_checksum': ip.chksum,
            'source_ip': ip.src,
            'destination_ip': ip.dst,
            'description': f"Internet Protocol Version 4, Src: {ip.src}, Dst: {ip.dst}"
        }
    
    @staticmethod
    def parse_ipv6(packet):
        """解析IPv6层"""
        if IPv6 not in packet:
            return None
            
        ip6 = packet[IPv6]
        return {
            'layer': 'IPv6',
            'version': ip6.version,
            'traffic_class': ip6.tc,
            'flow_label': ip6.fl,
            'payload_length': ip6.plen,
            'next_header': ip6.nh,
            'hop_limit': ip6.hlim,
            'source_ip': ip6.src,
            'destination_ip': ip6.dst,
            'description': f"Internet Protocol Version 6, Src: {ip6.src}, Dst: {ip6.dst}"
        }
    
    @staticmethod
    def parse_tcp(packet):
        """解析TCP层"""
        if TCP not in packet:
            return None
            
        tcp = packet[TCP]
        flags = ProtocolParser._parse_tcp_flags(tcp.flags)
        
        return {
            'layer': 'TCP',
            'source_port': tcp.sport,
            'destination_port': tcp.dport,
            'sequence_number': tcp.seq,
            'acknowledgment_number': tcp.ack,
            'header_length': tcp.dataofs * 4,
            'flags': flags,
            'window_size': tcp.window,
            'checksum': tcp.chksum,
            'urgent_pointer': tcp.urgptr,
            'options': str(tcp.options) if tcp.options else '',
            'description': f"Transmission Control Protocol, Src Port: {tcp.sport}, Dst Port: {tcp.dport}"
        }
    
    @staticmethod
    def _parse_tcp_flags(flags):
        """解析TCP标志位"""
        flag_names = ['FIN', 'SYN', 'RST', 'PSH', 'ACK', 'URG', 'ECE', 'CWR', 'NS']
        flag_values = []
        
        for i, name in enumerate(flag_names):
            if flags & (1 << i):
                flag_values.append(name)
                
        return ', '.join(flag_values) if flag_values else 'None'
    
    @staticmethod
    def parse_udp(packet):
        """解析UDP层"""
        if UDP not in packet:
            return None
            
        udp = packet[UDP]
        return {
            'layer': 'UDP',
            'source_port': udp.sport,
            'destination_port': udp.dport,
            'length': udp.len,
            'checksum': udp.chksum,
            'description': f"User Datagram Protocol, Src Port: {udp.sport}, Dst Port: {udp.dport}"
        }
    
    @staticmethod
    def parse_arp(packet):
        """解析ARP层"""
        if ARP not in packet:
            return None
            
        arp = packet[ARP]
        op_map = {1: 'REQUEST', 2: 'REPLY'}
        op_str = op_map.get(arp.op, f'UNKNOWN({arp.op})')
        
        return {
            'layer': 'ARP',
            'hardware_type': arp.hwtype,
            'protocol_type': arp.ptype,
            'hardware_size': arp.hwlen,
            'protocol_size': arp.plen,
            'opcode': arp.op,
            'opcode_str': op_str,
            'sender_mac': arp.hwsrc,
            'sender_ip': arp.psrc,
            'target_mac': arp.hwdst,
            'target_ip': arp.pdst,
            'description': f"Address Resolution Protocol ({op_str}), {arp.psrc} -> {arp.pdst}"
        }
    
    @staticmethod
    def parse_icmp(packet):
        """解析ICMP层"""
        if ICMP not in packet:
            return None
            
        icmp = packet[ICMP]
        return {
            'layer': 'ICMP',
            'type': icmp.type,
            'code': icmp.code,
            'checksum': icmp.chksum,
            'description': f"Internet Control Message Protocol, Type: {icmp.type}, Code: {icmp.code}"
        }
    
    @staticmethod
    def parse_dns(packet):
        """解析DNS层"""
        if DNS not in packet:
            return None
            
        dns = packet[DNS]
        return {
            'layer': 'DNS',
            'id': dns.id,
            'qr': 'Response' if dns.qr else 'Query',
            'opcode': dns.opcode,
            'aa': dns.aa,
            'tc': dns.tc,
            'rd': dns.rd,
            'ra': dns.ra,
            'z': dns.z,
            'rcode': dns.rcode,
            'qdcount': dns.qdcount,
            'ancount': dns.ancount,
            'nscount': dns.nscount,
            'arcount': dns.arcount,
            'description': f"Domain Name System ({'Response' if dns.qr else 'Query'})"
        }
    
    @staticmethod
    def parse_packet_details(packet):
        """完整解析报文的所有层"""
        layers = []
        
        # 按协议层顺序解析
        parsers = [
            ProtocolParser.parse_ethernet,
            ProtocolParser.parse_ipv4,
            ProtocolParser.parse_ipv6,
            ProtocolParser.parse_arp,
            ProtocolParser.parse_tcp,
            ProtocolParser.parse_udp,
            ProtocolParser.parse_icmp,
            ProtocolParser.parse_dns
        ]
        
        for parser in parsers:
            result = parser(packet)
            if result:
                layers.append(result)
        
        return layers
    
    @staticmethod
    def get_hex_dump(packet, bytes_per_line=16):
        """生成十六进制转储"""
        raw_data = bytes(packet)
        hex_dump = []
        
        for i in range(0, len(raw_data), bytes_per_line):
            chunk = raw_data[i:i + bytes_per_line]
            hex_str = ' '.join(f'{b:02x}' for b in chunk)
            ascii_str = ''.join(chr(b) if 32 <= b <= 126 else '.' for b in chunk)
            hex_dump.append(f'{i:04x}  {hex_str:<48}  {ascii_str}')
        
        return '\n'.join(hex_dump)