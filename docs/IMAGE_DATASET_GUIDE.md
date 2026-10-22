# Preparing an image dataset later

The CAT 2 classifier needs no image packages. There are currently no downloaded Roboflow images or own campus item photographs in the repository.

## Two different tasks

* **Roboflow version 2** is an object-detection dataset. Its boxes can support category recognition, but do not say whether two photos show the same physical item. If downloaded, preserve the export under `data/raw/roboflow/`, its source/version/licence, and its original split. Run `scripts/prepare_image_data.py` to inventory it; inspect corrupt files, annotation validity, classes and near duplicates before any model use. The published version has no validation set, so create one from training only if training a detector.
* **Own same-item photos** are needed to evaluate lost/found picture matching. As a manageable planning target, start with about 50 consented physical items and roughly four photos per item (around 200 images), then adjust based on feasibility. Include front, back, side and changed lighting/background. These are targets, not collected counts or measured results.

The metadata template is `data/metadata/image_metadata_template.csv`. `category` means an item type (for example, backpack); `instance_id` means one exact physical object. Also record a safe `image_id`, file path, source, report link and split. Have reviewers label same-item pairs and hard different-item pairs. Keep every photo of an `instance_id` in one training, validation or test partition. Check consent, private ownership clues and image licences before public sharing.

The first planned CLIP question is: **Can frozen pretrained embeddings rank another photo of the same physical object above photos of similar, different objects?** Encode images, compare cosine similarities, then measure retrieval on held-out physical items. Do not fine-tune CLIP or claim a result before the data and experiment exist. If useful, add measured image similarity to the Logistic Regression features and compare text-plus-metadata against text-plus-metadata-plus-image on the same reviewed pairs.
