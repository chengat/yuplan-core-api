"""Run all course timetable scrapers."""

import sys
from pathlib import Path
from typing import Dict, Any
from datetime import datetime

scrapers_dir = Path(__file__).parent
sys.path.insert(0, str(scrapers_dir))

try:
    import graduate_studies
    import lassonde
    import urban
    import glendon
    import schulich
    import education
    import school_of_arts
    import liberal_arts
    import health
    import science
except ImportError as e:
    print(f"Error importing scrapers: {e}")
    print("Make sure all scraper modules are available.")
    sys.exit(1)


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
        
        scraping_dir = Path(scraper_module.__file__).resolve().parents[1]
        scraper_name = Path(scraper_module.__file__).stem
        data_path = scraping_dir / "data" / f"{scraper_name}.json"
        
        if data_path.exists():
            import json
            with open(data_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                result["courses_count"] = len(data.get('courses', []))
        
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
    
    scrapers = [
        ("graduate_studies", graduate_studies, "Graduate Studies"),
        ("lassonde", lassonde, "Lassonde School of Engineering"),
        ("urban", urban, "Urban Studies"),
        ("glendon", glendon, "Glendon College"),
        ("schulich", schulich, "Schulich School of Business"),
        ("education", education, "Education"),
        ("school_of_arts", school_of_arts, "School of Arts"),
        ("liberal_arts", liberal_arts, "Liberal Arts and Professional Studies"),
        ("health", health, "Health"),
        ("science", science, "Science"),
    ]
    
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

