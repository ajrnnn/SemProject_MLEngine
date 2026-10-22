# Pair classification model

**AI Application: Classification. Algorithm/Approach: Logistic Regression.**

```text
Lost report + found report
            |
    normalize and compare
            |
 numeric feature vector X
            |
  Logistic Regression
            |
 match score in [0, 1]
            |
 class 0 or 1 at threshold 0.5
```

The features include normalized description overlap, exact attribute matches or conflicts, distinctive-feature overlap, location wording overlap, and capped time distance. Missing attributes create neither a match nor a conflict. `matching_system/feature_builder.py` defines the calculations; `data/processed/modelling_pairs.csv` lets a student inspect every input row.

The classifier is trained on synthetic labelled pairs. `match` maps to 1; `plausible` and `non_match` map to 0 for this coursework run. `plausible` means unconfirmed, so a second analysis excludes it. StandardScaler and Logistic Regression are fitted together inside each development fold. The fixed group split separates lost report IDs and their labelled found candidates. The held-out partition contains only eight labelled pairs, so even strong scores cannot be presented as deployment accuracy. Coefficients in `results/ml/coefficients.csv` describe this fitted sample and are not causal explanations.

In a future application, the same model's scores could sort several found reports. The API and Android starter do not run it yet. The current `matching_system/matcher.py` is the separately evaluated **Rule-Based Baseline**. Candidate ranking and ownership verification are different tasks: staff must verify a claimant before releasing an item.

## Future image extension

```text
Text features + metadata features + measured image similarity
                          |
               retrained classifier
                          |
             score and candidate order
```

Images require labelled photographs of the same physical items and comparable different items. A frozen CLIP encoder could supply image/image or text/image similarity values. Only then should we compare text-only against text-plus-image results. Roboflow object-detection categories alone cannot establish item identity. No image embeddings or CLIP scores are measured in this repository.
