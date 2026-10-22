# Campus pair labelling

The 32 pairs in `data/raw/campus/labelled_campus_pairs.csv` are controlled synthetic examples, not verified ownership claims. Original labels are unchanged. The author and reviewer of the original labels are unknown; they need manual review before publication.

- `match`: the two reports were intentionally written to describe the same physical item. A shared generic category alone is insufficient. Distinctive features, model, location and time support the decision.
- `plausible`: some details agree, but the item is not confirmed as the intended one. These are hard distractors, not positive labels. CAT 2 maps them to binary class 0 as an explicit coursework assumption and also reports a sensitivity check with them excluded; this is not verified non-identity.
- `non_match`: the reports intentionally describe different items, often with a conflicting colour, brand, model, size or distinctive feature.

The `match_type` and `notes` columns preserve the stated rationale. A future review should record reviewer, date, old label, new label and reason in a separate change log rather than silently editing ground truth.

The remaining lost-found combinations are **unlabelled**. They must not be called confirmed false positives. The evaluator reports them separately.
