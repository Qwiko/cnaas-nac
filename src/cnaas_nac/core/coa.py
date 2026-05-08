from typing import Optional, Self

from pyrad.client import Client, Timeout
from pyrad.dictionary import Dictionary
from pyrad.packet import CoAACK, CoANAK, Packet
from sqlalchemy import cast, select
from sqlalchemy.dialects.postgresql import INET
from sqlalchemy.ext.asyncio import AsyncSession

from cnaas_nac.core.db import async_session_factory
from cnaas_nac.core.logging import get_logger
from cnaas_nac.models.endpoint import Endpoint
from cnaas_nac.models.nas import Nas
from cnaas_nac.models.nas_port import NasPort

logger = get_logger()


class CoA:
    def __init__(self, endpoint: Endpoint, nas_port: NasPort, nas: Nas) -> None:
        self.endpoint = endpoint
        self.nas_port = nas_port
        self.nas = nas

        secret = self.nas.coa_secret if self.nas.coa_secret else self.nas.secret

        self.coa_client = Client(
            server=self.nas_port.nas_ip_address,
            coaport=self.nas.coa_port,
            secret=secret.encode(),
            dict=Dictionary("src/cnaas_nac/core/coa_dicts/dictionary"),
        )

        self.coa_client.timeout = 10

    @classmethod
    async def create(cls, endpoint: Endpoint) -> Optional[Self]:
        async with async_session_factory() as db:
            nas_port = await get_latest_nas_port(db, endpoint)

            if not nas_port:
                logger.info(
                    f"No NAS port found for endpoint: {endpoint.username},({endpoint.calling_station_id})."
                )
                return None

            # Check if this NAS_Port is more recent on another endpoint.abs

            result = await db.execute(
                select(NasPort).where(
                    NasPort.updated_at > nas_port.updated_at,
                    NasPort.username != endpoint.username,
                    NasPort.calling_station_id != endpoint.calling_station_id,
                )
            )

            other_port = result.scalar_one_or_none()

            if other_port:
                logger.info("Endpoint have no recent NAS Port, skipping port bounce.")
                return None

            assert nas_port.nas_ip_address, "NAS port must have NAS IP address."

            nas = await get_nas(db, nas_port.nas_ip_address)

            if not nas:
                logger.info(
                    f"NAS not found for the given IP address {nas_port.nas_ip_address}."
                )
                return None

            if not nas.coa_enabled:
                logger.debug(
                    f"CoA is disabled for {nas.name}, {nas_port.nas_identifier}, not sending CoA packet."
                )
                return None
            # db.expunge(endpoint)
            db.expunge(nas_port)
        return cls(endpoint, nas_port, nas)

    def send_coa_packet(self) -> None:
        logger.debug(
            f"Sending CoA packet to: {self.nas_port.nas_identifier} to bounce: {self.nas_port.nas_port_id}, user: {self.nas_port.username}."
        )

        attrs = {
            "NAS-Identifier": self.nas_port.nas_identifier,
            "NAS-IP-Address": self.nas_port.nas_ip_address,
            "NAS-Port-Id": self.nas_port.nas_port_id,
            "Calling-Station-Id": self.nas_port.calling_station_id,
            "Arista-PortFlap": "1",
            "Cisco-Avpair": "subscriber:command=bounce-host-port",
        }

        try:
            coa_attrs = {k.replace("-", "_"): attrs[k] for k in attrs}
            coa_pkt = self.coa_client.CreateCoAPacket(**coa_attrs)
            return_packet: Packet = self.coa_client.SendPacket(coa_pkt)

            if return_packet.code == CoAACK:
                logger.info("CoAACK received, port bounced.")
            elif return_packet.code == CoANAK:
                logger.error("CoANAK received, port not bounced.")
            else:
                logger.error("Unknown CoA return code received.")
        except Timeout:
            logger.debug("Failed to send CoA packet, is NAS reachable?")


async def get_latest_nas_port(
    db: AsyncSession, endpoint: Endpoint
) -> Optional[NasPort]:
    result = await db.execute(
        select(NasPort)
        .where(
            NasPort.username == endpoint.username,
            NasPort.calling_station_id == endpoint.calling_station_id,
        )
        .order_by(NasPort.updated_at.desc())
    )
    return result.scalars().first()


async def get_nas(db: AsyncSession, nas_ip_address: str) -> Optional[Nas]:
    result = await db.execute(
        select(Nas).where(Nas.network.op(">>=")(cast(nas_ip_address, INET)))
    )
    return result.scalar_one_or_none()
