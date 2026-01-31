#!/usr/bin/env python3
"""
pulse - Research a topic from the last 30 days on Reddit + X + HackerNews + GitHub.

Usage:
    python3 pulse.py <topic> [options]

Options:
    --mock              Use fixtures instead of real API calls
    --emit=MODE         Output mode: compact|json|md|context|path (default: compact)
    --sources=MODE      Source selection: auto|reddit|x|both (default: auto)
    --quick             Faster research with fewer sources (8-12 each)
    --deep              Comprehensive research with more sources (50-70 Reddit, 40-60 X)
    --debug             Enable verbose debug logging
    --no-hn             Skip HackerNews search
    --no-github         Skip GitHub search
"""

import argparse
import json
import os
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path

# Add lib to path
SCRIPT_DIR = Path(__file__).parent.resolve()
sys.path.insert(0, str(SCRIPT_DIR))

from lib import (
    dates,
    dedupe,
    env,
    github_search,
    hackernews,
    http,
    models,
    normalize,
    openai_reddit,
    reddit_enrich,
    render,
    schema,
    score,
    ui,
    websearch,
    xai_x,
)


def load_fixture(name: str) -> dict:
    """Load a fixture file."""
    fixture_path = SCRIPT_DIR.parent / "fixtures" / name
    if fixture_path.exists():
        with open(fixture_path) as f:
            return json.load(f)
    return {}


def _search_reddit(
    topic: str,
    config: dict,
    selected_models: dict,
    from_date: str,
    to_date: str,
    depth: str,
    mock: bool,
) -> tuple:
    """Search Reddit via OpenAI (runs in thread).

    Returns:
        Tuple of (reddit_items, raw_openai, error)
    """
    raw_openai = None
    reddit_error = None

    if mock:
        raw_openai = load_fixture("openai_sample.json")
    else:
        try:
            raw_openai = openai_reddit.search_reddit(
                config["OPENAI_API_KEY"],
                selected_models["openai"],
                topic,
                from_date,
                to_date,
                depth=depth,
            )
        except http.HTTPError as e:
            raw_openai = {"error": str(e)}
            reddit_error = f"API error: {e}"
        except Exception as e:
            raw_openai = {"error": str(e)}
            reddit_error = f"{type(e).__name__}: {e}"

    # Parse response
    reddit_items = openai_reddit.parse_reddit_response(raw_openai or {})

    # Quick retry with simpler query if few results
    if len(reddit_items) < 5 and not mock and not reddit_error:
        core = openai_reddit._extract_core_subject(topic)
        if core.lower() != topic.lower():
            try:
                retry_raw = openai_reddit.search_reddit(
                    config["OPENAI_API_KEY"],
                    selected_models["openai"],
                    core,
                    from_date, to_date,
                    depth=depth,
                )
                retry_items = openai_reddit.parse_reddit_response(retry_raw)
                # Add items not already found (by URL)
                existing_urls = {item.get("url") for item in reddit_items}
                for item in retry_items:
                    if item.get("url") not in existing_urls:
                        reddit_items.append(item)
            except Exception:
                pass

    return reddit_items, raw_openai, reddit_error


def _search_x(
    topic: str,
    config: dict,
    selected_models: dict,
    from_date: str,
    to_date: str,
    depth: str,
    mock: bool,
) -> tuple:
    """Search X via xAI (runs in thread).

    Returns:
        Tuple of (x_items, raw_xai, error)
    """
    raw_xai = None
    x_error = None

    if mock:
        raw_xai = load_fixture("xai_sample.json")
    else:
        try:
            raw_xai = xai_x.search_x(
                config["XAI_API_KEY"],
                selected_models["xai"],
                topic,
                from_date,
                to_date,
                depth=depth,
            )
        except http.HTTPError as e:
            raw_xai = {"error": str(e)}
            x_error = f"API error: {e}"
        except Exception as e:
            raw_xai = {"error": str(e)}
            x_error = f"{type(e).__name__}: {e}"

    # Parse response
    x_items = xai_x.parse_x_response(raw_xai or {})

    return x_items, raw_xai, x_error


def _search_hn(
    topic: str,
    from_date: str,
    to_date: str,
    depth: str,
    mock: bool,
) -> tuple:
    """Search HackerNews via Algolia (runs in thread).

    Returns:
        Tuple of (hn_items, raw_hn, error)
    """
    raw_hn = None
    hn_error = None

    if mock:
        raw_hn = load_fixture("hn_sample.json")
    else:
        try:
            raw_hn = hackernews.search_hn(
                topic,
                from_date,
                to_date,
                depth=depth,
            )
        except http.HTTPError as e:
            raw_hn = {"error": str(e)}
            hn_error = f"API error: {e}"
        except Exception as e:
            raw_hn = {"error": str(e)}
            hn_error = f"{type(e).__name__}: {e}"

    # Parse response
    hn_items = hackernews.parse_hn_response(raw_hn or {})

    return hn_items, raw_hn, hn_error


def _search_github(
    topic: str,
    from_date: str,
    to_date: str,
    depth: str,
    mock: bool,
) -> tuple:
    """Search GitHub repositories (runs in thread).

    Returns:
        Tuple of (github_items, raw_github, error)
    """
    raw_github = None
    github_error = None

    if mock:
        raw_github = load_fixture("github_sample.json")
    else:
        try:
            raw_github = github_search.search_github(
                topic,
                from_date,
                to_date,
                depth=depth,
            )
        except http.HTTPError as e:
            raw_github = {"error": str(e)}
            github_error = f"API error: {e}"
        except Exception as e:
            raw_github = {"error": str(e)}
            github_error = f"{type(e).__name__}: {e}"

    # Parse response
    github_items = github_search.parse_github_response(raw_github or {})

    return github_items, raw_github, github_error


def run_research(
    topic: str,
    sources: str,
    config: dict,
    selected_models: dict,
    from_date: str,
    to_date: str,
    depth: str = "default",
    mock: bool = False,
    progress: ui.ProgressDisplay = None,
    skip_hn: bool = False,
    skip_github: bool = False,
) -> tuple:
    """Run the research pipeline.

    Returns:
        Tuple of (reddit_items, x_items, hn_items, github_items, web_needed,
                  raw_openai, raw_xai, raw_hn, raw_github, raw_reddit_enriched,
                  reddit_error, x_error, hn_error, github_error)
    """
    reddit_items = []
    x_items = []
    hn_items = []
    github_items = []
    raw_openai = None
    raw_xai = None
    raw_hn = None
    raw_github = None
    raw_reddit_enriched = []
    reddit_error = None
    x_error = None
    hn_error = None
    github_error = None

    # Check if WebSearch is needed (always needed in web-only mode)
    web_needed = sources in ("all", "web", "reddit-web", "x-web")

    # Determine which searches to run
    run_reddit = sources in ("both", "reddit", "all", "reddit-web")
    run_x = sources in ("both", "x", "all", "x-web")
    run_hn = not skip_hn
    run_github = not skip_github

    # Web-only mode with no HN/GitHub: Claude handles everything
    if sources == "web" and skip_hn and skip_github:
        if progress:
            progress.start_web_only()
            progress.end_web_only()
        return (reddit_items, x_items, hn_items, github_items, True,
                raw_openai, raw_xai, raw_hn, raw_github, raw_reddit_enriched,
                reddit_error, x_error, hn_error, github_error)

    # Run all searches in parallel (up to 4 workers)
    futures = {}

    with ThreadPoolExecutor(max_workers=4) as executor:
        # Submit Reddit search
        if run_reddit:
            if progress:
                progress.start_reddit()
            futures["reddit"] = executor.submit(
                _search_reddit, topic, config, selected_models,
                from_date, to_date, depth, mock
            )

        # Submit X search
        if run_x:
            if progress:
                progress.start_x()
            futures["x"] = executor.submit(
                _search_x, topic, config, selected_models,
                from_date, to_date, depth, mock
            )

        # Submit HN search (always free)
        if run_hn:
            if progress:
                progress.start_hn()
            futures["hn"] = executor.submit(
                _search_hn, topic, from_date, to_date, depth, mock
            )

        # Submit GitHub search (always free)
        if run_github:
            if progress:
                progress.start_github()
            futures["github"] = executor.submit(
                _search_github, topic, from_date, to_date, depth, mock
            )

        # Collect results
        if "reddit" in futures:
            try:
                reddit_items, raw_openai, reddit_error = futures["reddit"].result()
                if reddit_error and progress:
                    progress.show_error(f"Reddit error: {reddit_error}")
            except Exception as e:
                reddit_error = f"{type(e).__name__}: {e}"
                if progress:
                    progress.show_error(f"Reddit error: {e}")
            if progress:
                progress.end_reddit(len(reddit_items))

        if "x" in futures:
            try:
                x_items, raw_xai, x_error = futures["x"].result()
                if x_error and progress:
                    progress.show_error(f"X error: {x_error}")
            except Exception as e:
                x_error = f"{type(e).__name__}: {e}"
                if progress:
                    progress.show_error(f"X error: {e}")
            if progress:
                progress.end_x(len(x_items))

        if "hn" in futures:
            try:
                hn_items, raw_hn, hn_error = futures["hn"].result()
                if hn_error and progress:
                    progress.show_error(f"HN error: {hn_error}")
            except Exception as e:
                hn_error = f"{type(e).__name__}: {e}"
                if progress:
                    progress.show_error(f"HN error: {e}")
            if progress:
                progress.end_hn(len(hn_items))

        if "github" in futures:
            try:
                github_items, raw_github, github_error = futures["github"].result()
                if github_error and progress:
                    progress.show_error(f"GitHub error: {github_error}")
            except Exception as e:
                github_error = f"{type(e).__name__}: {e}"
                if progress:
                    progress.show_error(f"GitHub error: {e}")
            if progress:
                progress.end_github(len(github_items))

    # Enrich Reddit items with real data (sequential, but with error handling per-item)
    if reddit_items:
        if progress:
            progress.start_reddit_enrich(1, len(reddit_items))

        for i, item in enumerate(reddit_items):
            if progress and i > 0:
                progress.update_reddit_enrich(i + 1, len(reddit_items))

            try:
                if mock:
                    mock_thread = load_fixture("reddit_thread_sample.json")
                    reddit_items[i] = reddit_enrich.enrich_reddit_item(item, mock_thread)
                else:
                    reddit_items[i] = reddit_enrich.enrich_reddit_item(item)
            except Exception as e:
                # Log but don't crash - keep the unenriched item
                if progress:
                    progress.show_error(f"Enrich failed for {item.get('url', 'unknown')}: {e}")

            raw_reddit_enriched.append(reddit_items[i])

        if progress:
            progress.end_reddit_enrich()

    return (reddit_items, x_items, hn_items, github_items, web_needed,
            raw_openai, raw_xai, raw_hn, raw_github, raw_reddit_enriched,
            reddit_error, x_error, hn_error, github_error)


def main():
    parser = argparse.ArgumentParser(
        description="Research a topic from the last 30 days on Reddit + X + HackerNews + GitHub"
    )
    parser.add_argument("topic", nargs="?", help="Topic to research")
    parser.add_argument("--mock", action="store_true", help="Use fixtures")
    parser.add_argument(
        "--emit",
        choices=["compact", "json", "md", "context", "path"],
        default="compact",
        help="Output mode",
    )
    parser.add_argument(
        "--sources",
        choices=["auto", "reddit", "x", "both"],
        default="auto",
        help="Source selection",
    )
    parser.add_argument(
        "--quick",
        action="store_true",
        help="Faster research with fewer sources (8-12 each)",
    )
    parser.add_argument(
        "--deep",
        action="store_true",
        help="Comprehensive research with more sources (50-70 Reddit, 40-60 X)",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable verbose debug logging",
    )
    parser.add_argument(
        "--include-web",
        action="store_true",
        help="Include general web search alongside Reddit/X (lower weighted)",
    )
    parser.add_argument(
        "--no-hn",
        action="store_true",
        help="Skip HackerNews search",
    )
    parser.add_argument(
        "--no-github",
        action="store_true",
        help="Skip GitHub search",
    )

    args = parser.parse_args()

    # Enable debug logging if requested
    if args.debug:
        os.environ["PULSE_DEBUG"] = "1"
        # Re-import http to pick up debug flag
        from lib import http as http_module
        http_module.DEBUG = True

    # Determine depth
    if args.quick and args.deep:
        print("Error: Cannot use both --quick and --deep", file=sys.stderr)
        sys.exit(1)
    elif args.quick:
        depth = "quick"
    elif args.deep:
        depth = "deep"
    else:
        depth = "default"

    if not args.topic:
        print("Error: Please provide a topic to research.", file=sys.stderr)
        print("Usage: python3 pulse.py <topic> [options]", file=sys.stderr)
        sys.exit(1)

    # Load config
    config = env.get_config()

    # Check available sources
    available = env.get_available_sources(config)

    # Mock mode can work without keys
    if args.mock:
        if args.sources == "auto":
            sources = "both"
        else:
            sources = args.sources
    else:
        # Validate requested sources against available
        sources, error = env.validate_sources(args.sources, available, args.include_web)
        if error:
            # If it's a warning about WebSearch fallback, print but continue
            if "WebSearch fallback" in error:
                print(f"Note: {error}", file=sys.stderr)
            else:
                print(f"Error: {error}", file=sys.stderr)
                sys.exit(1)

    # Get date range
    from_date, to_date = dates.get_date_range(30)

    # Check what keys are missing for promo messaging
    missing_keys = env.get_missing_keys(config)

    # Initialize progress display
    progress = ui.ProgressDisplay(args.topic, show_banner=True)

    # Show promo for missing keys BEFORE research
    if missing_keys != 'none':
        progress.show_promo(missing_keys)

    # Select models
    if args.mock:
        # Use mock models
        mock_openai_models = load_fixture("models_openai_sample.json").get("data", [])
        mock_xai_models = load_fixture("models_xai_sample.json").get("data", [])
        selected_models = models.get_models(
            {
                "OPENAI_API_KEY": "mock",
                "XAI_API_KEY": "mock",
                **config,
            },
            mock_openai_models,
            mock_xai_models,
        )
    else:
        selected_models = models.get_models(config)

    # Determine mode string
    has_reddit_x = sources not in ("web",)
    has_hn = not args.no_hn
    has_github = not args.no_github

    if sources == "web" and has_hn and has_github:
        mode = "lite"  # HN + GitHub + Web (no API keys)
    elif sources == "web" and not has_hn and not has_github:
        mode = "web-only"
    elif sources == "all":
        mode = "all"
    elif sources == "both":
        mode = "both"
    elif sources == "reddit":
        mode = "reddit-only"
    elif sources == "reddit-web":
        mode = "reddit-web"
    elif sources == "x":
        mode = "x-only"
    elif sources == "x-web":
        mode = "x-web"
    elif sources == "web":
        mode = "lite" if (has_hn or has_github) else "web-only"
    else:
        mode = sources

    # Run research
    (reddit_items, x_items, hn_items, github_items, web_needed,
     raw_openai, raw_xai, raw_hn, raw_github, raw_reddit_enriched,
     reddit_error, x_error, hn_error, github_error) = run_research(
        args.topic,
        sources,
        config,
        selected_models,
        from_date,
        to_date,
        depth,
        args.mock,
        progress,
        skip_hn=args.no_hn,
        skip_github=args.no_github,
    )

    # Processing phase
    progress.start_processing()

    # Normalize items
    normalized_reddit = normalize.normalize_reddit_items(reddit_items, from_date, to_date)
    normalized_x = normalize.normalize_x_items(x_items, from_date, to_date)
    normalized_hn = normalize.normalize_hn_items(hn_items, from_date, to_date)
    normalized_github = normalize.normalize_github_items(github_items, from_date, to_date)

    # Hard date filter: exclude items with verified dates outside the range
    filtered_reddit = normalize.filter_by_date_range(normalized_reddit, from_date, to_date)
    filtered_x = normalize.filter_by_date_range(normalized_x, from_date, to_date)
    filtered_hn = normalize.filter_by_date_range(normalized_hn, from_date, to_date)
    filtered_github = normalize.filter_by_date_range(normalized_github, from_date, to_date)

    # Score items
    scored_reddit = score.score_reddit_items(filtered_reddit)
    scored_x = score.score_x_items(filtered_x)
    scored_hn = score.score_hn_items(filtered_hn)
    scored_github = score.score_github_items(filtered_github)

    # Sort items
    sorted_reddit = score.sort_items(scored_reddit)
    sorted_x = score.sort_items(scored_x)
    sorted_hn = score.sort_items(scored_hn)
    sorted_github = score.sort_items(scored_github)

    # Dedupe items
    deduped_reddit = dedupe.dedupe_reddit(sorted_reddit)
    deduped_x = dedupe.dedupe_x(sorted_x)
    deduped_hn = dedupe.dedupe_hn(sorted_hn)
    deduped_github = dedupe.dedupe_github(sorted_github)

    progress.end_processing()

    # Create report
    report = schema.create_report(
        args.topic,
        from_date,
        to_date,
        mode,
        selected_models.get("openai"),
        selected_models.get("xai"),
    )
    report.reddit = deduped_reddit
    report.x = deduped_x
    report.hackernews = deduped_hn
    report.github = deduped_github
    report.reddit_error = reddit_error
    report.x_error = x_error
    report.hn_error = hn_error
    report.github_error = github_error

    # Generate context snippet
    report.context_snippet_md = render.render_context_snippet(report)

    # Write outputs
    render.write_outputs(report, raw_openai, raw_xai, raw_reddit_enriched, raw_hn, raw_github)

    # Show completion
    if mode == "web-only":
        progress.show_web_only_complete()
    elif mode == "lite" and not reddit_items and not x_items:
        progress.show_lite_complete(len(deduped_hn), len(deduped_github))
    else:
        progress.show_complete(len(deduped_reddit), len(deduped_x), len(deduped_hn), len(deduped_github))

    # Output result
    output_result(report, args.emit, web_needed, args.topic, from_date, to_date, missing_keys)


def output_result(
    report: schema.Report,
    emit_mode: str,
    web_needed: bool = False,
    topic: str = "",
    from_date: str = "",
    to_date: str = "",
    missing_keys: str = "none",
):
    """Output the result based on emit mode."""
    if emit_mode == "compact":
        print(render.render_compact(report, missing_keys=missing_keys))
    elif emit_mode == "json":
        print(json.dumps(report.to_dict(), indent=2))
    elif emit_mode == "md":
        print(render.render_full_report(report))
    elif emit_mode == "context":
        print(report.context_snippet_md)
    elif emit_mode == "path":
        print(render.get_context_path())

    # Output WebSearch instructions if needed
    if web_needed:
        print("\n" + "="*60)
        print("### WEBSEARCH REQUIRED ###")
        print("="*60)
        print(f"Topic: {topic}")
        print(f"Date range: {from_date} to {to_date}")
        print("")
        print("Claude: Use your WebSearch tool to find 8-15 relevant web pages.")
        print("EXCLUDE: reddit.com, x.com, twitter.com, news.ycombinator.com, github.com (already covered above)")
        print("INCLUDE: blogs, docs, news, tutorials from the last 30 days")
        print("")
        print("After searching, synthesize WebSearch results WITH the Reddit/X/HN/GitHub")
        print("results above. WebSearch items should rank LOWER than comparable")
        print("Reddit/X/HN/GitHub items (they lack engagement metrics).")
        print("="*60)


if __name__ == "__main__":
    main()
