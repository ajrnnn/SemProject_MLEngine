# Future external image export

Place an authorised Roboflow version 2 YOLO export here, retaining its `data.yaml` and `train/valid/test` structure. Do not add downloaded images to Git. Record the source URL, version, licence, download date and ZIP checksum in `docs/DATASET.md` after acquisition. Run `python scripts/prepare_image_data.py data/raw/roboflow --output data/metadata/image_metadata.csv` only after the export is present. Its object-detection labels do not establish same-item identity.
