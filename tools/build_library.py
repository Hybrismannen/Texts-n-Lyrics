#!/usr/bin/env python3
"""Build a verifiable, source-linked, multilevel literary atlas. No external dependencies."""
import csv
import json
import math
import re
import sys
from pathlib import Path
from collections import Counter, defaultdict
from urllib.parse import quote
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"tools"))
import analyze_archive as A
from unique_texts import build as build_unique_index
BASE="https://github.com/Hybrismannen/Texts-n-Lyrics/blob/main/"
OUT=ROOT/"docs"/"data"
def rel(p):return p.relative_to(ROOT).as_posix()
def link(p):return BASE+quote(p,safe="/")
def tokens(s):return A.tokens(s)
def canonic(name):
    return re.sub(r"[^a-z0-9]+","",name.casefold().replace("å","a").replace("ä","a").replace("ö","o"))
def collect_refs():
    names=[];p=ROOT/"catalog"/"chat-register-2024-2026.md"
    if p.exists():
        for line in p.read_text(encoding="utf-8").splitlines():
            m=re.match(r"^\s*\d+\.\s+(.+?)\s*$",line)
            if m:names.append(m.group(1).split(" — fulltext")[0])
    return names
def get_text(original):
    r=rel(original)
    if original.suffix.lower()==".txt" and original.parts[-2] in ("other","chat-poetry"):
        return original.read_text(encoding="utf-8-sig",errors="replace"),r,True
    readable=ROOT/"readable"/Path(*original.relative_to(ROOT/"originals").parts)
    readable=Path(str(readable)+".txt")
    if readable.exists():
        return readable.read_text(encoding="utf-8-sig",errors="replace"),rel(readable),True
    return "",None,False
def artist_routing(title,text,path):
    lower=(title+"\n"+text).casefold()
    explicit=[]
    if re.search(r"\bdaddy[\s-]+ferma\b|\bferma\b",lower) or "ferma dj" in path.casefold():
        explicit.append("daddy-ferma")
    if "lyrical-bonde" in path.casefold() or "lyrical bonde" in lower:
        explicit.append("lyrical-bonde")
    if "trubadur o" in lower:
        explicit.append("trubadur-o")
    if "hy the man" in lower:
        explicit.append("hy-the-man")
    # Author name is not a performance persona. These are two different dimensions.
    literary = path.startswith(("originals/poetry/","originals/other/","originals/chat-poetry/"))
    authorial_voice = "linus-fast" if literary and not explicit else None
    return sorted(set(explicit)),authorial_voice
def editorial(path,title,text):
    low=(path+" "+title).casefold()
    manual=[
      ("höströst",["Politisk allegori","Satir","Kollektivt val"],"Väljarens relation till politiska alternativ","Skog och svampar som politisk allegori"),
      ("social gravitation",["Migration","Gemenskap","Gränser"],"Social sammanhållning och exkludering","Gravitation som social metafor"),
      ("more than ever",["Rasism","Solidaritet","Jämlikhet"],"Antirasistisk kollektiv mobilisering","Direkt moraliskt och politiskt tilltal"),
      ("to narrow",["Unga","Ojämlikhet","Delaktighet"],"Livsvillkor och politisk inkludering","Frågan som refräng"),
      ("stock market",["Ekonomi","Ojämlikhet","Kapital"],"Vem får nytta av marknadens logik?","Ekonomisystem genom vardagsnära kontraster"),
      ("periodiska systemfel",["Makt","Propaganda","Politik"],"Sociala och strukturella maktfel","Ordspel och vintermetaforer"),
      ("we are the fungi",["Natur","Gemenskap","Ekologi"],"Ömsesidigt beroende","Mycel som nätverksbild"),
      ("oral quest",["Kunskap","Frågor","Existens"],"Frågandet som livshållning","Repetition av en frågande röst"),
      ("skrattkommit",["Humor","Social gemenskap"],"Skrattets sociala funktion","Kommittén som personifiering"),
      ("pikant är livet",["Kärlek","Existens","Absurdism"],"Kärlek i en absurd värld","Kontrast mellan högtid och vardag"),
      ("the hy the man",["Myter","Identitet","Tävling"],"Kampen om ett artistnamn","Pegasus och självmytologisering"),
      ("the hatter",["Artistidentitet","Tillhörighet","Nationalism"],"Stil och motstånd mot snäv identitet","Hatten som identitetsmarkör")
    ]
    for term,tags,focus,trope in manual:
        if term in low:return {"status":"editorial_interpretation","themes":tags,"focus":focus,"figure_or_image":trope}
    return None
def profile_entry(key,records,wordcounts,source_registry):
    if key=="linus-fast":
        active=records
        stated="Arkivets författar-/upphovsnivå; ingår samtliga textkällor med förbehåll för upphovsgranskning."
    else:
        active=[r for r in records if key in r["performer_ids"]]
        stated="Endast uttryckligen källbelagda namn i titel/text/arkivnamn. Detta är inte en bedömning av juridiskt upphov."
    counter=Counter(); theme=Counter();subject=Counter(); genres=Counter()
    for r in active:
        counter.update(wordcounts.get(r["id"],{}))
        genres[r["genre"]]+=1
        theme.update(r["auto_themes"])
        subject.update(r["auto_subjects"])
    n=sum(counter.values())
    top=[{"word":w,"count":c,"per1000":round(c/max(1,n)*1000,2)} for w,c in counter.most_common() if w not in A.STOP and len(w)>2][:35]
    distinct=[{"word":w,"count":c,"per1000":round(c/max(1,n)*1000,2)} for w,c in counter.most_common() if len(w)>2 and w not in A.STOP]
    return {"id":key,"size":len(active),"tokens":n,"description":stated,"genre_distribution":genres,"theme_distribution":theme,
            "topic_distribution":subject,"top_content_words":top,"profile_words":distinct[:100],
            "works":[r["id"] for r in active],"coverage":"author_archive" if key=="linus-fast" else "explicit_performer_reference"}
def extract_segments(text,path):
    # Source verified: Lyrical Bonde Rhymes.doc contains six titled/identifiable pieces.
    if Path(path).name!="Lyrical Bonde Rhymes.doc":return []
    markers=[
      ("Dosh (tidigt utkast)",r"(?m)^intro\s*$"),
      ("Lyrical Bonde – Killa",r"(?m)^Lyrical Bonde\s*-\s*Killa!!"),
      ("Lyrical Bonde – Ta Ta",r"(?m)^Lyrical Bonde\s*-\s*Ta Ta"),
      ("Homo reggae (arbetsrubrik)",r"(?m)^Homo reggae!!!"),
      ("Lyrical Bonde – Första battlen",r"(?m)^Lyrical Bonde\s*-\s*första battlen ever"),
      ("Lyrical Bonde – Bubble tribute",r"(?m)^Lyrical Bonde\s*[–-]\s*Bubble tribute")
    ]
    found=[]
    for title,pattern in markers:
        m=re.search(pattern,text,re.I)
        if m:found.append((m.start(),title))
    found.sort()
    if len(found)<5:return []
    result=[]
    for i,(pos,title) in enumerate(found):
        excerpt=text[pos:found[i+1][0] if i+1<len(found) else None].strip()
        if len(tokens(excerpt))>=25:result.append({"title":title,"text":excerpt,"start":pos})
    return result
def main():
    unique_index=build_unique_index()
    canonical_records=[r for r in unique_index["records"] if r["status"]=="canonical"]
    original_paths=[ROOT/r["original"] for r in canonical_records]
    index_by_original={r["original"]:r for r in canonical_records}
    readable_paths=sorted([p for p in (ROOT/"readable").rglob("*") if p.is_file()])
    documents=[];wordcounts={};subworks=[];missing=[];mappings=[]
    for index,p in enumerate(original_paths,1):
        raw=rel(p)
        provenance=index_by_original[raw]
        rpath=provenance["readable"]
        ok=bool(rpath)
        text=(ROOT/rpath).read_text(encoding="utf-8-sig",errors="replace") if rpath else ""
        if not ok:missing.append(raw)
        title=p.stem
        if p.suffix.lower()==".txt":title=p.name[:-4]
        x=tokens(text);count=Counter(x)
        lineage="variant" if "/_versions/" in raw else "unclassified" if "/_unclassified/" in raw else "source"
        ids,literary=artist_routing(title,text,raw)
        structure=extract_segments(text,raw)
        genre=A.FAMILY.get(p.relative_to(ROOT/"originals").parts[0],p.parent.name)
        auto_themes=A.tags(text,A.THEMES) if text else {}
        auto_subjects=A.tags(text,A.SUBJECTS,2,2) if text else {}
        editorial_note=editorial(raw,title,text)
        document={
          "id":f"source-{index:03d}","title":title,"original":raw,"readable":rpath,
          "original_url":link(raw),"text_url":link(rpath or raw),
          "genre":genre,"source_group":p.relative_to(ROOT/"originals").parts[0],
          "role":lineage,"text_status":"full_text" if ok else "unparsed_binary",
          "performer_ids":ids,"literary_voice":literary,
          "tokens":len(x),"types":len(count),"lexical_diversity":round(len(count)/max(1,len(x)),4),
          "hapax":sum(1 for n in count.values() if n==1),
          "lines":sum(bool(s.strip()) for s in text.splitlines()),
          "unique_line_tokens":len(tokens("\n".join(dict.fromkeys(s.strip().casefold() for s in text.splitlines() if s.strip())))),
          "auto_themes":auto_themes,"auto_subjects":auto_subjects,
          "editorial":editorial_note,"top_words":count.most_common(20),
          "container_segments":len(structure),"snippet":re.sub(r"\s+"," ",text)[:240], "full_text":text
        }
        documents.append(document);wordcounts[document["id"]]=count
        mappings.append({"source":raw,"readable":rpath,"status":document["text_status"],"segments_detected":len(structure)})
        for i,segment in enumerate(structure,1):
            subtokens=tokens(segment["text"]);subworks.append({
              "id":f"fragment-{index:03d}-{i:02d}","title":segment["title"],"source_id":document["id"],
              "source":raw,"text_url":link(rpath or raw),"text_status":"extracted_section",
              "editorial_status":"inferred_heading_requires_review","tokens":len(subtokens),
              "performer_ids":["lyrical-bonde"],"full_text":segment["text"],
              "genre":"Svensk rap / visa (samlingsdokument)"})
    # Figures in separately editorial-transcribed texts may be visible but are not counted as source.
    editorial_entries=[]
    for p in sorted((ROOT/"readable"/"chat-poetry"/"_editorial").glob("*.txt")):
        editorial_entries.append({"title":p.stem,"path":rel(p),"status":"editorial_transcription_not_original","url":link(rel(p))})
    existing_titles={canonic(r["title"]) for r in documents}
    pending=[]
    for title in collect_refs():
        name=title.split(" — ")[0]
        pending.append({"title":title,"status":"register_reference","possibly_in_sources":canonic(name) in existing_titles})
    all_files=sorted([p for p in ROOT.rglob("*") if p.is_file() and ".git" not in p.parts and not (p.parts and "docs" in p.parts and "data" in p.parts)])
    inventory=[]
    for p in all_files:
        key=rel(p)
        role="source" if key.startswith("originals/") else "readable_copy" if key.startswith("readable/") else "analysis_data" if key.startswith("analytics/") else "catalog_or_wiki" if key.startswith(("catalog/","wiki/")) else "site_or_code"
        inventory.append({"path":key,"role":role,"bytes":p.stat().st_size,"url":link(key)})
    alias_info=[
      {"id":"linus-fast","title":"Linus Fast","kind":"arkivets författarnamn","role":"archival_author"},
      {"id":"daddy-ferma","title":"Daddy Ferma","kind":"MC/artistpersona","role":"performer"},
      {"id":"lyrical-bonde","title":"Lyrical Bonde","kind":"rap-/lyrikpersona","role":"performer"},
      {"id":"trubadur-o","title":"Trubadur O","kind":"litterär persona","role":"performer"},
      {"id":"hy-the-man","title":"The Hy The Man","kind":"litterär persona","role":"performer"},
      {"id":"abnocal","title":"Abnocal","kind":"DJ-/musikprofil, inga verifierade lyriktillskrivningar","role":"external_music_identity"},
      {"id":"senor-dia-y-noche","title":"Señor Día y Noche","kind":"DJ-profil, inga verifierade lyriktillskrivningar","role":"external_music_identity"},
      {"id":"sublime-groove","title":"Sublime Groove","kind":"DJ-profil, inga verifierade lyriktillskrivningar","role":"external_music_identity"},
    ]
    artists={}
    for artist in alias_info:
        artists[artist["id"]]=profile_entry(artist["id"],documents,wordcounts,original_paths)
    for r in documents:
        if r["role"]=="variant":continue
        if "lyrical-bonde" in r["performer_ids"]:pass
    genre=Counter(r["genre"] for r in documents)
    themes=Counter(k for r in documents for k in r["auto_themes"])
    subjects=Counter(k for r in documents for k in r["auto_subjects"])
    lexical=Counter()
    for count in wordcounts.values():lexical.update(count)
    duplicates=defaultdict(list)
    for r in documents:
        norm=re.sub(r"\s+","",r["full_text"]).casefold()
        if norm:duplicates[__import__("hashlib").sha256(norm.encode()).hexdigest()].append(r["id"])
    duplicate_sets=[v for v in duplicates.values() if len(v)>1]
    summary={
      "original_files":len(original_paths),"physical_original_files":unique_index["source_files"],
      "canonical_unique_texts":len(original_paths),
      "excluded_duplicate_or_version":unique_index["excluded_duplicate_or_version"],
      "readable_copies":len(readable_paths),"analyzed_source_files":len(documents)-len(missing),
      "missing_readable":len(missing),"register_references":len(pending),
      "physical_text_files":unique_index["source_files"]+len(readable_paths),
      "detected_subworks_in_compilations":len(subworks),
      "potential_work_units":len(documents)+sum(max(0,r["container_segments"]-1) for r in documents),
      "count_note":"The 117 canonical unique source texts are deduplicated. Subworks in collection files are not added to the main count. This is not a verified count of distinct literary works.",
      "editorial_transcriptions":len(editorial_entries),"word_tokens":sum(r["tokens"] for r in documents),
      "distinct_wordforms":len(lexical),"duplicate_source_sets":[g["members"] for g in unique_index["groups"] if len(g["members"])>1],
      "source_genres":dict(genre),"theme_document_frequency":dict(themes),"subject_document_frequency":dict(subjects),
      "top_words":lexical.most_common(100),
      "top_content_words":[[w,n] for w,n in lexical.most_common() if w not in A.STOP and len(w)>2][:100],
      "inventory_filenames":len(inventory)}
    corpus={
      "schema_version":"2.1","definitions":{"count_unit":"canonical unique source text, not physical file","aliases":"explicit name detection; archive author separate",
      "automatic_themes":"2 distinct keyword markers and 3 hits","wordforms":"casefold exact tokens; no lemmatization",
      "subworks":"collection-title-bounded extracts, provisional until editorial check"},
      "summary":summary,"documents":documents,"subworks":subworks,
      "pending_chat_titles":pending,"editorial_transcriptions":editorial_entries,
      "artists":artists,"artist_metadata":alias_info,"inventory":inventory,
      "lineage":unique_index["records"]}
    OUT.mkdir(parents=True,exist_ok=True)
    (OUT/"atlas.json").write_text(json.dumps(corpus,ensure_ascii=False,separators=(",",":"))+"\n",encoding="utf-8")
    (OUT/"README.md").write_text("# Dashboard-datakälla\n\n**Endast kanoniskt unika textkällor** analyseras. Original, dubblett, alternativversion och läskopia hålls separata i analytics/unique_text_index.json. Inga saknade original rekonstrueras. Statistik byggs av analyze_archive.py och build_library.py från samma unika register.\n",encoding="utf-8")
    with (OUT/"source_audit.csv").open("w",encoding="utf-8",newline="") as f:
        w=csv.writer(f);w.writerow(["original","readable","status","canonical","reason"]);w.writerows([[x["original"],x["readable"] or "",x["status"],x["canonical"] or "",x.get("reason","")] for x in unique_index["records"]])
    with (OUT/"all_files.csv").open("w",encoding="utf-8",newline="") as f:
        w=csv.writer(f);w.writerow(["path","role","bytes","github_url"]);w.writerows([x.values() for x in inventory])
    print(json.dumps({k:summary[k] for k in ["original_files","readable_copies","analyzed_source_files","missing_readable","detected_subworks_in_compilations","potential_work_units","word_tokens","distinct_wordforms","register_references"]},ensure_ascii=False))
if __name__=="__main__":main()
