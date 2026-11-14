"""Android bridge for the original Atlas analysis runtime."""
import json
import os
import traceback

_runtime = None

def set_data_dir(path):
    os.makedirs(path, exist_ok=True)
    os.environ["HOME"] = path
    os.environ["XDG_CACHE_HOME"] = os.path.join(path, "cache")
    os.makedirs(os.environ["XDG_CACHE_HOME"], exist_ok=True)
    os.chdir(path)

def analyze(symbol):
    global _runtime
    try:
        if _runtime is None:
            from atlas_runtime import AtlasRuntime
            _runtime = AtlasRuntime()
        result = _runtime.analyze_symbol(str(symbol or "").strip(), force_refresh=True)
        return json.dumps({"ok": True, "data": result}, ensure_ascii=False, default=str)
    except Exception as exc:
        return json.dumps({
            "ok": False,
            "error": str(exc),
            "trace": traceback.format_exc(limit=8)
        }, ensure_ascii=False)
