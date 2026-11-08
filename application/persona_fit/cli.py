"""Command line for the persona-fit pipeline.

    list                          datasets and raw files
    download  --dataset X         fetch direct links, print instructions for gated files
    prepare   --dataset X         load, lock split, draw the scored sample
    personas  --dataset X         one persona YAML per scored person
    tasks     --dataset X         one task folder per distinct scored task card
    jobs      --dataset X         job YAML shards (--with-control adds persona-free shards)
    all       --dataset X         prepare + personas + tasks + jobs
    run       --dataset X --mode full|none
    score     --dataset X         metrics vs observed decisions (and vs the control, if run)
    templates [--dataset X]       (re)write checked-in template tasks
"""

from __future__ import annotations

import argparse
import json
import sys

from .registry import ADAPTERS, all_adapters, get_adapter


def _datasets(args: argparse.Namespace) -> list:
    if getattr(args, "dataset", None) in (None, "all"):
        return all_adapters()
    return [get_adapter(slug) for slug in args.dataset.split(",")]


def _modes(args: argparse.Namespace) -> tuple[str, ...]:
    return ("full", "none") if getattr(args, "with_control", False) else ("full",)


def cmd_list(_: argparse.Namespace) -> None:
    for adapter in all_adapters():
        print("{:<22} {:<3} {:<11} {:<11} {}".format(
            adapter.slug, adapter.sheet_id, adapter.path, adapter.decision_type, adapter.title))
        for f in adapter.raw_files:
            print("    {} {}".format("direct" if f.url else "manual", f.name))


def cmd_download(args: argparse.Namespace) -> None:
    from .download import download

    for adapter in _datasets(args):
        print("== {}".format(adapter.slug))
        for line in download(adapter, force=args.force):
            print("  " + line)


def _prepare(adapter, args):
    from .prepare import prepare

    prepared = prepare(
        adapter,
        sample_rows=args.sample_rows,
        max_rows_per_person=args.max_rows_per_person,
        skip_people=set(getattr(args, "skip_people", "") .split(",")) - {""},
    )
    print("{}: {}".format(adapter.slug, json.dumps(prepared.manifest["counts"])))
    return prepared


def cmd_prepare(args: argparse.Namespace) -> None:
    for adapter in _datasets(args):
        _prepare(adapter, args)


def cmd_personas(args: argparse.Namespace) -> None:
    from .personas import build_personas
    from .prepare import load_prepared

    for adapter in _datasets(args):
        paths = build_personas(adapter, load_prepared(adapter))
        print("{}: {} personas".format(adapter.slug, len(paths)))


def cmd_tasks(args: argparse.Namespace) -> None:
    from .prepare import load_prepared
    from .tasks import build_tasks

    for adapter in _datasets(args):
        summary = build_tasks(adapter, load_prepared(adapter))
        print("{}: {} tasks".format(adapter.slug, summary["taskCount"]))


def cmd_jobs(args: argparse.Namespace) -> None:
    from .jobs import make_jobs

    for adapter in _datasets(args):
        written = make_jobs(
            adapter, modes=_modes(args), model=args.model, max_agents=args.max_agents,
            n_concurrent=args.concurrent, tag=getattr(args, "tag", ""),
        )
        print("{}: {}".format(adapter.slug, {m: len(v) for m, v in written.items()}))


def cmd_all(args: argparse.Namespace) -> None:
    from .jobs import make_jobs
    from .personas import build_personas
    from .tasks import build_tasks

    for adapter in _datasets(args):
        prepared = _prepare(adapter, args)
        print("  personas: {}".format(len(build_personas(adapter, prepared))))
        print("  tasks:    {}".format(build_tasks(adapter, prepared)["taskCount"]))
        written = make_jobs(adapter, modes=_modes(args), model=args.model, max_agents=args.max_agents, n_concurrent=args.concurrent)
        print("  jobs:     {}".format({m: len(v) for m, v in written.items()}))


def cmd_run(args: argparse.Namespace) -> None:
    from .jobs import run_jobs

    failures = 0
    for adapter in _datasets(args):
        for config, code in run_jobs(
            adapter, args.mode, parallel=args.parallel, limit=args.limit,
            max_cost_usd=args.max_cost_usd, dry_run=args.dry_run,
            tag=getattr(args, "tag", ""),
        ):
            if code:
                failures += 1
                print("failed ({}): {}".format(code, config), file=sys.stderr)
    if failures:
        sys.exit(1)


def cmd_score(args: argparse.Namespace) -> None:
    from .score import render_markdown, score_dataset

    for adapter in _datasets(args):
        print(render_markdown(score_dataset(adapter, n_boot=args.n_boot)))


def cmd_templates(args: argparse.Namespace) -> None:
    from .tasks import build_template

    for adapter in _datasets(args):
        print("{}: {}".format(adapter.slug, build_template(adapter)))


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="run_persona_fit", description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)

    def add(name, func, *, dataset_required=True):
        p = sub.add_parser(name)
        p.add_argument("--dataset", required=dataset_required,
                       help="Slug, comma list, or 'all': {}".format(", ".join(ADAPTERS)))
        p.set_defaults(func=func)
        return p

    p = sub.add_parser("list")
    p.set_defaults(func=cmd_list)
    add("download", cmd_download).add_argument("--force", action="store_true")
    for name, func in (("prepare", cmd_prepare), ("all", cmd_all)):
        p = add(name, func)
        p.add_argument("--sample-rows", type=int, default=None, help="Scored test rows (default: per dataset)")
        p.add_argument("--max-rows-per-person", type=int, default=10)
        p.add_argument("--skip-people", default="", help="Comma-separated person ids already scored; draw the next people")
        if name == "all":
            p.add_argument("--model", default="anthropic/claude-sonnet-4-6")
            p.add_argument("--max-agents", type=int, default=100)
            p.add_argument("--concurrent", type=int, default=4)
            p.add_argument("--with-control", action="store_true", help="Also write persona-free (mode none) shards")
    add("personas", cmd_personas)
    add("tasks", cmd_tasks)
    p = add("jobs", cmd_jobs)
    p.add_argument("--model", default="anthropic/claude-sonnet-4-6")
    p.add_argument("--max-agents", type=int, default=100)
    p.add_argument("--concurrent", type=int, default=4)
    p.add_argument("--tag", default="", help="Model tag in the job name, so a new model does not reuse old trials")
    p.add_argument("--with-control", action="store_true", help="Also write persona-free (mode none) shards")
    p = add("run", cmd_run)
    p.add_argument("--mode", choices=["full", "none"], required=True)
    p.add_argument("--tag", default="", help="Model tag matching the jobs written with --tag")
    p.add_argument("--parallel", type=int, default=1, help="Job shards at once")
    p.add_argument("--limit", type=int, default=None, help="Run at most N pending shards")
    p.add_argument("--max-cost-usd", type=float, default=None)
    p.add_argument("--dry-run", action="store_true")
    p = add("score", cmd_score)
    p.add_argument("--n-boot", type=int, default=500)
    add("templates", cmd_templates, dataset_required=False)

    args = parser.parse_args(argv)
    args.func(args)
