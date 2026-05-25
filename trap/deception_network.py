class DeceptionNetwork:
    """Simulates a vulnerable internal network topology."""
    
    def __init__(self):
        self.nodes = [
            {"ip": "10.0.0.5", "hostname": "db-primary", "ports": [3306, 22], "vulns": ["CVE-2021-1234"]},
            {"ip": "10.0.0.6", "hostname": "redis-cache", "ports": [6379], "vulns": ["Unauthenticated_Access"]},
            {"ip": "10.0.0.10", "hostname": "jenkins-ci", "ports": [8080, 22], "vulns": ["CVE-2019-1003000"]},
            {"ip": "10.0.0.15", "hostname": "k8s-master", "ports": [6443, 2379, 22], "vulns": ["Anonymous_API_Access"]}
        ]
        
    def scan_network(self, ip_range):
        """Simulates network scanning results."""
        return {"scanned_range": ip_range, "active_hosts": self.nodes}
