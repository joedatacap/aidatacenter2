"""One network attempt per json() call; the durable worker owns retries and budgets."""
import asyncio
import json
import math
import os
import random
import time
from datetime import datetime,timezone
from email.utils import parsedate_to_datetime
import httpx
from .connectivity import classify_error


def retry_seconds(value,default=0):
    try:
        number=float(value)
        return max(0,number) if math.isfinite(number) else default
    except (TypeError,ValueError):
        try:
            stamp=parsedate_to_datetime(value)
            if stamp.tzinfo is None:
                stamp=stamp.replace(tzinfo=timezone.utc)
            return max(0,(stamp-datetime.now(timezone.utc)).total_seconds())
        except (TypeError,ValueError,OverflowError):
            return default


def backoff_delay(attempt,provider_delay=0):
    exponential=min(30,2**max(1,attempt))
    return max(provider_delay,exponential+random.uniform(0,exponential*.25))


class InferenceError(RuntimeError):
    def __init__(self,message,status_code=None,retry_after=2,category=None):
        super().__init__(message)
        self.status_code=status_code
        self.provider_retry_after=max(0,float(retry_after))
        # Preserve the original bounded display field; scheduling respects the full provider delay.
        self.retry_after=min(max(self.provider_retry_after,1),30)
        self.category=category or ('http_'+str(status_code) if status_code else 'structured_response_error')
        self.retryable=status_code not in (401,403)


class Crusoe:
    def __init__(self):
        self.key=os.getenv('CRUSOE_API_KEY','')
        self.base=os.getenv('CRUSOE_BASE_URL','https://api.inference.crusoecloud.com/v1').rstrip('/')
        if self.base!='https://api.inference.crusoecloud.com/v1':
            raise ValueError('Crusoe endpoint must use the approved HTTPS host')
        self.model=os.getenv('CRUSOE_MODEL','')
        self.available_models=[]
        self.last_metadata={}
        self.cooldowns={}
        self.verification_attempts=[]

    async def models(self):
        if not self.key:
            raise InferenceError('CRUSOE_API_KEY is not configured',category='missing_credential')
        try:
            async with httpx.AsyncClient(timeout=20) as client:
                response=await client.get(self.base+'/models',headers={'Authorization':'Bearer '+self.key})
        except httpx.HTTPError as exc:
            raise InferenceError('Crusoe model discovery connection failed',category=classify_error(exc)) from None
        if response.status_code!=200:
            raise InferenceError('Crusoe model discovery HTTP '+str(response.status_code),response.status_code,
                                 retry_seconds(response.headers.get('retry-after')))
        try:
            self.available_models=[m['id'] for m in response.json()['data'] if isinstance(m.get('id'),str)]
        except (ValueError,KeyError,TypeError,AttributeError):
            raise InferenceError('Crusoe model discovery returned invalid metadata') from None
        return list(self.available_models)

    def candidates(self):
        configured=[m.strip() for m in os.getenv('CRUSOE_FALLBACK_MODELS','').split(',') if m.strip()]
        preferred=[self.model,*configured,'nvidia/Nemotron-3.5-Lightning-30B-A3B',
                   'zai-org/GLM-5.3-Flash','nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B',
                   'openai/gpt-oss-120b','deepseek-ai/Deepseek-V4-Flash']
        return list(dict.fromkeys(m for m in preferred if m and m in self.available_models))

    def select_model(self,failed_models=()):
        candidates=self.candidates()
        if not candidates:
            raise InferenceError('No configured model appears in Crusoe account discovery',category='model_unavailable')
        failed_families={m.split('/')[0] for m in failed_models}
        candidates=sorted(candidates,key=lambda m:m.split('/')[0] in failed_families)
        ready=[m for m in candidates if self.cooldowns.get(m,0)<=time.monotonic()]
        return next((m for m in ready if m not in failed_models),
                    next((m for m in candidates if m not in failed_models),ready[0] if ready else candidates[0]))

    def note_failure(self,model,exc):
        if getattr(exc,'status_code',None) in (404,429,503) or getattr(exc,'category','') in ('structured_response_error','output_limit'):
            self.cooldowns[model]=time.monotonic()+max(15,getattr(exc,'provider_retry_after',0))

    async def verify(self):
        await self.models()
        failed=[]
        for attempt in range(3):
            model=self.select_model(failed)
            try:
                result=await self.json('Return JSON only: {"connectivity":"ok"}.',{'purpose':'connectivity verification'},model=model)
                if result.get('connectivity')!='ok':
                    raise InferenceError('Crusoe JSON connectivity response failed validation')
                self.model=model
                return {'provider':'Crusoe Managed Inference','model':model,'json_verified':True,
                        'available_models':list(self.available_models),'verification_attempts':len(self.verification_attempts)+1}
            except InferenceError as exc:
                self.verification_attempts.append({'model':model,'category':exc.category,'http_status':exc.status_code})
                self.note_failure(model,exc);failed.append(model)
                if not exc.retryable or attempt==2:
                    raise
                delay=backoff_delay(attempt+1,exc.provider_retry_after)
                if delay>30:
                    raise
                await asyncio.sleep(delay)

    async def json(self,instruction,context,model=None):
        selected=model or self.model
        if not self.key or not selected:
            raise InferenceError('Crusoe credentials/model not configured; run connectivity verification',category='missing_configuration')
        started=time.monotonic()
        self.last_metadata={'model':selected,'status':'started',
                            'requested_thinking_disabled':'nemotron' in selected.lower() and os.getenv('CRUSOE_DISABLE_THINKING','1')=='1'}
        try:
            async with httpx.AsyncClient(timeout=40) as client:
                response=await client.post(self.base+'/chat/completions',
                    headers={'Authorization':'Bearer '+self.key},
                    json={'model':selected,'temperature':0.1,'max_tokens':8192,
                          'response_format':{'type':'json_object'},
                          **({'chat_template_kwargs':{'enable_thinking':False}} if 'nemotron' in selected.lower() and os.getenv('CRUSOE_DISABLE_THINKING','1')=='1' else {}),
                          'messages':[{'role':'system','content':instruction},
                                      {'role':'user','content':json.dumps(context,default=str)}]})
        except httpx.HTTPError as exc:
            raise InferenceError('Crusoe inference connection failed',category=classify_error(exc)) from None
        self.last_metadata.update(http_status=response.status_code,latency_ms=round((time.monotonic()-started)*1000))
        if response.status_code!=200:
            category={401:'authentication_failure',403:'authentication_failure',404:'model_unavailable',
                      429:'rate_limited'}.get(response.status_code,'provider_http_error')
            raise InferenceError('Crusoe inference HTTP '+str(response.status_code),response.status_code,
                                 retry_seconds(response.headers.get('retry-after')),category)
        try:
            payload=response.json();choice=payload['choices'][0]
            self.last_metadata['finish_reason']=choice.get('finish_reason')
            usage=payload.get('usage')
            self.last_metadata['usage']={k:v for k,v in (usage if isinstance(usage,dict) else {}).items()
                                         if k in ('prompt_tokens','completion_tokens','total_tokens') and isinstance(v,int)}
            content=choice['message']['content']
            if choice.get('finish_reason')=='length':
                raise InferenceError('Crusoe structured response exceeded output-token budget',category='output_limit')
            if isinstance(content,str) and content.strip().startswith('```json') and content.strip().endswith('```'):
                content=content.strip()[7:-3].strip()
            result=json.loads(content)
            if not isinstance(result,dict):
                raise ValueError()
            self.last_metadata['status']='succeeded'
            return result
        except (KeyError,IndexError,ValueError,TypeError):
            raise InferenceError('Invalid structured Crusoe response',category='structured_response_error') from None
