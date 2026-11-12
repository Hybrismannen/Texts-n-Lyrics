#!/usr/bin/env python3
"""Källtroget index över unika textfiler. Standard library only.

Räknar en text per kanoniskt original, inte per filformat. Läskopior räknas aldrig
separat. Endast verifierbart likartade texter och uttryckligen namngivna
säkerhetskopior kan slås ihop. Alla ursprungliga filer bevaras i git.
"""
from __future__ import annotations
from collections import defaultdict
from difflib import SequenceMatcher
import csv
import hashlib
import json
import re
import unicodedata
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
ORIGINALS=ROOT/"originals"
READABLE=ROOT/"readable"
VARIANT_KEYS=("_versions","backup of","säkerhetskopia","alternate","_alternate")
EXTS={".txt",".doc",".docx",".rtf"}
MIN_TEXT_TOKENS=1
NEAR_SIMILARITY=0.93
MIN_NEAR_TOKENS=45

def rel(path:Path)->str:
    return path.relative_to(ROOT).as_posix()

def tokens(text:str)->list[str]:
    return re.findall(r"[^\W\d_]+(?:['’\-][^\W\d_]+)*",text.casefold(),re.UNICODE)

def normalized(text:str)->str:
    """Conservative equivalence: spacing, capitalization, Unicode normalization.
    Does not erase punctuation, meaning, stanzas, or alter actual source."""
    text=unicodedata.normalize("NFKC",text).casefold()
    text=text.replace("\ufeff","").replace("\u200b","").replace("\r","\n")
    text=re.sub(r"\s+"," ",text).strip()
    return text

def text_hash(text:str)->str:
    return hashlib.sha256(normalized(text).encode("utf-8")).hexdigest()

def shingle_set(words:list[str],n:int=5)->set[tuple[str,...]]:
    return {tuple(words[i:i+n]) for i in range(len(words)-n+1)}

def likeness(a:str,b:str)->float:
    x,y=tokens(a),tokens(b)
    if min(len(x),len(y))<MIN_NEAR_TOKENS:return 0
    if max(len(x),len(y))>min(len(x),len(y))*1.20:return 0
    sa,sb=shingle_set(x),shingle_set(y)
    overlap=len(sa & sb)
    return overlap/max(1,len(sa|sb))

def is_version(path:str)->bool:
    return any(p in path.casefold() for p in VARIANT_KEYS)

def title_key(path:str)->str:
    name=Path(path).stem
    name=re.sub(r"^(backup of|säkerhetskopia av|kopia av|copy of)\s*","",name,flags=re.I)
    name=re.sub(r"\s*[-_]\s*(alternate|alternative|backup|version\s*\d+|v\d+)\s*$","",name,flags=re.I)
    name=unicodedata.normalize("NFKD",name).casefold()
    name="".join(c for c in name if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9]+","",name)

def read_path(original:Path)->Path|None:
    candidate=READABLE / original.relative_to(ORIGINALS)
    tests=[Path(str(candidate)+".txt")]
    parts=original.relative_to(ORIGINALS).parts
    if "_versions" in parts or "_unclassified" in parts:
        tests.append(READABLE / parts[0] / (original.name+".txt"))
    if original.suffix.casefold()==".txt":
        tests.insert(0,original)
    for test in tests:
        if test.exists() and test.is_file():return test
    return None

def build(root:Path=ROOT)->dict:
    # root argument reserved for unit tests or copied archive roots.
    originals=sorted(x for x in (root/"originals").rglob("*") if x.is_file() and x.suffix.lower() in EXTS)
    readables=sorted(x for x in (root/"readable").rglob("*") if x.is_file() and x.suffix.lower()==".txt")
    # For reproducibility, path resolution follows root rather than process cwd.
    records=[]
    for path in originals:
        raw=path.relative_to(root).as_posix()
        relparts=path.relative_to(root/"originals").parts
        tests=[root/"readable"/Path(*relparts[:-1])/(relparts[-1]+".txt")]
        if len(relparts)>2 and relparts[1] in ("_versions","_unclassified"):
            tests.append(root/"readable"/relparts[0]/(relparts[-1]+".txt"))
        if path.suffix.casefold()==".txt":tests.insert(0,path)
        # Source filenames were renamed on import; these mapping exceptions are verified
        # against the original archive's exported readable text files.
        raw_key=path.relative_to(root).as_posix()
        renamed={
            "originals/lyrics/Untitled-archive-01.rtf":"readable/lyrics/----.rtf.txt",
            "originals/lyrics/_versions/Summer breeze - alternate.docx":"readable/lyrics/Summer breeze.docx.txt",
        }
        if raw_key in renamed:tests.insert(0,root/renamed[raw_key])
        text_path=next((p for p in tests if p.exists() and p.is_file()),None)
        body=text_path.read_text(encoding="utf-8-sig",errors="replace") if text_path else ""
        norm=normalized(body)
        record={"original":raw,"readable":text_path.relative_to(root).as_posix() if text_path else None,
                "text_hash":hashlib.sha256(norm.encode()).hexdigest() if norm else None,
                "tokens":len(tokens(body)),"source_text":body,
                "is_version":is_version(raw),"title_key":title_key(raw),
                "status":"pending","canonical":None,"similarity":None}
        if record["tokens"]<MIN_TEXT_TOKENS or not norm:record["status"]="unreadable_or_too_short"
        records.append(record)
    # Higher-priority originals take precedence over explicitly marked backups.
    candidates=sorted([r for r in records if r["status"]=="pending"],key=lambda r:(r["is_version"],r["original"]))
    canonical=[]
    by_hash={}
    merged=[]
    for record in candidates:
        parent=None;reason=None;similarity=1.0
        if record["text_hash"] in by_hash:
            parent=by_hash[record["text_hash"]];reason="same_normalized_text"
        else:
            # Safe high-overlap heuristic: most five-token sequences must match.
            for other in canonical:
                if abs(record["tokens"]-other["tokens"])>max(20,other["tokens"]*0.20):continue
                similarity=likeness(record["source_text"],other["source_text"])
                if similarity>=NEAR_SIMILARITY:
                    parent=other;reason="near_identical_text";break
            if parent is None and record["is_version"]:
                peers=[o for o in canonical if o["title_key"]==record["title_key"]]
                if peers:
                    parent=peers[0];reason="explicit_named_version";similarity=likeness(record["source_text"],parent["source_text"])
        if parent is not None:
            record["status"]="duplicate_or_version";record["canonical"]=parent["original"]
            record["reason"]=reason;record["similarity"]=round(similarity,4)
            merged.append(record)
        else:
            record["status"]="canonical";record["canonical"]=record["original"]
            record["reason"]="unique_source_text";record["similarity"]=1.0
            canonical.append(record)
            by_hash[record["text_hash"]]=record
    # Includes files without usable text separately, but not among unique texts.
    unreadable=[r for r in records if r["status"]=="unreadable_or_too_short"]
    groups=defaultdict(list)
    for record in records:
        if record["status"]!="unreadable_or_too_short":
            groups[record["canonical"]].append(record["original"])
    for record in records: record.pop("source_text",None)
    return {"definition":"One canonical, non-empty original text per normalized textual identity. "
                         "Strong near-identical sources and explicit backups/versions collapse into canonical. "
                         "Unreadable sources remain uncounted and visible. Editorial-only copies are excluded.",
            "source_files":len(records),"readable_files":len(readables),"canonical_unique_texts":len(canonical),
            "excluded_duplicate_or_version":len(merged),"unreadable_or_too_short":len(unreadable),
            "editorial_only_files":sum("_editorial" in p.parts for p in readables),
            "other_readable_file_count":len(readables)-sum("_editorial" in p.parts for p in readables),
            "records":records,"groups":[{"canonical":k,"members":v} for k,v in sorted(groups.items())],
            "unmatched_text_files":len(readables)-sum(r["readable"] is not None and r["readable"].startswith("readable/") for r in records)}

def export(index:dict,folder:Path)->None:
    folder.mkdir(parents=True,exist_ok=True)
    (folder/"unique_text_index.json").write_text(json.dumps(index,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    with (folder/"unique_text_index.csv").open("w",encoding="utf-8",newline="") as fp:
        wr=csv.writer(fp)
        wr.writerow(["original","readable","status","canonical","reason","similarity","tokens","text_sha256"])
        wr.writerows([r["original"],r["readable"] or "",r["status"],r["canonical"] or "",
                      r.get("reason",""),r["similarity"] if r["similarity"] is not None else "",
                      r["tokens"],r["text_hash"] or ""] for r in index["records"])

if __name__=="__main__":
    index=build();export(index,ROOT/"analytics")
    print(json.dumps({k:v for k,v in index.items() if k not in ("records","groups")},ensure_ascii=False,indent=2))
