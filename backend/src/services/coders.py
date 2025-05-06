"""
RxNorm and ICD code lookup agents
"""
from abc import ABC, abstractmethod
import asyncio
import json
from pprint import pprint
import random
import urllib.parse

from anyio import Semaphore
import httpx

from src._logging import get_logger
from src.services.schema import CodeLookupAction, CodeLookupActions, CodeLookupResult, CodeSystem
from src.utils import retry

logger = get_logger(__name__)

class CodeLookupAPI(ABC):
    """
    Base API lookup class. Basic flow is to take an item, feed it to the corresponding API and return the code if it exists. 
    """
    def __init__(self):
        super().__init__()
        self.semaphore = Semaphore(2)

    @abstractmethod
    async def lookup(self, names: list[str]) -> CodeLookupResult | None:
        pass

    @abstractmethod
    def _get_api_lookup_url(self, term: str) -> str:
        pass

    @retry
    @abstractmethod
    async def _make_api_call_internal(self, client: httpx.AsyncClient, url: str):
        pass

    async def _make_api_call(self, url: str) -> CodeLookupResult | None:
        logger.debug(f"{url}")

        async with self.semaphore:
            async with httpx.AsyncClient(timeout=20) as client:
                try:
                    r = await self._make_api_call_internal(client, url)
                except Exception as ex:
                    logger.exception("coder api call failed", ex)
                    r = None

                await asyncio.sleep(.5 + random.random() * .75 + .5)

                return r
            
    async def lookup(self, name: str) -> CodeLookupResult | None:
        """
        looks up the code information for each of the names in sequential order
        shortcircuits after the first successful result
        """
        url = self._get_api_lookup_url(name)
        lookup = await self._make_api_call(url)

        if lookup is not None:
            return lookup

        return None

class RxNormAPI(CodeLookupAPI):
    def __init__(self):
        super().__init__()

    def _get_api_lookup_url(self, term: str) -> str:
        query_payload = {
            "term": term,
            "maxEntries": 5,
        }
        query_str = urllib.parse.urlencode(query_payload)
        return f"https://rxnav.nlm.nih.gov/REST/approximateTerm.json?{query_str}"

    async def _make_api_call_internal(self, client: httpx.AsyncClient, url: str):
        response = await client.get(url)
        if response.status_code != 200:
            return None

        rjson = json.loads(response.text)

        # https://lhncbc.nlm.nih.gov/RxNav/APIs/api-RxNorm.getApproximateMatch.html                        
        for c in rjson.get('approximateGroup').get('candidate') or []:
            if not (c.get('rxcui') and c.get('name')):
                continue

            return CodeLookupResult.rxnorm(name = c['name'].strip(), code = c['rxcui'].strip())

        return None
    

class ICDApi(CodeLookupAPI):

    def __init__(self):
        super().__init__()

    def _get_api_lookup_url(self, term: str) -> str:
        # https://clinicaltables.nlm.nih.gov/apidoc/icd10cm/v3/doc.html
        query_payload = {
            "ICD10Search": term,
        }
        query_str = urllib.parse.urlencode(query_payload)
        url = f"https://icd.mediware.com/api/ICD10/Find?{query_str}"
        return url

    async def _make_api_call_internal(self, client: httpx.AsyncClient, url: str):
        response = await client.get(url)
        if response.status_code != 200:
            return None

        rjson = json.loads(response.text)
        if rjson is None:
            return None

        for c in rjson.get('ICD10Codes') or []:
            if not (c.get('ICD10Code') and c.get('Description')):
                continue

            return CodeLookupResult.icd(name = c['Description'].strip(), code = c['ICD10Code'].strip())
        
        return None

APIS: dict[CodeSystem, CodeLookupAPI] = {
    CodeSystem.ICD: ICDApi(),
    CodeSystem.RXNORM: RxNormAPI(),
}

async def run_code_lookup_action(concept: CodeLookupAction) -> CodeLookupResult | None:
    api = APIS.get(concept.system)
    if not api:
        raise ValueError(f"No api for concept: {concept}")
    
    lookup = await api.lookup(concept.name)
    return lookup


if __name__ == "__main__":
    pass

