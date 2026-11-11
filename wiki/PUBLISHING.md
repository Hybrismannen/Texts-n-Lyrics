# Publishing the native GitHub Wiki

The readable Wiki source is maintained in the **wiki/** directory and generated from the real literary corpus.

GitHub's native Wiki is a **different Git repository** from the primary repository. Standard GitHub Contents API tools cannot update it. This project therefore has an automatic publisher:

- Workflow: [.github/workflows/publish-native-wiki.yml](../.github/workflows/publish-native-wiki.yml)
- Source: [wiki/](../wiki/)
- Target: https://github.com/Hybrismannen/Texts-n-Lyrics/wiki

**One-time setup if the native Wiki is still empty:** open the repository's **Wiki** tab, create a page named **Home** and save it. Then open **Actions → Publish corpus atlas to native GitHub Wiki → Run workflow**. The action uses the repository's own short-lived GitHub Actions token, with contents:write. No personal access token should be pasted in a document or chat.

The publisher checks whether the Wiki exists before attempting an authenticated push. Until initialized, the entire atlas remains browsable under **wiki/** in the main repository. It copies or updates only pages with matching Markdown filenames, preserving unrelated native Wiki pages.

Statistical content comes from [tools/analyze_archive.py](../tools/analyze_archive.py) via [corpus-statistics.yml](../.github/workflows/corpus-statistics.yml).

**State distinction:** A Markdown page in wiki/ is not proof that the native GitHub Wiki is already published. Check the target URL or the publish workflow's actual result before claiming native publication.
