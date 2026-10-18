"""Verified role routing. All inference remains on Crusoe's approved endpoint."""
import os
from .crusoe import InferenceError

# Exact IDs below were discovered and JSON-probed, not inferred from marketing names.
GLM = 'zai-org/GLM-5.3'
FLASH = 'zai-org/GLM-5.3-Flash'
DEEP = 'deepseek-ai/Deepseek-V4-Flash'
PRO = 'deepseek-ai/DeepSeek-V4-Pro'
CHEAP = 'openai/gpt-oss-120b'
NANO = 'nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B'
ROUTES = {
    'manager': [GLM, PRO, FLASH], 'auditor': [GLM, PRO, FLASH],
    'debt': [DEEP, FLASH], 'followup': [DEEP, FLASH],
    'funding': [DEEP, FLASH], 'coverage': [DEEP, FLASH], 'maturity': [DEEP, FLASH],
    'deals': [FLASH, DEEP], 'contract_backing': [FLASH, DEEP],
    'markets': [FLASH, DEEP], 'bond_market': [FLASH, DEEP],
    'verification': [GLM, PRO, FLASH], 'dossier': [FLASH, CHEAP], 'triage': [CHEAP, NANO, DEEP],
}
# Estimates only, USD / million tokens. Refresh against provider pricing before production.
PRICES = {GLM: (1.4, 4.4), FLASH: (.15, .50), DEEP: (.14, .28),
          CHEAP: (.05, .25), NANO: (.05, .20)}


def token_cost(model, usage):
    if model not in PRICES:
        return None
    inp, out = PRICES[model]
    return (usage.get('prompt_tokens', 0) * inp + usage.get('completion_tokens', 0) * out) / 1_000_000


class RoleRouter:
    def __init__(self, crusoe):
        self.crusoe = crusoe
        self.verified = {}
        self.diagnostics = []

    def configured(self, role):
        override = [s.strip() for s in os.getenv('CRUSOE_ROUTE_' + role.upper(), '').split(',') if s.strip()]
        return override or ROUTES.get(role, ROUTES['triage'])

    async def verify(self):
        available = await self.crusoe.models()
        self.verified = {}
        self.diagnostics = []
        # Verify distinct candidates once. Unadvertised IDs are never called.
        candidates = list(dict.fromkeys(m for r in ROUTES for m in self.configured(r)))
        for model in candidates:
            record = {'model': model, 'advertised': model in available, 'json_verified': False}
            if model in available:
                try:
                    result = await self.crusoe.json('Return JSON only: {"connectivity":"ok"}.',
                                                    {'purpose': 'role route availability probe'}, model=model)
                    record['json_verified'] = result.get('connectivity') == 'ok'
                    record['latency_ms'] = self.crusoe.last_metadata.get('latency_ms')
                    record['usage'] = self.crusoe.last_metadata.get('usage', {})
                    record['estimated_cost_usd'] = token_cost(model, record['usage'])
                except InferenceError as exc:
                    record['category'] = exc.category
                if record['json_verified']:
                    self.verified[model] = True
            self.diagnostics.append(record)
        return self.view()

    def select(self, role, failed=()):
        candidates = [m for m in self.configured(role) if m in self.verified and m in PRICES]
        # Prefer a fresh fallback, but permit the worker's final bounded retry on a ready primary.
        candidates = [m for m in candidates if m not in failed] + [m for m in candidates if m in failed]
        if not candidates:
            raise InferenceError('No JSON-verified Crusoe route for ' + role, category='model_unavailable')
        ready = [m for m in candidates if self.crusoe.cooldowns.get(m, 0) <= __import__('time').monotonic()]
        if not ready:
            raise InferenceError('Crusoe role routes are cooling down', 429, 15, 'rate_limited')
        return ready[0]

    def view(self):
        return {'provider': 'Crusoe Managed Inference', 'models': self.diagnostics,
                'routes': {r: {'configured': self.configured(r),
                               'verified': [m for m in self.configured(r) if m in self.verified],
                               'routable': [m for m in self.configured(r) if m in self.verified and m in PRICES]}
                           for r in ROUTES},
                'pricing': {'usd_per_million_tokens': PRICES, 'reference_date': '2026-10-17',
                            'source': 'https://www.crusoe.ai/cloud/pricing', 'estimated_only': True}}
