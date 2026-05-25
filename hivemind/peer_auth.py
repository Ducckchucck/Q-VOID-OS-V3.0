import hashlib
import hmac
from rust_core import engine as rust_core

class PeerAuthenticator:
    """Handles secure mutual authentication between Hive nodes."""
    def __init__(self, shared_secret: str = "qvoid_swarm_secret"):
        self.shared_secret = shared_secret.encode()

    def generate_challenge(self) -> str:
        return rust_core.secure_random(16).hex()

    def solve_challenge(self, challenge: str) -> str:
        h = hmac.new(self.shared_secret, challenge.encode(), hashlib.sha256)
        return h.hexdigest()

    def verify_solution(self, challenge: str, solution: str) -> bool:
        expected = self.solve_challenge(challenge)
        return hmac.compare_digest(expected, solution)
