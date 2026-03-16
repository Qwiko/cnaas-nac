#!/usr/bin/python3

import sys
from typing import List, Optional

from jinja2 import DictLoader, Environment, FileSystemLoader
from pydantic import BaseModel, Field, ValidationError
from pydantic_settings import BaseSettings


class ProxyServer(BaseModel):
    name: str
    ipaddr: str
    port: int = 1812
    secret: str


class ProxyRealm(BaseModel):
    realm: str
    # If pool_name is not provided, we will auto-generate it in the template
    pool_name: Optional[str] = None
    # Default to fail-over, but allows load-balance, client-balance, etc.
    pool_type: str = Field(default="fail-over")
    servers: List[ProxyServer]


class EapInstance(BaseModel):
    name: str
    domain: str
    priv_key: str
    cert: str
    ca: str

    check_crl: bool
    crl_url: str


    

class Settings(BaseSettings):
    pre_start_base_folder: str = "/etc/raddb"

    radius_proxy_configs: List[ProxyRealm] = []
    radius_eap_configs: List[EapInstance] = []

    AD_USERNAME_ATTR: str = "sAMAccountName"
    AD_MEMBER_ATTR: str = "memberOf"
    AD_DOMAIN : str = ""
    AD_SERVER: str = "" # Optional hostname other than the domain name
    AD_USERNAME : str = ""
    AD_PASSWORD : str = ""
    AD_BASE_DN : str = ""


if __name__ == "__main__":
    try:
        settings = Settings()
    except ValidationError as e:
        print("Configuration Error! The environment variables are invalid:")
        print(e.json(indent=2))
        sys.exit(1)

    base_folder = settings.pre_start_base_folder

    env = Environment(
        loader=FileSystemLoader(
            [
                base_folder,
                f"{base_folder}/sites-available",
                f"{base_folder}/mods-available",
            ]
        )
    )

    for template_name in env.list_templates(extensions=["j2"]):
        template = env.get_template(template_name)
        render_filename = template_name[:-3]

        rendered_template = template.render(**settings.model_dump())

        with open(f"{base_folder}/{render_filename}", "w", encoding="utf-8") as f:
            f.write(rendered_template)

    # print(rendered_templates)
