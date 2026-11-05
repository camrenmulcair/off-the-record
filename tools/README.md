# Weekly build

1. Write the new issue as `src/issueN.html` (copy the previous one as the template).
2. Add `{"n": N, "week": "..."}` to the top of `issues.json`.
3. Add the issue's sources to `sources.json` under `"N"`: key = the start of each story's headline, value = `[["Outlet: title", "url"], ...]`; `"__calls"` holds the scorecard sources.
4. If there's a new group-chat reaction, add it to the top of `reactions.json` (`{"after": N, "msgs": [{"from": "...", "text": "..."}, {"from": "Camren", "me": true, "text": "..."}]}`), copied word for word.
5. `node tools/render.js N` → `issues/off-the-record-issue-N.pdf` (+ HD PNG in /home/claude).
6. `python3 tools/trailer.py N` → `/home/claude/off-the-record-issue-N-trailer.mp4` (not committed).
7. `python3 tools/build_site.py` → rebuilds `index.html` (issues, My calls tracker, Best reactions).
8. Commit and push to `main`; GitHub Pages republishes in about a minute.
