# User manual

## FreeRadius sites

In the CNaaS-NAC FreeRadius configuration there are two different sites.  
This value can be set in the radius clients server attribute.

### default

Exposes EAP and proxies.  
Issues REST calls to the internal API for policy engine processing.

Should be used for internal radius clients.

### external

Exposes only the EAP instances, does not issue any call to the internal api.
Will still generate authorization logs that can be viewed through the api.

Suitable for remote radius clients.