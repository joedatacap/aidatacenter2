"""Run before demo; outputs only sanitized connectivity metadata."""
import asyncio
import json
from neocloud.crusoe import Crusoe, InferenceError

async def main():
    try:
        print(json.dumps(await Crusoe().verify()))
    except (InferenceError, OSError) as exc:
        # Do not print raw SDK/network errors that might contain credentials.
        print(json.dumps({"verified": False, "reason": str(exc) if isinstance(exc,InferenceError) else "Network unavailable"}))
        raise SystemExit(1)

if __name__ == "__main__":
    asyncio.run(main())
