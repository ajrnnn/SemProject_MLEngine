# Next steps

## Before CAT 2

1. On each presenter's machine, install `requirements.txt` and obtain the local Delhi CSV as described in `docs/DATASET.md`; run `python -m scripts.run_cat2`, `python run_evaluation.py` and `python -m pytest -q`.
2. The CAT 2 notebook's 11 code cells and four EDA figures were verified on 22 October 2026. Re-run it from the repository root on the presentation machine and check that its counts and plots agree with the saved outputs.
3. Independently review the original pair labels, especially `plausible`, and document any change separately. Do not silently edit raw files.
4. Each student should explain raw/clean data, features, X/y, training, grouped cross-validation, confusion matrix, precision, recall, F1 and a false negative.
5. Check the course's shared spreadsheet entry and presentation schedule. Commit the final notebook before the course deadline; review any public data for personal details.

## After CAT 2

1. Download and inspect licensed Roboflow images only if object detection serves a defined feature.
2. Collect consented same-item campus photographs with `instance_id`, pair labels and reviewer records.
3. Test frozen pretrained CLIP image/image and text/image similarities on held-out physical items.
4. Compare text-only and text-plus-image Logistic Regression on the same labelled pairs.
5. Compare Random Forest and Support Vector Machine on the same features, groups and metrics; report measured results only.
6. Build a durable, permission-controlled backend and integrate the tested matching flow with the Kotlin app. Preserve staff ownership verification.
