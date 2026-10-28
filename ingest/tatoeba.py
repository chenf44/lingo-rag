"""Build a pairs TSV (id, lang, text, translation) from the Tatoeba exports.

Tatoeba data is CC BY 2.0 FR: keep the attribution in the README and UI.

Usage (run on your own machine or Colab, not on Vercel):
    python -m ingest.tatoeba --download            # fetch the two exports into data/raw/
    python -m ingest.tatoeba --limit 1000          # write data/pairs.tsv

Exports used (see https://tatoeba.org/downloads):
    sentences.tar.bz2 -> sentences.csv : sentence_id <TAB> lang <TAB> text
    links.tar.bz2     -> links.csv     : sentence_id <TAB> translation_id
"""

import argparse
import csv
import tarfile
from pathlib import Path

import httpx

EXPORTS = {
    "sentences": "https://downloads.tatoeba.org/exports/sentences.tar.bz2",
    "links": "https://downloads.tatoeba.org/exports/links.tar.bz2",
}
# Tatoeba language codes -> our codes
SOURCE_LANGS = {"eng": "en", "tha": "th"}
TRANSLATION_LANG = "cmn"  # Mandarin Chinese

RAW_DIR = Path("data/raw")


def download(raw_dir: Path = RAW_DIR) -> None:
    raw_dir.mkdir(parents=True, exist_ok=True)
    for name, url in EXPORTS.items():
        archive = raw_dir / f"{name}.tar.bz2"
        if not archive.exists():
            print(f"Downloading {url} ...")
            with httpx.stream("GET", url, timeout=None, follow_redirects=True) as r:
                r.raise_for_status()
                with archive.open("wb") as f:
                    for chunk in r.iter_bytes():
                        f.write(chunk)
        print(f"Extracting {archive} ...")
        with tarfile.open(archive, "r:bz2") as tar:
            tar.extractall(raw_dir, filter="data")


def build_pairs(raw_dir: Path, out: Path, limit: int) -> None:
    csv.field_size_limit(10**7)
    wanted = set(SOURCE_LANGS) | {TRANSLATION_LANG}
    lang_of: dict[int, str] = {}
    text_of: dict[int, str] = {}
    with (raw_dir / "sentences.csv").open(encoding="utf-8", newline="") as f:
        for row in csv.reader(f, delimiter="\t", quoting=csv.QUOTE_NONE):
            if len(row) < 3 or row[1] not in wanted:
                continue
            sid = int(row[0])
            lang_of[sid] = row[1]
            text_of[sid] = row[2]

    translation_of: dict[int, int] = {}
    with (raw_dir / "links.csv").open(encoding="utf-8", newline="") as f:
        for row in csv.reader(f, delimiter="\t", quoting=csv.QUOTE_NONE):
            src, dst = int(row[0]), int(row[1])
            if (
                lang_of.get(src) in SOURCE_LANGS
                and lang_of.get(dst) == TRANSLATION_LANG
                and src not in translation_of
            ):
                translation_of[src] = dst

    counts = dict.fromkeys(SOURCE_LANGS, 0)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f, delimiter="\t")
        writer.writerow(["id", "lang", "text", "translation"])
        for src in sorted(translation_of):
            tl = lang_of[src]
            if counts[tl] >= limit:
                continue
            writer.writerow(
                [src, SOURCE_LANGS[tl], text_of[src], text_of[translation_of[src]]]
            )
            counts[tl] += 1
    print(f"Wrote {out}: {counts}")


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    p.add_argument("--download", action="store_true", help="download and extract the exports")
    p.add_argument("--limit", type=int, default=1000, help="max pairs per source language")
    p.add_argument("--out", type=Path, default=Path("data/pairs.tsv"))
    args = p.parse_args()
    if args.download:
        download()
    build_pairs(RAW_DIR, args.out, args.limit)


if __name__ == "__main__":
    main()
