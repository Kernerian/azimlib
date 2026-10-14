"""Independent implementation of UAX #9, rules P2 through L2.

Algorithmic specification: https://www.unicode.org/reports/tr9/tr9-51.html
Unicode character properties are obtained from ICU; no ICU bidi code is used.
"""
from functools import lru_cache
from azimlib._unicode_icu import _api

ISOLATES = frozenset(('LRI','RLI','FSI'))
REMOVED = frozenset(('LRE','RLE','LRO','RLO','PDF','BN'))
NEUTRAL = frozenset(('B','S','WS','ON','LRI','RLI','FSI','PDI'))
NAMES = ('L','R','EN','ES','ET','AN','CS','B','S','WS','ON','LRE','LRO','AL','RLE','RLO','PDF','NSM','BN','FSI','LRI','RLI','PDI')


@lru_cache(maxsize=8192)
def properties(char):
    api=_api();direction,integer,pair=api['char_direction'],api['integer_property'],api['paired_bracket'];cp=ord(char)
    bracket=integer(cp,0x1015) # UCHAR_BIDI_PAIRED_BRACKET_TYPE
    canonical=lambda c: {0x2329:0x3008,0x232a:0x3009}.get(c,c)
    return NAMES[direction(cp)],bracket,canonical(pair(cp)),canonical(cp)


def first_strong(types,start,end,pairs):
    i=start
    while i<end:
        t=types[i]
        if t=='L':return 0
        if t in ('R','AL'):return 1
        if t in ISOLATES:i=pairs.get(i,end)
        i+=1
    return 0


def resolved_levels(text,direction='auto'):
    """Code-point embedding levels, including retained X9 controls (section 5.2)."""
    props=[properties(c) for c in text];original=[p[0] for p in props];n=len(text)
    pairs={};opens=[]
    for i,t in enumerate(original):
        if t in ISOLATES:opens.append(i)
        elif t=='PDI' and opens:
            a=opens.pop();pairs[a]=i;pairs[i]=a
    base=first_strong(original,0,n,pairs) if direction=='auto' else {'ltr':0,'rtl':1}[direction]
    types=original.copy();levels=[base]*n
    stack=[(base,None,False)];overflow_isolate=overflow_embedding=valid_isolate=0
    for i,t in enumerate(original):
        level,override,isolate=stack[-1];levels[i]=level
        if t in ('RLE','LRE','RLO','LRO'):
            new=level+1 if (level%2==0)==(t in ('RLE','RLO')) else level+2
            if not overflow_isolate and not overflow_embedding and new<=125:
                stack.append((new,{'RLO':'R','LRO':'L'}.get(t),False))
            elif not overflow_isolate:overflow_embedding+=1
        elif t in ISOLATES:
            if override:types[i]=override
            rtl=t=='RLI' or t=='FSI' and first_strong(original,i+1,pairs.get(i,n),pairs)==1
            new=level+1 if (level%2==0)==rtl else level+2
            if not overflow_isolate and not overflow_embedding and new<=125:
                valid_isolate+=1;stack.append((new,None,True))
            else:overflow_isolate+=1
        elif t=='PDI':
            if overflow_isolate:overflow_isolate-=1
            elif valid_isolate:
                overflow_embedding=0
                while not stack[-1][2]:stack.pop()
                stack.pop();valid_isolate-=1
            levels[i]=stack[-1][0]
            if stack[-1][1]:types[i]=stack[-1][1]
        elif t=='PDF':
            if not overflow_isolate:
                if overflow_embedding:overflow_embedding-=1
                elif len(stack)>1 and not isolate:stack.pop()
        elif t=='B':levels[i]=base
        elif t!='BN' and override:types[i]=override
    active=[i for i,t in enumerate(original) if t not in REMOVED]
    runs=[];owner={}
    for i in active:
        if not runs or levels[i]!=levels[runs[-1][-1]]:runs.append([])
        runs[-1].append(i);owner[i]=len(runs)-1
    # Link the level runs into disjoint isolating run sequences.
    links={};incoming=set()
    for r,run in enumerate(runs):
        last=run[-1]
        if original[last] in ISOLATES and last in pairs:
            target=owner[pairs[last]]
            if target!=r:links[r]=target;incoming.add(target)
    active_position={i:p for p,i in enumerate(active)}
    sequence_data=[]
    for r,run in enumerate(runs):
        if r in incoming:continue
        seq=list(run)
        while r in links:r=links[r];seq.extend(runs[r])
        a,b=active_position[seq[0]],active_position[seq[-1]]
        before=levels[active[a-1]] if a else base
        after=base if original[seq[-1]] in ISOLATES or b+1==len(active) else levels[active[b+1]]
        sos='R' if max(levels[seq[0]],before)%2 else 'L'
        eos='R' if max(levels[seq[-1]],after)%2 else 'L'
        sequence_data.append((seq,sos,eos))
    for seq,sos,eos in sequence_data:
        ts=[types[i] for i in seq];length=len(ts);embedding=levels[seq[0]]
        # W1: NSM inherits the preceding type, except isolate boundaries.
        previous=sos
        for p,t in enumerate(ts):
            if t=='NSM':ts[p]='ON' if previous in ISOLATES or previous=='PDI' else previous
            previous=ts[p]
        # W2/W3: Arabic strong context changes European numbers.
        previous=sos
        for p,t in enumerate(ts):
            if t=='EN' and previous=='AL':ts[p]='AN'
            if t in ('L','R','AL'):previous=t
        ts=['R' if t=='AL' else t for t in ts]
        # W4/W5/W6: numeric separators and terminators.
        for p in range(1,length-1):
            if ts[p]=='ES' and ts[p-1]==ts[p+1]=='EN':ts[p]='EN'
            elif ts[p]=='CS' and ts[p-1]==ts[p+1] and ts[p-1] in ('EN','AN'):ts[p]=ts[p-1]
        p=0
        while p<length:
            if ts[p]!='ET':p+=1;continue
            end=p+1
            while end<length and ts[end]=='ET':end+=1
            if (p>0 and ts[p-1]=='EN') or (end<length and ts[end]=='EN'):
                ts[p:end]=['EN']*(end-p)
            p=end
        ts=['ON' if t in ('ES','ET','CS') else t for t in ts]
        previous=sos
        for p,t in enumerate(ts):
            if t=='EN' and previous=='L':ts[p]='L'
            if t in ('L','R'):previous=t
        # BD16/N0: pair only neutral brackets; exceeding 63 opens stops pairing.
        brackets=[];pending=[]
        for p,i in enumerate(seq):
            if ts[p]!='ON':continue
            _,kind,match,canonical=props[i]
            if kind==1:
                if len(pending)==63:break
                pending.append((p,match))
            elif kind==2:
                found=next((q for q in range(len(pending)-1,-1,-1) if pending[q][1]==canonical),None)
                if found is not None:
                    brackets.append((pending[found][0],p));del pending[found:]
        e='R' if embedding%2 else 'L';opposite='L' if e=='R' else 'R'
        strong=lambda t:'R' if t in ('EN','AN') else t
        for a,b in sorted(brackets):
            enclosed={strong(t) for t in ts[a+1:b]}
            value=None
            if e in enclosed:value=e
            elif opposite in enclosed:
                before=next((strong(ts[q]) for q in range(a-1,-1,-1) if strong(ts[q]) in ('L','R')),sos)
                value=opposite if before==opposite else e
            if value:
                ts[a]=ts[b]=value
                for bracket in (a,b):
                    q=bracket+1
                    while q<length and original[seq[q]]=='NSM':ts[q]=value;q+=1
        # N1/N2, then I1/I2.
        p=0
        while p<length:
            if ts[p] not in NEUTRAL:p+=1;continue
            end=p+1
            while end<length and ts[end] in NEUTRAL:end+=1
            before=strong(ts[p-1]) if p else sos;after=strong(ts[end]) if end<length else eos
            ts[p:end]=[before if before==after else e]*(end-p);p=end
        for p,i in enumerate(seq):
            t=ts[p]
            levels[i]+=((1 if t=='R' else 2 if t in ('EN','AN') else 0) if embedding%2==0 else (0 if t=='R' else 1))
    # L1. Ignore X9 characters when looking behind a separator/end of line.
    reset=frozenset(('WS','LRI','RLI','FSI','PDI'))
    ends=[p for p,i in enumerate(active) if original[i] in ('B','S')]+[len(active)]
    for p in ends:
        if p<len(active):levels[active[p]]=base
        p-=1
        while p>=0 and original[active[p]] in reset:levels[active[p]]=base;p-=1
    previous=base
    for i,t in enumerate(original):
        if t in REMOVED:levels[i]=previous
        else:previous=levels[i]
    return tuple(levels),base


def visual_runs(text,direction='auto'):
    if direction not in ('auto','ltr','rtl'):raise ValueError('Invalid paragraph direction')
    if len(text)>4096:raise ValueError('Bidi paragraph exceeds 4096 code points')
    if not text:return ()
    levels,_=resolved_levels(text,direction);runs=[]
    for i,level in enumerate(levels):
        if not runs or runs[-1][2]!=level:runs.append((i,i+1,level))
        else:runs[-1]=(runs[-1][0],i+1,level)
    odd=[level for level in levels if level%2]
    if odd:
        for threshold in range(max(levels),min(odd)-1,-1):
            p=0
            while p<len(runs):
                if runs[p][2]<threshold:p+=1;continue
                end=p+1
                while end<len(runs) and runs[end][2]>=threshold:end+=1
                runs[p:end]=reversed(runs[p:end]);p=end
    return tuple((a,b,'rtl' if level%2 else 'ltr') for a,b,level in runs)
