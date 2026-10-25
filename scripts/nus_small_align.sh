#!/bin/bash
# NUSAutoLyrixAlign with a per-song lexicon. Copied into the karaokeer container and run from /NUSAutoLyrixAlign:
#     xl_small_align.sh <audio.wav> <lyrics.txt> <aligned.txt>      (same arguments and output as RunAlignment.sh)
#
# The stock lang dir's L.fst is 4.2 GB (207k words x up to ~50 sung-length pronunciation variants, 12.9M lexicon
# entries) and compile-train-graphs loads all of it for every run: ~14 GB of RAM however short the lyrics, which
# twice ran the machine out of memory mid-rollout. This builds a lang dir holding only this song's words (all their
# variants, plus !SIL and <unk>) - same phones, topo and model - so alignment needs a fraction of the memory.
set -e
cd /NUSAutoLyrixAlign
BIG=data/lang_asru_PHON_final_mirex
T=$(tr -dc A-Za-z0-9 </dev/urandom | head -c 13)
L=data/lang_xl_$T

python PreProcessing.py "$1" "$2" "$T" > /dev/null    # before path.sh: it puts a python without pydub first
sed -i 's/\r$//' "data/$T/text"
. ./path.sh

mkdir -p "$L"
cp -r "$BIG/phones" "$BIG/phones.txt" "$BIG/topo" "$L/"
cut -d' ' -f2- "data/$T/text" | tr ' ' '\n' | grep -v '^$' | sort -u > "$L/want"
printf '!SIL\n<unk>\nBREATH*\n' >> "$L/want"
# align_lexicon.txt lines are "WORD WORD phone..."; the lexicon wants "WORD phone..."
awk 'NR == FNR { w[$1] = 1; next } ($1 in w) { $2 = ""; sub(/  /, " "); print }' "$L/want" "$BIG/phones/align_lexicon.txt" \
    > "$L/lexicon.txt"
{ echo "<eps> 0"; cut -d' ' -f1 "$L/lexicon.txt" | sort -u | awk '{ print $1, NR }'; } > "$L/words.txt"
echo "#0 $(wc -l < "$L/words.txt")" >> "$L/words.txt"
echo "<unk>" > "$L/oov.txt"
awk '$1 == "<unk>" { print $2 }' "$L/words.txt" > "$L/oov.int"
utils/make_lexicon_fst.pl "$L/lexicon.txt" 0.5 "$(cat "$BIG/phones/optional_silence.txt")" \
    | fstcompile --isymbols="$L/phones.txt" --osymbols="$L/words.txt" --keep_isymbols=false --keep_osymbols=false \
    | fstarcsort --sort_type=olabel > "$L/L.fst"

sed "s#data/lang_asru_PHON_final_mirex#$L#g" run_align.sh > "run_align_$T.sh"
bash "run_align_$T.sh" "$T" > "data/$T.log" 2>&1 || { tail -20 "data/$T.log" >&2; exit 1; }
python ConvertCTMtoFiles.py "$T"
mv "AlignedLyricsOutput/$T/alignedoutput.txt" "$3"

rm -rf "AlignedLyricsOutput/$T" "data/$T" "data/${T}_hires" "data/$T.log" "$L" "run_align_$T.sh" \
    "exp_asru_PHON/chain/cnn-tdnn_sp/ali_$T" "exp_asru_PHON/make_mfcc/$T" \
    mfcc/raw_mfcc_$T.* mfcc/cmvn_$T.*
