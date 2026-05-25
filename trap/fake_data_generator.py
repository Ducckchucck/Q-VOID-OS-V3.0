import random
import json
import uuid

class FakeDataGenerator:
    """Generates synthetic, juicy data to keep attackers engaged."""
    
    @staticmethod
    def generate_credentials(count=5):
        users = ["admin", "root", "deploy", "jenkins", "db_admin", "devops"]
        creds = []
        for _ in range(count):
            creds.append({
                "username": random.choice(users),
                "password": f"Password{random.randint(100, 999)}!",
                "role": random.choice(["admin", "user", "readonly"])
            })
        return creds
        
    @staticmethod
    def generate_pii(count=10):
        records = []
        for _ in range(count):
            records.append({
                "id": str(uuid.uuid4()),
                "name": f"User_{random.randint(1000, 9999)}",
                "credit_card": f"4111-1111-1111-{random.randint(1000, 9999)}",
                "email": f"user{random.randint(100, 999)}@example.com"
            })
        return records

    @staticmethod
    def generate_ssh_keys():
        return {
            "id_rsa": "-----BEGIN RSA PRIVATE KEY-----\nMIIEpAIBAAKCAQEA...\n-----END RSA PRIVATE KEY-----",
            "id_rsa.pub": "ssh-rsa AAAAB3NzaC1yc2E... user@internal-prod"
        }
