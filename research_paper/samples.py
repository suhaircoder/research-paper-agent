"""Short practice papers. They are not real publications."""

SYNC_FACE = """
Audio-Visual Face Animation with a Lightweight Sync Loss

Abstract
We study the problem of generating a talking face from one image and a speech clip. We propose SyncFace, a compact generator that aligns lip motion with audio using a sync loss. The method keeps the identity of the input face while changing the mouth.

1 Introduction
Talking-head generation is useful for video creation. Existing models are large and can drift from the speaker identity.

2 Method
SyncFace encodes the face image and the speech clip with two small networks. A decoder predicts the mouth region, and a sync loss pulls the lip motion toward the audio. The rest of the face is copied from the input so identity stays stable.

3 Experiments
We evaluate on HDTF and VoxCeleb2. The FID is 14.2 and LSE-D is 7.1 on HDTF. Sync accuracy is 91.4%.

4 Conclusion
The model is fast. However, it struggles with large head turns and non-English speech.
""".strip()


MORPH_NET = """
Monocular 3D Face Reconstruction with a Morphable Model

Abstract
We reconstruct a 3D face from a single image. We propose MorphNet, which fits a 3D morphable model and then refines details with an image encoder.

1 Introduction
A 3D face is needed for animation and relighting. Landmark-only methods miss shape outside the landmarks.

2 Method
MorphNet predicts the shape and expression parameters of a 3D morphable model. An encoder then adds a detail displacement. Training uses paired images and scans.

3 Experiments
We evaluate on NoW and Florence. NME is 1.8 on NoW.

4 Conclusion
The mesh is stable. However, the method cannot recover the inside of the mouth and fails on strong profile views.
""".strip()
