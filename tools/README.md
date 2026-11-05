# Weekly build

1. Write the new issue as `src/issueN.html` (same template as earlier issues).
2. Add `{"n": N, "week": "..."}` to the top of `issues.json`.
3. `node tools/render.js N` → `issues/off-the-record-issue-N.pdf` (+ HD PNG in /home/claude).
4. `python3 tools/trailer.py N` → `/home/claude/off-the-record-issue-N-trailer.mp4` (not committed).
5. `python3 tools/build_site.py` → rebuilds `index.html`.
6. Commit and push to `main`; GitHub Pages republishes in about a minute.
