"""Safe diagnostic categories; no exception text, URIs or credentials leave this module."""
import fnmatch
import json
from pathlib import Path
from urllib.parse import parse_qs,urlsplit


def classify_error(exc):
    text=str(exc).lower()
    for category,terms in (
        ('dns_resolution_failure',('name resolution','translate host','name or service not known','nodename nor servname')),
        ('tls_problem',('certificate verify','ssl handshake','tls handshake','certificate validation')),
        ('authentication_failure',('password authentication failed','invalid authorization','authentication failed')),
        ('network_policy_restriction',('proxyerror','403 forbidden','tunnel connection failed: 403')),
        ('tcp_connection_failure',('connection refused','network is unreachable','timeout expired','connection timed out')),
    ):
        if any(term in text for term in terms):
            return category
    name=type(exc).__name__
    return {'ProxyError':'proxy_connection_failure','ConnectTimeout':'connection_timeout',
            'ReadTimeout':'provider_timeout','ConnectError':'connection_failure',
            'gaierror':'dns_resolution_failure'}.get(name,'application_error')


def policy_snapshot():
    try:
        data=json.loads(Path('/etc/codex/network-policy.json').read_text())
        return data if data.get('version')==1 else {}
    except (OSError,ValueError):
        return {}


def http_policy_allows(host):
    policy=policy_snapshot().get('http_network_policy',{})
    if policy.get('type')=='unrestricted':
        return True
    if policy.get('type')!='restricted':
        return None
    return any(fnmatch.fnmatchcase(host,entry.get('host','')) for entry in policy.get('egress_rules',[]))


def database_configuration(uri):
    try:
        part=urlsplit(uri or '')
        host=part.hostname
        port=part.port or 5432
        return {'configured':bool(uri),'host':host,'port':port,
                'postgres_scheme':part.scheme in ('postgres','postgresql'),
                'tls_required':parse_qs(part.query).get('sslmode',[''])[0] in ('require','verify-ca','verify-full'),
                'https_endpoint_host':('api.'+host.split('.',1)[1]) if host and host.endswith('.neon.tech') else None,
                'tcp_grant_configured':any(fnmatch.fnmatchcase(host or '',entry if isinstance(entry,str) else entry.get('host',''))
                    for entry in policy_snapshot().get('tcp_network_access',{}).get('domains',[]))}
    except (ValueError,TypeError):
        return {'configured':bool(uri),'configuration_error':True}
