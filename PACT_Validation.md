# PACT v1.1.1 validation

Windows x64, 24 September 2026.

All 40 Python tests and five installer path cases passed during the build.

Three new visual regression tests cover long sync-message wrapping at sidebar widths of 320, 420, 520 and 693 pixels; reflow when a visible message's sidebar narrows; and a stationary, single analytics divider across sampled frames in both directions at three widths. These tests also passed with Qt display scaling set to 200%.

The original Work and Learning SVGs use different widths and divider coordinates. PACT now draws one divider at a shared visual position and crops animated content below it. Hover labels retain the existing theme and mouse-transparent behavior, calculate their wrapped height, and stay within the sidebar width.

Rendered and inspected the full sync message and midpoint of the slide. The text is fully visible and the divider remains one line.

An isolated v1.1.0 installation was upgraded to v1.1.1 while running. Hidden launch, second-launch reveal, graceful shutdown, update shutdown, database/target/token-sentinel preservation and uninstall all passed. The installer also ran its installed startup self-test. Tests used synthetic data and did not replace the user's installed application.

Source/package ZIP integrity and SHA-256 checksums verified. App and installer versions are 1.1.1. Installer is unsigned. No Garmin endpoint or authentication behavior changed in this patch.
