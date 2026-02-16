from pyrad.client import Client
from pyrad.dictionary import Dictionary

from cnaas_nac.core.logging import get_logger


logger = get_logger()


class CoA:
    def __init__(self, host, secret):
        self.host = host
        self.client = Client(
            self.host, coaport=3799, secret=secret, dict=Dictionary("dictionary")
        )
        self.client.timeout = 10

    def send_packet(self, attrs=None):
        logger.debug(f"Sending CoA packet to {self.host}.")
        try:
            self.coa_attrs = {k.replace("-", "_"): attrs[k] for k in attrs}
            self.coa_pkt = self.client.CreateCoAPacket(**self.coa_attrs)
            self.client.SendPacket(self.coa_pkt)
        except Exception:
            raise Exception("Failed to send CoA packet, is NAS reachable?")
        logger.debug("CoA packet sent successfully.")
        return "Port bounced"
