"""Future optional CLIP feature extraction; no encoder or weights are bundled.

The CAT 2 Logistic Regression experiment does not import this module.
"""


def encode_image(*_args, **_kwargs):
    raise NotImplementedError(
        "Image encoding needs consented same-item photos, an evaluated pretrained encoder, "
        "and separately installed image dependencies. No CLIP result exists yet."
    )
