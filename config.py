from homeassistant.const import (
    CONF_API_KEY,
    CONF_HOST,
    CONF_PORT,
    CONF_SSL,
    CONF_VERIFY_SSL,
)

from .const import CONF_ENDPOINT_ID, CONF_INSTANCE_ID


class ConnectionConfig:
    def __init__(
        self,
        host: str,
        port: str,
        api_key: str,
        ssl: bool,
        verify_ssl: bool,
        instance_id: str,
        endpoint_id: int,
    ) -> None:
        self.host = host
        self.port = port
        self.api_key = api_key
        self.ssl = ssl
        self.verify_ssl = verify_ssl
        self.instance_id = instance_id
        self.endpoint_id = endpoint_id

    def to_dict(self) -> dict:
        return {
            CONF_HOST: self.host,
            CONF_PORT: self.port,
            CONF_API_KEY: self.api_key,
            CONF_SSL: self.ssl,
            CONF_VERIFY_SSL: self.verify_ssl,
            CONF_ENDPOINT_ID: self.endpoint_id,
            CONF_INSTANCE_ID: self.instance_id,
        }
