from pyrad.client import Client, Timeout  # type: ignore[import-untyped]
from pyrad.dictionary import Dictionary  # type: ignore[import-untyped]
from pyrad.packet import Packet, CoAACK, CoANAK  # type: ignore[import-untyped]

from cnaas_nac.core.logging import get_logger
from cnaas_nac.core.settings import settings
from cnaas_nac.models.nas_port import NasPort

logger = get_logger()


class CoA:
    def __init__(self, nasport: NasPort):
        self.nasport = nasport

        self.client = Client(
            self.nasport.nas_ip_address,
            coaport=3799,
            secret=str.encode(settings.RADIUS.COA_SECRET),
            dict=Dictionary("src/cnaas_nac/core/coa_dicts/dictionary"),
        )

        self.client.timeout = 10

    def send_packet(self) -> None:
        if not settings.RADIUS.COA_ENABLED:
            logger.debug("CoA is disabled, not sending CoA packet.")
            return
        logger.debug(
            f"Sending CoA packet to: {self.nasport.nas_identifier} to bounce: {self.nasport.nas_port_id}, user: {self.nasport.username}."
        )

        attrs = {
            "NAS-Identifier": self.nasport.nas_identifier,
            "NAS-IP-Address": self.nasport.nas_ip_address,
            "NAS-Port-Id": self.nasport.nas_port_id,
            "Calling-Station-Id": self.nasport.calling_station_id,
            "Arista-PortFlap": "1",
            "Cisco-Avpair": "subscriber:command=bounce-host-port",
        }

        try:
            self.coa_attrs = {k.replace("-", "_"): attrs[k] for k in attrs}
            self.coa_pkt = self.client.CreateCoAPacket(**self.coa_attrs)
            return_packet: Packet = self.client.SendPacket(self.coa_pkt)  # type: ignore[annotation-unchecked]

            if return_packet.code == CoAACK:
                logger.info("CoAACK received, port bounced.")
            elif return_packet.code == CoANAK:
                logger.error("CoANAK received, port not bounced.")
            else:
                logger.error("Unknown CoA return code received.")
        except Timeout:
            logger.debug("Failed to send CoA packet, is NAS reachable?")
