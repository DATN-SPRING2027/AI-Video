---
name: add-knowledge-graphs
description: Add the 2D Knowledge Graph, 3D Knowledge Graph and/or 3D Semantic Graph from the 2d-3d-knowledge-graph package to the current app, wired to its notes or data and to its way of opening a note. Use when the user asks to add a knowledge graph, note graph, Obsidian-style graph, 3D graph or semantic map to their app.
---

# Add knowledge graphs to this app

1. Read https://github.com/hungnv26/2d-3d-knowledge-graph/blob/main/AGENTS.md (or `node_modules/2d-3d-knowledge-graph/AGENTS.md` once installed from GitHub) and follow it step by step.
2. Ask the user only what the code can't tell you:
   - which of the three graphs they want;
   - where their notes or records live, if that isn't obvious;
   - what should happen when a node is opened, if the app has several ways to show a note.
3. Prefer the ready-made pieces:
   - the `kg-links` and `kg-graphify` tools and `tools/semantic/build.py` for data;
   - `createHost` / `createStaticSemantic` for the host;
   - the React or Vue components when the app uses those frameworks.
4. Before finishing, run through AGENTS.md section 8 ("Check your work"). Report the node and link counts the graphs show.
5. Add the credit line from AGENTS.md section 7.9 unless the user declines.
