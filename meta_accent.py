"""Meta-accentor: base stressonnx/ruaccent + clause-scoped collocations + defaults + overrides (from stress_data.json)."""
import json, os, re
_DATA_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "stress_data.json")
def _load():
    with open(_DATA_PATH, encoding="utf-8") as f: return json.load(f)
_D = _load()
OVERRIDES = _D["overrides"]; HOMO_COLLOC = _D["homographs"]; DEFAULT = _D.get("defaults", {})
HOMO_COLLOC = {k: dict(v) for k,v in HOMO_COLLOC.items()}
def base_stress(text):
    from stressonnx import stress
    return stress(text, "ru", model="ruaccent", notation="plus")
def _cyr(c): return ("а"<=c.lower()<="я") or c in "ёЁ"
def _apply_form(form, w):
    if not form: return w
    if w and w[0].isupper(): return form[0].upper()+form[1:]
    return form
def _idx(form):
    m=re.match(r"^([А-Яа-яЁё]*)\+", form)
    return len(m.group(1)) if m else None
def _set(idx, w):
    bare=w.replace("+","")
    if idx is None or idx<0 or idx>=len(bare): return w
    return bare[:idx]+"+"+bare[idx:]
def _tokenize(s):
    toks=[]; i=0; n=len(s)
    while i<n:
        c=s[i]
        if _cyr(c):
            j=i
            while j<n and (_cyr(s[j]) or s[j]=="+"): j+=1
            toks.append(s[i:j]); i=j
        elif c=="+" and i+1<n and _cyr(s[i+1]):
            j=i+1
            while j<n and (_cyr(s[j]) or s[j]=="+"): j+=1
            toks.append(s[i:j]); i=j
        else:
            j=i
            while j<n:
                if _cyr(s[j]): break
                if s[j]=="+" and j+1<n and _cyr(s[j+1]): break
                j+=1
            toks.append(s[i:j]); i=j
    return toks
def _clauses(text):
    return [re.findall(r"[А-Яа-яЁё]+", p) for p in re.split(r"[,.!?;:…—]+", text)]

def accent(text):
    out=base_stress(text)
    toks=_tokenize(out)
    in_words=re.findall(r"[А-Яа-яЁё]+", text)
    clauses=_clauses(text)
    wmap=[]
    for ci,cl in enumerate(clauses):
        for _w in cl: wmap.append(ci)
    wi=0; res=[]
    for tok in toks:
        bare=tok.replace("+","")
        is_word=bool(bare) and all(_cyr(c) or c in "ёЁ" for c in bare)
        if is_word and wi < len(in_words):
            low=in_words[wi].lower(); nt=tok
            if low in OVERRIDES:
                nt=_apply_form(OVERRIDES[low], in_words[wi])
            elif (low in HOMO_COLLOC or low in DEFAULT) and wi < len(wmap):
                ci=wmap[wi]; ctx=" ".join(w.lower() for w in clauses[ci])
                cur=_idx(tok); fired=False
                for cue,form in HOMO_COLLOC.get(low,{}).items():
                    if cue in ctx:
                        ix=_idx(form)
                        if ix is not None and ix!=cur: nt=_set(ix, in_words[wi])
                        fired=True; break
                if not fired and low in DEFAULT:
                    ix=_idx(DEFAULT[low])
                    if ix is not None and ix!=cur: nt=_set(ix, in_words[wi])
            res.append(nt); wi+=1
        else:
            res.append(tok)
    return "".join(res)
