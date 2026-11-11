#!/usr/bin/env python3
"""Texts-n-Lyrics: reproducible, source-linked corpus analysis. Standard library only."""
from __future__ import annotations
import csv
import json
import re
import hashlib
from html import escape as xml_escape
from pathlib import Path
from collections import Counter, defaultdict
from datetime import datetime, timezone
from urllib.parse import quote

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "analytics"
WIKI = ROOT / "wiki"
REPO = "https://github.com/Hybrismannen/Texts-n-Lyrics"
TOKEN = re.compile(r"[^\W\d_]+(?:['’\-][^\W\d_]+)*", re.UNICODE)
META = re.compile(r"^(?:(?:v|vers|verse)\s*\d+|intro|outro|bridge|brygga|(?:chorus|ref|refräng)\s*(?:\d+|[xX]\s*\d+|2x)?\s*:?)$", re.I)
FAMILY = {
 "poetry": "Dikt och prosalyrik", "lyrics": "Musiklyrik / dancehall-reggae (blandat)",
 "recording": "Inspelningslyrik (blandat)", "grime": "Grime / junglist",
 "lyrical-bonde": "Svensk rap / visa", "songs": "Fristående låtprojekt",
 "dubplates": "Dubplate", "misc": "Övrig sångtext", "other": "Fristående text",
 "chat-poetry": "Dikt i samtalsarkiv"
}
STOP = set(("a an the this that these those to from for by in on into at as and or if but is are was were be being been i me my mine we us our you your they them their it its he she him her his when who whom where what why which how can could would should may do does did not no yes all one two there here any some such more many much only very just so too up down out over under now then as of with will have has had get got go going come make made see say said know like really ever even much every each than true well also oh ah yeah hey people di mi yuh dem inna pon fi seh caw nuh gwaan wid uno dat deh wah waah likkle bwy gal gyal haffi mek tink me a de and suh nuh all dat be come on is to it i a an of our we at for and so in on deh did a make as in one when can he they who a is it the of we are no yes how more was be have was by had you like know but i if just no oh for as what who why your to we now is dat di weh me do it of that they with all more one two a en ett och det den den här där du jag vi ni han hon sig sin sina på av för till med mellan efter före utan om när var är blir blev kan ska skulle har hade måste vill att som de dem ett en är var så nu då ju bara väl alltid aldrig nog mer detta dessa enligt över under kring fram och nu").split())
DIALECT = set("mi yuh dem di inna pon fi seh caw nuh gwaan wid uno dat deh wah waah likkle bwy gal gyal haffi mek tink cyaan neva bredda duppy selecta riddim".split())
THEMES = {
 "Kärlek och relationer": "love loving lovin lover lovely heart hearts romance romantic passion desire longing darling beloved kiss kissing kärlek kyss älskling passion förälskad".split(),
 "Musik, ljud och dans": "music musical dance dancing dancehall riddim bass bassline lyrics lyric song songs tune tunes sound soundsystem selecta dj mic microphone junglist dubplate reggae beat beats drum drums rhythm sång dans musik".split(),
 "Solidaritet och gemenskap": "together community solidarity solidary unity support helping help collective social friends friendship society everybody togetherness gemenskap solidaritet tillsammans kollektivt".split(),
 "Politik, makt och ojämlikhet": "power politician politicians government state racist racism inequality unequal wealth poverty poor rich profit market bank stock politics political democracy democratic makt politik fattigdom ojämlikhet demokrati".split(),
 "Konflikt, hot och våld": "war wars gun gunshot blood bloody kill killing killer murder murda death dead violence violent attack crime clash fight shoot fighting skott våld krig död".split(),
 "Tid, minne och förändring": "time times history memory memories future past tomorrow yesterday season change changes age years year moment earlier later tid tiden minne minnen framtid historia år".split(),
 "Natur, rum och kosmos": "sun moon sky tree trees forest flower winter summer star stars space universe earth sea ocean nature rain wind natur skog svamp måne sol himmel universum vinter sommar".split(),
 "Liv, existens och identitet": "life living live human humanity identity existence soul spirit mind body meaning freedom liberty living liv livet människa mänsklighet identitet mening frihet själ".split(),
 "Vardag, hem och arbete": "work working job jobs home house household family parents parent food money rent school street yard workplace arbete hem familj pengar skola vardag".split(),
 "Språk, kunskap och tänkande": "word words language talk speech think thinking thought question questions answer answers knowledge reason logic truth fact facts story stories berättelse fråga frågor sanning språk kunskap".split(),
}
SUBJECTS = {
 "Rasism och diskriminering": "racism racist race nationalism nationalist discrimination discriminatory ethnicity etnicity fördom diskriminering rasism".split(),
 "Ekonomi, marknad och klass": "money bank banks stock market poor poverty rich wealth wages profit kapital pengar fattigdom ekonomi".split(),
 "Kärlek och partnerskap": "love loving lovin romance heart heartache partner lovers kärlek älskling kyss".split(),
 "Musik, scen och ljud": "riddim music lyrics tune selecta dancehall sound soundsystem dubplate bassline microphone mic drum reggae".split(),
 "Barn, familj och föräldraskap": "child children kids pickney parent parents parenting mummy mother father daughter son barn föräldr föräldrar".split(),
 "Teknik och digitalisering": "computer digital internet network facebook instagram algorithm algorytm modem technology teknolog data bionic digitalisering".split(),
 "Krig och våld": "war murder kill killing blood gun violence violent krig våld död".split(),
 "Resor och geografi": "travel journey trip train tram station city sweden stockholm gothenburg malmö journey resa tåg stad resor".split(),
 "Natur, väder och årstider": "summer winter forest earth tree sun moon flower weather snow skog svamp sol måne natur".split(),
 "Rättvisa och välfärd": "fairness justice injustice equality equal rights support welfare solidarity rättvisa jämlikhet solidaritet".split(),
}
FIGURES = {
 "Daddy Ferma": ("artistpersona", ["daddy ferma"]),
 "Peter Pan-ta": ("fiktiv figur", ["peter pan-ta", "pan-ta mera"]),
 "Mr Pan": ("fiktiv/litterär figur", ["mr pan"]),
 "Klara": ("namngiven person i text", ["klara"]),
 "Santa": ("kulturfigur", ["santa", "santas"]),
 "Trubadur O": ("fiktiv figur", ["trubadur o", "trubaduren o"]),
 "The Hatter": ("artistpersona/figur", ["the hatter"]),
 "The Hy The Man": ("artistpersona/figur", ["the hy the man"]),
 "Pegasus": ("mytologisk figur", ["pegasus"]),
 "Icarus": ("mytologisk figur", ["icarus"]),
 "Captain Kirk": ("kulturell referens", ["captain kirk"]),
 "Captain Picard": ("kulturell referens", ["captain picard", "captain pickard"]),
 "Jim Crow": ("historisk referens", ["jim crow"]),
 "Steve Urkel": ("kulturell referens", ["steve urkle", "steve urkel"]),
 "Fred Astaire": ("kulturell referens", ["fred astair", "fred astaire"]),
 "Eek-A-Mouse": ("artistreferens", ["eek-a-mouse", "eek-amouse"]),
 "Jah Cure": ("artistreferens", ["jah cure"]),
}
KEYWORDS = ["love", "life", "people", "music", "power", "time", "world", "system", "community", "sound", "riddim", "kärlek", "frihet", "makt", "människa"]
GROUPS = {
 "Love / loving": "love loving lovin lover lovemaking lovely kärlek älskling".split(),
 "Life / livity": "life live living livity livet liv".split(),
 "Sound / soundsystem": "sound sounds soundsystem soundbwy selecta".split(),
 "Music / musical": "music musical musik".split(),
 "Power / makt": "power powa makt".split(),
 "Society / social": "society social community samhälle gemenskap".split(),
 "War / violent": "war wars violence violent krig våld".split(),
}

def tokens(s: str) -> list[str]:
    return TOKEN.findall(s.casefold())
def link(path: str) -> str:
    return REPO + "/blob/main/" + quote(path, safe="/")
def table(rows: list[list]) -> str:
    if not rows: return ""
    def fmt(row): return "| " + " | ".join(str(x).replace("|", "/").replace("\n", " ") for x in row) + " |"
    return "\n".join([fmt(rows[0]),fmt(["---"]*len(rows[0])),*[fmt(r) for r in rows[1:]]]) + "\n"
def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(text,encoding="utf-8")
def writecsv(name: str, head: list, rows: list[list]) -> None:
    p=OUT/name; p.parent.mkdir(parents=True,exist_ok=True)
    with p.open("w",encoding="utf-8",newline="") as f:
        wr=csv.writer(f);wr.writerow(head);wr.writerows(rows)
def svg_bar_chart(path: Path, title: str, data: list[tuple], color: str="#187c7a", limit: int=14) -> None:
    data = list(data)[:limit]
    width, height = 1020, 114 + len(data) * 43
    max_value = max([int(v) for _,v in data],default=1)
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-label="{xml_escape(title,quote=True)}">',
             f'<rect width="{width}" height="{height}" rx="15" fill="#f5f8f9"/>',
             f'<text x="30" y="48" font-size="25" font-weight="bold" fill="#16363c" font-family="system-ui,Arial">{xml_escape(title)}</text>',
             '<text x="30" y="73" font-size="13" fill="#4c646d" font-family="system-ui,Arial">Antal källfiler eller förekomster; se tabeller för definitioner</text>']
    for i,(label,value) in enumerate(data):
        y=105+i*43
        n=int(value)
        b=max(1,round(n/max_value*465))
        parts += [f'<text x="30" y="{y+13}" font-size="15" fill="#25474f" font-family="system-ui,Arial">{xml_escape(str(label))}</text>',
                  f'<rect x="475" y="{y-3}" width="465" height="22" rx="6" fill="#e2ebec"/>',
                  f'<rect x="475" y="{y-3}" width="{b}" height="22" rx="6" fill="{color}"/>',
                  f'<text x="955" y="{y+13}" font-size="15" font-weight="bold" fill="#173a40" font-family="system-ui,Arial">{n}</text>']
    write(path,"\n".join(parts+["</svg>"])+"\n")

def mentions(text: str, phrase: str) -> int:
    return len(re.findall(r"(?<!\w)"+re.escape(phrase.casefold())+r"(?!\w)", text.casefold()))
def score(text: str, terms: list[str]) -> tuple[int,int,list[str]]:
    x=[(term,mentions(text,term)) for term in terms]
    hits=sum(n for _,n in x)
    present=[w for w,n in x if n]
    return hits,len(present),present
def tags(text: str, lex: dict, min_total:int=3, min_types:int=2) -> dict:
    result={}
    for name,terms in lex.items():
        hits,types,_=score(text,terms)
        if hits>=min_total and types>=min_types: result[name]=hits
    return result
def genus(path: Path) -> str:
    parts = path.relative_to(ROOT).parts
    return parts[1] if len(parts) > 1 else parts[0]
def corpus_paths():
    readable=[p for p in (ROOT/"readable").rglob("*.txt") if "_editorial" not in p.parts]
    direct=list((ROOT/"originals"/"other").glob("*.txt")) + list((ROOT/"originals"/"chat-poetry").glob("*.txt"))
    return sorted(readable+direct)
def primary(path: str) -> bool:
    low=path.casefold()
    return not any(k in low for k in ["/_versions/","/_unclassified/","backup of","säkerhetskopia"])
def figure_tags(text: str) -> dict:
    return {n:sum(mentions(text,t) for t in terms) for n,(_,terms) in FIGURES.items() if sum(mentions(text,t) for t in terms)>0}
def main():
    paths=corpus_paths()
    if not paths: raise SystemExit("No source text available")
    allwords=Counter(); allwords_no_refrain=Counter(); document_frequency=Counter()
    bigrams=Counter(); trigrams=Counter(); dialects=Counter()
    rows=[]; concordance=[]; semantic_context=defaultdict(Counter)
    by_family=defaultdict(Counter); by_family_docfreq=defaultdict(Counter)
    for p in paths:
        rel=p.relative_to(ROOT).as_posix()
        original=p.read_text(encoding="utf-8-sig",errors="replace")
        lines=[x.strip() for x in original.splitlines() if x.strip() and not META.fullmatch(x.strip())]
        text="\n".join(lines)
        words=tokens(text)
        distinct_lines=list(dict.fromkeys(x.casefold() for x in lines))
        no_refrain=tokens("\n".join(distinct_lines))
        counts=Counter(words)
        allwords.update(words)
        allwords_no_refrain.update(no_refrain)
        document_frequency.update(set(words))
        dialects.update(w for w in words if w in DIALECT)
        for line in lines:
            w=tokens(line)
            bigrams.update(zip(w,w[1:]))
            trigrams.update(zip(w,w[1:],w[2:]))
        for keyword in KEYWORDS:
            examples=[line[:220] for line in lines if mentions(line,keyword)]
            if examples:
                for ex in examples[:3]:
                    concordance.append([keyword,rel,ex])
                for line in examples:
                    w=tokens(line)
                    for i,v in enumerate(w):
                        if v==keyword:
                            semantic_context[keyword].update(w[max(0,i-3):i]+w[i+1:i+4])
        family=genus(p)
        if family=="other" or family=="chat-poetry": family=family
        themes=tags(text,THEMES)
        subjects=tags(text,SUBJECTS,2,2)
        figures=figure_tags(text)
        if themes.get("Politik, makt och ojämlikhet"): focus="Samhällskritik"
        elif themes.get("Kärlek och relationer"): focus="Kärlek och relation"
        elif themes.get("Musik, ljud och dans"): focus="Musik och scen"
        elif themes.get("Språk, kunskap och tänkande"): focus="Språk och reflektion"
        else: focus="Ej fastställt"
        title=p.name
        for suffix in [".rtf.txt",".docx.txt",".doc.txt",".txt"]:
            if title.endswith(suffix):
                title=title[:-len(suffix)];break
        rows.append({"path":rel,"title":title,"family":family,"genre":FAMILY.get(family,family),
          "primary":primary(rel),"tokens":len(words),"unique_words":len(counts),
          "lines":len(lines),"nonrepeated_lines":len(distinct_lines),
          "nonrepeated_tokens":len(no_refrain),"lexical_diversity":round(len(counts)/len(words),4) if words else 0,
          "themes":themes,"subjects":subjects,"figures":figures,"focus":focus,
          "word_top":counts.most_common(8),"content_top":[x for x in counts.most_common() if x[0] not in STOP and len(x[0])>2][:8],
          "hash":hashlib.sha256(text.encode()).hexdigest()})
        by_family[FAMILY.get(family,family)].update(words)
        by_family_docfreq[FAMILY.get(family,family)].update(set(words))
    # Scope: all source files vs primary files excluding named alternate/backup files
    primary_rows=[r for r in rows if r["primary"]]
    occurrences=sum(x["tokens"] for x in rows)
    nr_words=sum(x["nonrepeated_tokens"] for x in rows)
    genres=Counter(r["genre"] for r in rows)
    themes=Counter(k for r in rows for k in r["themes"])
    subjects=Counter(k for r in rows for k in r["subjects"])
    focuses=Counter(r["focus"] for r in rows)
    figures=Counter(k for r in rows for k in r["figures"])
    exact=defaultdict(list)
    for r in rows: exact[r["hash"]].append(r["path"])
    duplicates=[v for v in exact.values() if len(v)>1]
    corpus={
      "updated_at":datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
      "scope":"Source files, not verified unique works. Editorial transcriptions excluded.",
      "documents":len(rows),"primary_documents":len(primary_rows),
      "tokens_including_refrains":occurrences,"tokens_without_repeated_lines":nr_words,
      "distinct_wordforms":len(allwords),"exact_duplicate_groups":duplicates,
      "source_families":dict(genres.most_common()),"themes_document_frequency":dict(themes.most_common()),
      "subjects_document_frequency":dict(subjects.most_common()),"focus_document_frequency":dict(focuses.most_common()),
      "figures_document_frequency":dict(figures.most_common()),
      "most_frequent_words":allwords.most_common(40),
      "most_frequent_content_words":[(w,n) for w,n in allwords.most_common() if w not in STOP and len(w)>2][:40],
      "most_frequent_nonrepeated_words":allwords_no_refrain.most_common(40),
      "dialect_markers":dialects.most_common(30),
      "bigrams":[(" ".join(a),n) for a,n in bigrams.most_common(60)],
      "trigrams":[(" ".join(a),n) for a,n in trigrams.most_common(50)]}
    OUT.mkdir(exist_ok=True)
    write(OUT/"summary.json",json.dumps(corpus,ensure_ascii=False,indent=2)+"\n")
    writecsv("documents.csv",["path","title","form_source","primary","tokens","distinct_wordforms","nonrepeated_line_tokens","lexical_diversity","focus","themes","subjects","figures"],[
      [r["path"],r["title"],r["genre"],r["primary"],r["tokens"],r["unique_words"],r["nonrepeated_tokens"],r["lexical_diversity"],r["focus"],"; ".join(r["themes"]),"; ".join(r["subjects"]),"; ".join(r["figures"])] for r in rows])
    writecsv("words.csv",["wordform","count","documents","per_1000_tokens","nonrepeated_line_count","is_functional_word","is_dialect_marker"],[
      [w,n,document_frequency[w],round(1000*n/max(1,occurrences),3),allwords_no_refrain[w],w in STOP,w in DIALECT] for w,n in allwords.most_common()])
    writecsv("bigrams.csv",["bigram","count"],[[" ".join(k),v] for k,v in bigrams.most_common()])
    writecsv("trigrams.csv",["trigram","count"],[[" ".join(k),v] for k,v in trigrams.most_common()])
    writecsv("concordance.csv",["word","source","line"],concordance)
    # One file and one genre are distinct grains; do not sum overlapping theme groups.
    writecsv("words_by_genre.csv",["source_genre","wordform","occurrences","document_frequency","per_1000_genre_tokens"],[
      [fam,w,n,by_family_docfreq[fam][w],round(1000*n/max(1,sum(counts.values())),3)]
      for fam,counts in sorted(by_family.items()) for w,n in counts.most_common()])
    writecsv("top_words_by_work.csv",["source","wordform","count","is_content_word"],[
      [r["path"],word,n,word not in STOP] for r in rows for word,n in r["word_top"]])
    writecsv("theme_by_genre.csv",["genre","theme","tagged_files","all_genre_files","share_percent"],[
      [gen,theme,sum(theme in r["themes"] for r in rows if r["genre"]==gen),sum(r["genre"]==gen for r in rows),
        round(100*sum(theme in r["themes"] for r in rows if r["genre"]==gen)/max(1,sum(r["genre"]==gen for r in rows)),2)]
      for gen in sorted(set(r["genre"] for r in rows)) for theme in THEMES])
    writecsv("topic_by_genre.csv",["genre","topic","tagged_files","all_genre_files","share_percent"],[
      [gen,sub,sum(sub in r["subjects"] for r in rows if r["genre"]==gen),sum(r["genre"]==gen for r in rows),
        round(100*sum(sub in r["subjects"] for r in rows if r["genre"]==gen)/max(1,sum(r["genre"]==gen for r in rows)),2)]
      for gen in sorted(set(r["genre"] for r in rows)) for sub in SUBJECTS])
    theme_pairs=Counter()
    for record in rows:
      ordered=sorted(record["themes"])
      for i in range(len(ordered)):
        for j in range(i+1,len(ordered)):
          theme_pairs[(ordered[i],ordered[j])]+=1
    writecsv("theme_pairs.csv",["first_theme","second_theme","shared_source_files"],[
      [a,b,n] for (a,b),n in theme_pairs.most_common()])

    writecsv("document_tags.csv",["source","genre_or_form","dimension","tag","matched_token_occurrences"],[
      [r["path"],r["genre"],d,k,n] for r in rows for d,label in [("theme","themes"),("subject","subjects"),("figure","figures")] for k,n in r[label].items()])
    writecsv("semantic_neighbors.csv",["key_word","neighbor","count"],[
      [k,w,n] for k,c in semantic_context.items() for w,n in c.most_common() if w not in STOP and w!=k][:2500])
    writecsv("figures.csv",["figure","type","documents","mentions","sources"],[
      [name,FIGURES[name][0],sum(name in r["figures"] for r in rows),sum(r["figures"].get(name,0) for r in rows),
       "; ".join(r["path"] for r in rows if name in r["figures"])] for name in FIGURES])
    def ref(pth,title):
        return "["+title+"]("+link(pth)+")"
    family_rows=[[name,str(n),f"{round(100*n/len(rows),1)} %"] for name,n in genres.most_common()]
    theme_rows=[[name,str(n),f"{round(100*n/len(rows),1)} %",f"{'▰'*max(1,round(n/max(1,len(rows))*15))}"] for name,n in themes.most_common()]
    topic_rows=[[name,str(n),f"{round(100*n/len(rows),1)} %"] for name,n in subjects.most_common()]
    figure_rows=[[name,FIGURES[name][0],str(n),str(sum(r["figures"].get(name,0) for r in rows))] for name,n in figures.most_common()]
    word_rows=[[w,str(n),str(document_frequency[w]),str(round(1000*n/max(1,occurrences),2))] for w,n in allwords.most_common(25)]
    content_rows=[[w,str(n),str(document_frequency[w]),str(round(1000*n/max(1,occurrences),2))] for w,n in corpus["most_frequent_content_words"][:30]]
    dialect_rows=[[w,str(n)] for w,n in dialects.most_common(20)]
    bigram_rows=[[ " ".join(w), str(n)] for w,n in bigrams.most_common(22)]
    figure_top=[[name, str(n), "; ".join(ref(r["path"],r["title"]) for r in rows if name in r["figures"])[:950]] for name,n in figures.most_common(16)]
    # Source-backed static visuals; never synthetic estimates.
    svg_bar_chart(OUT/"charts"/"source_families.svg","Arkivets genrer och textfamiljer",genres.most_common(),color="#187c7a")
    svg_bar_chart(OUT/"charts"/"themes.svg","Tematiska markörer per källfil",themes.most_common(),color="#a96b33")
    svg_bar_chart(OUT/"charts"/"content_words.svg","Mest använda innehållsord",
      corpus["most_frequent_content_words"][:16],color="#4d6287")
    WIKI.mkdir(exist_ok=True)
    nav=("[Hem](Home.md) · [Verkindex](Verkindex.md) · [Genre och form](Genre-och-form.md) · "
         "[Teman](Teman-och-motiv.md) · [Ämnen och fokus](Amnen-och-fokus.md) · "
         "[Figurer](Figurer.md) · [Semantik](Semantik.md) · [Redaktionell analys](Redaktionell-analys.md) · [Metod](Korpus-och-metod.md)")
    write(WIKI/"_Sidebar.md","\n".join(["# Texts-n-Lyrics",*[f"- [{name}]({page}.md)" for name,page in [
      ("Hem","Home"),("Verkindex","Verkindex"),("Genre och form","Genre-och-form"),("Teman och motiv","Teman-och-motiv"),
      ("Ämnen och fokus","Amnen-och-fokus"),("Figurer","Figurer"),("Semantik","Semantik"),("Redaktionell analys","Redaktionell-analys"),("Korpus och metod","Korpus-och-metod")]]])+"\n")
    write(WIKI/"Home.md", "# Texts-n-Lyrics – verk och språklig atlas\n\n"+nav+"\n\n"+
     "## Översikt\n\n"+table([["Mått","Verdi"],["Analysbara källfiler",len(rows)],["Primära källfiler (exklusive uttryckligt märkta varianter)",len(primary_rows)],
     ["Ordförekomster (inklusive upprepade refränger)",f"{occurrences:,}"],["Ordförekomster efter upprepade rader tagits bort",f"{nr_words:,}"],
     ["Distinkta ordformer",f"{len(allwords):,}"],["Exakta dubbla textversioner",len(duplicates)]])+
     "\n## Genre och ursprunglig form\n\n![Arkivfördelning](https://raw.githubusercontent.com/Hybrismannen/Texts-n-Lyrics/main/analytics/charts/source_families.svg)\n\n"+table([["Form/källfamilj","Filer","Andel"],*family_rows])+
     "\n## Tematiska signaler\n\n![Temamarkörer](https://raw.githubusercontent.com/Hybrismannen/Texts-n-Lyrics/main/analytics/charts/themes.svg)\n\n"+table([["Tematisk dimension","Filer","Andel","Fördelning"],*theme_rows])+
     "\n## Vidare analys\n\n- [Läs direkt ur verkindex](Verkindex.md)\n- [Ämne respektive retoriskt fokus](Amnen-och-fokus.md)\n- [Figurer, karaktärer och artistpersonae](Figurer.md)\n- [Ordformer, innehållsord, dialekt, n-gram och konkordans](Semantik.md)\n- [Korpus, osäkerhet, urval och metod](Korpus-och-metod.md)\n\n"+
     "> Kategorierna ovan är **lexikala indikatorer**, inte fastställda litteraturvetenskapliga tolkningar. Ett verk kan matcha flera teman. Dokument/fil är inte detsamma som unikt litterärt verk. \n")
    write(WIKI/"Genre-och-form.md","# Genre, form och källfamiljer\n\n"+nav+"\n\n"+
      "Genre här är en **provisorisk formklassning från ursprunglig arkivplacering**. Mappen 'recording' är inte en musikgenre, och många dokument är genreblandade.\n\n"+
      table([["Form/källfamilj","Källfiler","Andel"],*family_rows])+
      "\n## Tema per källfamilj\n\n"+
      table([["Källfamilj","Tema","Filer","Andel inom gruppen"],*[
        [gen,theme,sum(theme in r["themes"] for r in rows if r["genre"]==gen),
        str(round(100*sum(theme in r["themes"] for r in rows if r["genre"]==gen)/max(1,n),1))+" %"]
        for gen,n in genres.most_common() for theme in THEMES
        if sum(theme in r["themes"] for r in rows if r["genre"]==gen)>=2]])+
      "\n## Vanligaste innehållsord per källfamilj\n\n"+
      "\n".join("### "+gen+"\n\n"+", ".join(w+" ("+str(n)+")" for w,n in by_family[gen].most_common() if w not in STOP and len(w)>2)[:1300]+"\n"
        for gen,n in genres.most_common())+
      "\n## Verk i varje form\n\n"+
      "\n".join(f"### {name} ({n})\n\n"+", ".join(ref(r["path"],r["title"]) for r in rows if r["genre"]==name)+"\n" for name,n in genres.most_common()))
    write(WIKI/"Teman-och-motiv.md","# Teman och motiv\n\n"+nav+"\n\n"+
      "Ett tema markeras när minst **tre ordträffar och två olika indikatorord** finns i samma källfil. Det är en transparent indexeringsregel, inte bevis på verkets budskap.\n\n"+
      table([["Tema","Antal källfiler","Andel"],*[r[:3] for r in theme_rows]])+
      "\n## Samförekomst mellan teman\n\n"+
      table([["Tema 1","Tema 2","Gemensamma filer"],*[
        [a,b,n] for (a,b),n in theme_pairs.most_common(18)]])+
      "\nMer data: [tema per källfamilj]("+REPO+"/blob/main/analytics/theme_by_genre.csv) och [temapar]("+
      REPO+"/blob/main/analytics/theme_pairs.csv).\n\n"+
      "\n".join(f"\n### {name} — {n} filer\n\n"+", ".join(ref(r["path"],r["title"]) for r in rows if name in r["themes"])+"\n" for name,n in themes.most_common()))
    write(WIKI/"Amnen-och-fokus.md","# Ämnen och textens fokus\n\n"+nav+"\n\n"+
      "Ämne avser konkret behandlad sakfråga. Tema avser återkommande motiv. Fokus är en **provisorisk enkelklassning** genom prioriterade lexikala regler; det är inte säkerställd författaravsikt.\n\n## Ämnen\n\n"+
      table([["Ämne","Källfiler","Andel"],*topic_rows])+
      "\n## Fokus\n\n"+table([["Huvudsaklig etikett","Filer"],*[[a,b] for a,b in focuses.most_common()]])+
      "\n## Källor efter ämne\n\n"+
      "\n".join(f"### {name}\n\n"+", ".join(ref(r["path"],r["title"]) for r in rows if name in r["subjects"])+"\n" for name,n in subjects.most_common()))
    write(WIKI/"Figurer.md","# Figurer, röster och referenser\n\n"+nav+"\n\n"+
      "En **nämning** är en exakt ord-/frasträff. En **karaktär** är inte samma sak som en artistpersona eller referens till en verklig person. Tabellen håller dessa isär. Enskilda namn kan saknas i ordboken.\n\n"+
      table([["Namn","Typ","Källfiler","Nämningar"],*figure_rows])+
      "\n## Återfinn verken\n\n"+table([["Figur/referens","Filer","Källtexter"],*figure_top]))
    write(WIKI/"Semantik.md","# Semantik, ordval och språkliga mönster\n\n"+nav+"\n\n"+
      "## Mest frekventa ordformer\n\n"+
      table([["Ordform","Förekomster","Källfiler","Per 1 000 ord"],*word_rows])+
      "\n## Innehållsord (funktionsord bortfiltrerade)\n\n"+table([["Ordform","Förekomster","Källfiler","Per 1 000 ord"],*content_rows])+
      "\n## Patois- och dialektmarkörer\n\n"+table([["Markör","Förekomster"],*dialect_rows])+
      "\n## Tvåordskombinationer (bigrams)\n\n"+table([["Fras","Förekomster"],*bigram_rows])+
      "\n## Begreppsfamiljer – uttrycklig lexikonaggregering\n\n"+
      table([["Begreppsfamilj","Träffar","Ingående ordformer"],*[[name,sum(allwords[w] for w in items),", ".join(items)] for name,items in GROUPS.items()]])+
      "\n## Ord i olika kontexter och genrer\n\n"+
      table([["Nyckelord","Form/källfamilj","Antal","Per 1 000 ord i familjen"],*[
        [word,gen,by_family[gen].get(word,0),round(1000*by_family[gen].get(word,0)/max(1,sum(counts.values())),2)]
        for word in ["love","life","people","music","power","time","world","system","sound","riddim"]
        for gen,counts in by_family.items() if by_family[gen].get(word,0)>=2]])+
      "\n## Närliggande ord (fönster på tre positioner)\n\n"+
      table([["Nyckelord","Ordgrannar och antal"],*[
        [w,", ".join(a+" ("+str(n)+")" for a,n in semantic_context[w].most_common() if a!=w and a not in STOP)[:420]]
        for w in ["love","life","people","music","power","time","world","sound","riddim"]]])+
      "\n## Exempel ur källtexterna\n\n"+
      "\n".join("### "+kw+"\n\n"+
        "\n".join("- "+ref(pth,excerpt[:170]) for w,pth,excerpt in concordance if w==kw)[:800]+"\n"
        for kw in ["love","life","people","music","power","time","world"]) +
      "\n## Underliggande rådata\n\n"+
      "\n".join(["- [Alla ordformer och dokumentfrekvens]("+REPO+"/blob/main/analytics/words.csv)",
      "- [Bigrams]("+REPO+"/blob/main/analytics/bigrams.csv)",
      "- [Trigrams]("+REPO+"/blob/main/analytics/trigrams.csv)",
      "- [Konkordans – exempelrader med källor]("+REPO+"/blob/main/analytics/concordance.csv)",
      "- [Ordgrannar inom tre token]("+REPO+"/blob/main/analytics/semantic_neighbors.csv)",
      "- [Dokument och tematiska etiketter]("+REPO+"/blob/main/analytics/document_tags.csv)",
      "- [Ordfrekvens per källfamilj]("+REPO+"/blob/main/analytics/words_by_genre.csv)",
      "- [Ordfrekvens på verknivå]("+REPO+"/blob/main/analytics/top_words_by_work.csv)",
      "- [Ämnen per genre]("+REPO+"/blob/main/analytics/topic_by_genre.csv)"])+
      "\n\n**Viktigt:** 'Semantisk analys' betyder här spårbar, regelbaserad betydelse- och kontextindexering, inte en språkmodells djupsemantiska klassning. Ord utan uppenbar synonymi har inte automatiskt slagits ihop. Fullständiga lemmatiseringar för svenska, engelska och jamaicansk patois skulle kräva separat språkvetenskaplig validering.\n")
    write(WIKI/"Korpus-och-metod.md","# Korpus och metod\n\n"+nav+"\n\n"+
      "## Analysenhet och täckning\n\n- Enheten är **en textfil**, inte ett unikt litterärt verk.\n"+
      f"- Omfattning: **{len(rows)} analysbara filer**. Editoriala transkriptioner ligger utanför korpus.\n"+
      f"- Explicit versions-/backupmärkta filer: **{len(rows)-len(primary_rows)}** (gäller inte oidentifierade innehållsvarianter).\n"+
      "- Läsbara versioner analyseras; originalformaten förblir oförändrade i originals/.\n"+
      "- Dokument i samlingsfiler kan motsvara flera verk. Inga upphov har gissats fram.\n"+
      "- Ursprungsdatum saknas för många verk. Git-importdatum får inte användas som skrivdatum.\n\n"+
      "## Mätdefinitioner\n\n- **Ordförekomst:** token separerad med Unicode-bokstäver och tillåtna bindestreck/apostrofer, skiftlägesnormaliserad.\n"+
      "- **Distinkt ordform:** exakt normaliserad token, inte lemma eller synonym.\n"+
      "- **Dokumentfrekvens:** antal källfiler där ordformen finns minst en gång.\n"+
      "- **Refrängjusterat tokenmått:** samma identiska textrad räknas bara en gång *inom ett och samma dokument*.\n"+
      "- **Innehållsord:** enkla handbyggda funktionsordslistor för svenska, engelska och patois; urvalet är inte en fullständig lingvistisk taggning.\n"+
      "- **Tema:** minst tre lexikala träffar och två olika signalord; flera teman kan matcha samma text.\n"+
      "- **Ämne:** minst två lexikala träffar och två olika signalord.\n"+
      "- **Fokus:** prioriterad, provisorisk enkelklassning. 'Ej fastställt' är tillåtet.\n"+
      "- **Figur:** exakt matchning mot ett redovisat litet namnlexikon; typer skiljs åt.\n"+
      "- **Konkordans:** upp till tre autentiska textrader per sökord och källfil, med länk till källa.\n"+
      "- **Ordgrannar:** ord inom högst tre positioner i samma matchade rad; frekvens visar närhet, inte nödvändigtvis verklig semantisk relation.\n\n"+
      "## Kvalitetsbegränsningar\n\nRefränger driver upp frekvenser. Källornas stavningsvariation och flerspråkighet gör att närliggande former ofta räknas separat. Arkivmappar kan innehålla genreblandade texter. Namngivna historiska och fiktiva figurer är inte automatiskt huvudpersoner. Automatisk kategorisering kan ge både falska positiva och negativa träffar. Kategorier behöver senare kontrolleras av författaren.\n\n"+
      "## Reproducerbarhet\n\n- [Fullt analysprogram]("+REPO+"/blob/main/tools/analyze_archive.py)\n"+
      "- [Maskinläsbar sammanfattning]("+REPO+"/blob/main/analytics/summary.json)\n"+
      "- [Fullständig dokumentmatris]("+REPO+"/blob/main/analytics/documents.csv)\n"+
      "- [Källmanifest med Git-hashar]("+REPO+"/blob/main/catalog/SOURCE_MANIFEST.md)\n\n"+
      "Det går att köra analysen lokalt med kommandot 'python3 tools/analyze_archive.py'.\n")
    write(WIKI/"Verkindex.md","# Verkindex\n\n"+nav+"\n\n"+
      f"**{len(rows)} textfiler** med spårbara länkar till själva texten. Vissa rader avser ett utkast eller en alternativ version, inte ett nytt verk.\n\n"+
      table([["Titel","Form/källfamilj","Ord","Fokus","Primär källa"],*[
        [ref(r["path"],r["title"]),r["genre"],r["tokens"],r["focus"],"Ja" if r["primary"] else "Version/backup"] for r in sorted(rows,key=lambda x:(x["genre"],x["title"].casefold()))]]))
    # Non-wiki GitHub README (generated)
    readme=("# Texts-n-Lyrics · Linus Fast\n\n"
      "Ett källbevarande litterärt arkiv och en **öppen språklig atlas**: poesi, prosalyrik, reggae-/dancehalltexter, rap, grime, dubplates och musikaliska berättelser.\n\n"
      "## Arkivet i siffror\n\n"+table([["Källfiler med analyserbar text","Ordförekomster","Distinkta ordformer","Upprepade rader borttagna (ord)"],
      [str(len(rows)),f"{occurrences:,}",f"{len(allwords):,}",f"{nr_words:,}"]])+
      "**Tolkning:** siffrorna avser källfiler, inte verifierat antal unika verk. Refräng- och säkerhetskopieeffekter redovisas separat.\n\n"
      "## Utforska samlingen\n\n"
      "| Ingång | Beskrivning |\n| --- | --- |\n"
      "| [Wiki/atlas – startsida](wiki/Home.md) | Förklaringar, navigering och statistisk översikt |\n"
      "| [Verkindex](wiki/Verkindex.md) | Bläddra per titel, form, omfång och fokus |\n"
      "| [Genre och form](wiki/Genre-och-form.md) | Källfamiljer och provisoriska genreklasser |\n"
      "| [Teman och motiv](wiki/Teman-och-motiv.md) | Kärlek, samhälle, musik, natur, existens m.m. |\n"
      "| [Ämnen och fokus](wiki/Amnen-och-fokus.md) | Ämnesklassning separat från textens huvudfokus |\n"
      "| [Figurer och referenser](wiki/Figurer.md) | Artistpersonae, fiktiva figurer och kulturreferenser |\n"
      "| [Semantisk ordatlas](wiki/Semantik.md) | Mest använda ord, innehållsord, patois, fraser och kontext |\n"
      "| [Redaktionell närläsning](wiki/Redaktionell-analys.md) | Exempel på perspektiv, återkommande uttryck och genreblandning |\n"
      "| [Metod och datakvalitet](wiki/Korpus-och-metod.md) | Källor, definitionsregler, begränsningar |\n"
      "| [Rådata](analytics/) | CSV-filer, JSON och konkordans |\n"
      "| [Original](originals/) / [läsbara utgåvor](readable/) | Oförändrade original och separat textextraktion |\n\n"
      "## Genrer och former – efter källarkivets familjer\n\n![Genrer och formgrupper](analytics/charts/source_families.svg)\n\n"+table([["Form/källfamilj","Källfiler","Andel"],*family_rows])+
      "## Återkommande teman – lexikala indikatorer\n\n![Teman per källfil](analytics/charts/themes.svg)\n\n"+table([["Tema","Källfiler","Andel","Visuell andel"],*theme_rows])+
      "## Retoriskt fokus – provisorisk indexering\n\n"+
      table([["Fokus","Källfiler"],*[[name,n] for name,n in focuses.most_common()]])+
      "## Sakområden – ämnesklassning\n\n"+
      table([["Ämne","Källfiler"],*[[name,n] for name,n in subjects.most_common()]])+
      "## Vanliga innehållsord\n\n![Innehållsord](analytics/charts/content_words.svg)\n\n"+table([["Ordform","Antal","Källfiler"],*[[w,n,document_frequency[w]] for w,n in corpus["most_frequent_content_words"][:15]]])+
      "\n## Röst och återkommande figurregister\n\n"+table([["Namn","Typ","Filer"],*[[n,FIGURES[n][0],v] for n,v in figures.most_common(10)]])+
      "\n## Redaktionell och vetenskaplig integritet\n\n"
      "- Detta är en **korpusstatistisk indexering**, inte en bevisad psykologisk profil eller litterär kvalitetsbedömning.\n"
      "- **Genre, tema, ämne och fokus är olika dimensioner**; flera teman kan finnas i en text.\n"
      "- Råfilerna i originals/ förändras aldrig av statistiken; derivat lagras under readable/, analytics/ och wiki/.\n"
      "- Native GitHub Wiki är ett separat Git-repository. Denna wiki har versionshanterad källa i mappen wiki/ och kan speglas till GitHubs Wiki-gränssnitt.\n"
      "- Namn på externa artister, fiktiva figurer och artistpersonae redovisas separat; en namnträff är inte ett belägg för narrativ huvudroll.\n\n"
      "[Arkivets källstatus](catalog/INDEX.md) · [62 tidigare identifierade chattverk](catalog/chat-register-2024-2026.md) · [Källmanifest](catalog/SOURCE_MANIFEST.md)\n\n"
      f"*Statistik genererad {corpus['updated_at'][:10]} med tools/analyze_archive.py.*\n")
    write(ROOT/"README.md",readme)
    print(json.dumps({"files":len(rows),"primary":len(primary_rows),"tokens":occurrences,"types":len(allwords),"themes":themes.most_common(),"genres":genres.most_common(),"top_words":allwords.most_common(10)},ensure_ascii=False))
if __name__=="__main__": main()
