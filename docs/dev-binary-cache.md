# Development binary cache

Longcycle development-stage binary research assets are stored in one GitHub Release rather than in Git history or Google Drive.

- Release tag: `longcycle-dev-binary-cache`
- Role: development-only immutable binary cache for raw source acquisition packs, replay capsules, and hermetic sandbox runtimes.
- Git remains the control plane: task specs, source identity, SHA-256, Evidence/Reality/Judgment receipts, and replay metadata stay in the repository.
- Release assets use unique immutable filenames. A workflow must verify the outer SHA-256 after re-downloading the asset from the Release before the asset is considered durable enough to remove another cache copy.
- Actions runners and ChatGPT sandboxes restore only the asset required by the current task, verify its SHA-256, then extract/use it locally.
- GitHub Release is **not** the terminal production archive. After the product is operational, source/parser blobs and portable replay packs should move to a server/object store selected for production retention.
- Google Drive is not used for heavy research binaries after the Release migration. It may still be used for lightweight manual relay if a future connector constraint requires it, but no large source/replay pack should be placed there by default.
