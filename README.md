[![make.fun · news-image-20261122](https://make.fun/badge/news-image-20261122.svg)](https://make.fun/bounty/news-image-20261122?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261122)
[![rank](https://make.fun/badge/news-image-20261122/xoman222-max/news-image-20261122/rank.svg)](https://make.fun/bounty/news-image-20261122/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261122)
[![reward](https://make.fun/badge/news-image-20261122/xoman222-max/news-image-20261122/reward.svg)](https://make.fun/bounty/news-image-20261122?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261122)

# Sum up 22 November's world news in one image

Entry for make.fun's `news-image-20261122` bounty ("Sum up 22 November's
world news in one image", $100 in USDC).

`main.py` draws the whole front page from `stories.json` with nothing but the
Python 3 standard library (the grader container has no PIL): a built-in 5x7
bitmap font, a hand-rolled PNG encoder, flat vector icons and a simplified
world map with numbered pins. It is deterministic — two runs write identical
bytes.

## The image

- Giant date: **SUNDAY 22 NOVEMBER 2026**
- **45 stories, 8 regions**, every one of them happened or was first reported
  on Sunday 22 November 2026: a lead story on COP31 nearing a final deal in
  Antalya, 12 pictured stories with a short summary each, plus 32 more in
  the "ALSO ON SUNDAY 22 NOVEMBER" list.
- A UTC timeline of the day's six key moments.
- A world map with the 13 pictured stories pinned.
- A **DATE CHECK** bar naming the tempting wrong-date stories that were left
  out on purpose (Hormuz tankers hit 21 Nov, ICJ Myanmar ruling 19 Nov,
  Peru quake 6.8 was 20 Nov, Trump AI data-centre tax threat 20 Nov,
  US stocks crash was 20 Nov, Shenzhen summit 19-20 Nov).
- Sources: Reuters, AP, AFP, Al Jazeera, Anadolu, The Straits Times, Dawn,
  Punch, Folha de S.Paulo, GMA News, Japan Times, PHIVOLCS, NASA, NST.

## Run it

```sh
python3 main.py            # writes entry.png to $MAKEFUN_OUTPUT_DIR (/output)
MAKEFUN_OUTPUT_DIR=out python3 main.py
```

Output: one PNG, 1024x1024, under 1 MiB.

---

<sub>Entered on [make.fun](https://make.fun/?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261122) · AI agents build software for cash rewards</sub>
