build:
	python scripts/build_atlas.py

verify:
	python scripts/verify_links.py --limit 100

reports:
	python scripts/prune_candidates.py && python scripts/suggest_replacements.py && python scripts/find_duplicates.py

fixes:
	python scripts/apply_auto_fixes.py
