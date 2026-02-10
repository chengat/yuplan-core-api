"""Run all course timetable scrapers."""

import sys
import importlib.util
from pathlib import Path
from typing import Dict, Any, List, Tuple
from datetime import datetime

scrapers_dir = Path(__file__).parent
fall_winter_dir = scrapers_dir / "fall-winter-2025-2026"
sys.path.insert(0, str(fall_winter_dir))
sys.path.insert(1, str(scrapers_dir))

def _title_from_stem(stem: str) -> str:
    return stem.replace("_", " ").title()


def _load_scrapers(root: Path) -> List[Tuple[str, object, str]]:
    scrapers: List[Tuple[str, object, str]] = []
    for path in sorted(root.glob("*.py")):
        if path.name.startswith("_"):
            continue
        module_name = path.stem
        spec = importlib.util.spec_from_file_location(module_name, path)
        if spec is None or spec.loader is None:
            continue
        module = importlib.util.module_from_spec(spec)
        try:
            spec.loader.exec_module(module)
        except Exception as error:
            print(f"Error importing {module_name}: {error}")
            continue
        if not hasattr(module, "main"):
            continue
        scrapers.append((module_name, module, _title_from_stem(module_name)))

    if not scrapers:
        print(f"No scrapers found in {root}")
        sys.exit(1)

    return scrapers


def run_scraper(name: str, scraper_module, description: str) -> Dict[str, Any]:
    print(f"\n{'='*70}")
    print(f"Running {name} scraper")
    print(f"{description}")
    print(f"{'='*70}\n")
    
    result = {
        "name": name,
        "description": description,
        "success": False,
        "error": None,
        "courses_count": 0,
        "timestamp": datetime.now().isoformat()
    }
    
    try:
        scraper_module.main()
        result["success"] = True
        
        scraper_path = Path(scraper_module.__file__).resolve()
        scraping_dir = scraper_path.parents[2]
        scraper_name = scraper_path.stem
        term_dir = None
        if "fall-winter-2025-2026" in scraper_path.parts: # update for new sessions
            term_dir = "fall-winter-2025-2026"


        candidate_paths = []
        if term_dir:
            candidate_paths.append(scraping_dir / "data" / term_dir / f"{scraper_name}.json")
        else:
            candidate_paths.extend([ # update for new sessions
                scraping_dir / "data" / f"{scraper_name}.json",
                scraping_dir / "data" / "fall-winter-2025-2026" / f"{scraper_name}.json",
                
            ])

        for data_path in candidate_paths:
            if data_path.exists():
                import json
                with open(data_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    result["courses_count"] = len(data.get('courses', []))
                break
        
    except Exception as e:
        result["success"] = False
        result["error"] = str(e)
        print(f"Error in {name} scraper: {e}")
    
    return result


def main():
    """Run all scrapers and provide a summary."""
    print("\n" + "="*70)
    print("YORK UNIVERSITY COURSE TIMETABLE SCRAPERS")
    print("="*70)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    scrapers = _load_scrapers(fall_winter_dir)
    
    results = []
    for name, module, description in scrapers:
        result = run_scraper(name, module, description)
        results.append(result)
    
    # Print summary
    print("\n" + "="*70)
    print("SUMMARY")
    print("="*70)
    
    successful = [r for r in results if r["success"]]
    failed = [r for r in results if not r["success"]]
    
    total_courses = sum(r["courses_count"] for r in successful)
    
    print(f"\nSuccessful: {len(successful)}/{len(results)}")
    print(f"Failed: {len(failed)}/{len(results)}")
    print(f"Total courses scraped: {total_courses}\n")
    
    if successful:
        print("Successful scrapers:")
        for result in successful:
            print(f"  {result['name']:20} - {result['courses_count']:4} courses")
    
    if failed:
        print("\nFailed scrapers:")
        for result in failed:
            print(f"  {result['name']:20} - {result['error']}")
    
    print(f"\nCompleted at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # Exit with error code if any scraper failed
    if failed:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()

