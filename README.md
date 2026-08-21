# InferHub Watch

Daily probes of [InferHub](https://inferhub.dev/) Chat Completions. Public report: [alexeyleshchenko.github.io/inferhub-watch](https://alexeyleshchenko.github.io/inferhub-watch/).

A red cell means InferHub’s JSON did not match the documented OpenAI Chat Completions shape for that check. It does not mean InferHub was down, and it does not score the OpenCrabs parser.

Calls run on GitHub-hosted runners with the ops InferHub key (`INFERHUB_API_KEY`). Spend hits the same InferHub balance as OpenCrabs ops. Every cell shows the **resolved publisher** InferHub returned.

## Layout

| Path | Role |
| --- | --- |
| [CONTEXT.md](CONTEXT.md) | Alias, resolved publisher, pass/fail language |
| [models.toml](models.toml) | Aliases to probe |
| [checks/registry.toml](checks/registry.toml) | Check order, titles, scoring |
| [checks/](checks/) | One folder per check (`check.py`, `page.md`, OpenAI-shape `test.py`) |
| [tests/](tests/) | Cross-cutting wiring only (registry, site generate, no secrets) |
| [probe/run.py](probe/run.py) | Writes [data/runs/](data/runs/) |
| [site/generate.py](site/generate.py) | Static HTML from the registry and run files |

## Add a check

1. Create `checks/<id>/check.py` with `run(client, alias) -> dict` using [probe/result.py](probe/result.py).
2. Write `checks/<id>/page.md` in plain language (what / pass / fail / who cares).
3. Put OpenAI-shape fixtures in `checks/<id>/test.py` next to the check. Keep [tests/](tests/) for registry and site wiring only.
4. Append a `[[checks]]` block to [checks/registry.toml](checks/registry.toml). Set `scores_rank = true` only if the check should rank aliases.
5. Keep the runner on the Python 3.12 standard library. If you need pip, stop and ask.

Do not log or commit API keys. Do not store full SSE bodies; keep short summaries and hashes.

## Local

```bash
python3 -m unittest discover -s . -q
export INFERHUB_API_KEY=…
python3 -m probe.run
PAGES_BASE= python3 site/generate.py   # then open site/dist/index.html
```

## GitHub

- Workflow: daily 06:00 UTC and **Run workflow**.
- Secret: `INFERHUB_API_KEY` (ops InferHub key). Fork pull requests do not call InferHub.
- Pages: project site at `/inferhub-watch/`.
